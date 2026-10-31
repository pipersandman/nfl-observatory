#!/usr/bin/env python3
"""
NFL Officiating Observatory - Complete Data Pipeline
=====================================================
Pulls real data from nflreadpy and generates accurate JSON files.
Includes game details, scores, weather, and team information.

Usage:
    python update_data.py          # Update current season only
    python update_data.py --full   # Full rebuild (2015-present)
    
Requirements:
    pip install nflreadpy pandas numpy pyarrow
"""

import json
import argparse
import os
from pathlib import Path
from datetime import datetime, timezone
import re
import sys

try:
    import nflreadpy as nfl
    import pandas as pd
    import numpy as np  # noqa: F401  (dependency check)
except ImportError:
    print("❌ Missing dependencies. Run:")
    print("   pip install nflreadpy pandas numpy pyarrow")
    sys.exit(1)

import raw_capture  # noqa: E402  (raw pulls to R2; never stops the update)
from jsonsafe import atomic_write, forced_failure  # noqa: E402  (atomic writes; NFLOBS_FAIL test hook)
from teams import normalize_teams  # noqa: E402  (schedule teams -> today's abbreviations, #105)
import weeks  # noqa: E402  (shared windows and labels, #116)
from weeks import HISTORICAL_START  # noqa: E402,F401  (first season in the data)

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / 'frontend' / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)

CURRENT_YEAR = datetime.now().year          # calendar year: schedules go this far
CURRENT_SEASON = nfl.get_current_season()   # nflverse's season (turns over the Thursday after Labor Day)


def season_plan(full: bool, current_season: int | None = None, calendar_year: int | None = None):
    """Seasons to load: (required, schedule_seasons).

    Play-by-play and officials go up to nflverse's current season (it refuses later
    ones) and every one of them must load. Schedules go up to the calendar year, so
    next season's games appear as soon as nflverse publishes them (Week 1 previews
    before opening night); a season past the current one may be empty.
    """
    cs = CURRENT_SEASON if current_season is None else current_season
    cy = CURRENT_YEAR if calendar_year is None else calendar_year
    first = HISTORICAL_START if full else cs - 1
    return list(range(first, cs + 1)), list(range(first, max(cs, cy) + 1))


class DataLoadError(Exception):
    """A required source failed to load: stop before writing anything."""


def short_error(e: Exception) -> str:
    """Exception type and first line, without local paths (run_status.json is public)."""
    msg = str(e).splitlines()[0] if str(e) else ''
    msg = msg.replace(str(PROJECT_DIR) + os.sep, '').replace(str(PROJECT_DIR), '')
    return f"{type(e).__name__}: {msg}"[:200] if msg else type(e).__name__

# NFL team data for logos and display names
NFL_TEAMS = {
    'ARI': {'name': 'Arizona Cardinals', 'abbr': 'ARI', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/ari.png'},
    'ATL': {'name': 'Atlanta Falcons', 'abbr': 'ATL', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/atl.png'},
    'BAL': {'name': 'Baltimore Ravens', 'abbr': 'BAL', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/bal.png'},
    'BUF': {'name': 'Buffalo Bills', 'abbr': 'BUF', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/buf.png'},
    'CAR': {'name': 'Carolina Panthers', 'abbr': 'CAR', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/car.png'},
    'CHI': {'name': 'Chicago Bears', 'abbr': 'CHI', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/chi.png'},
    'CIN': {'name': 'Cincinnati Bengals', 'abbr': 'CIN', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/cin.png'},
    'CLE': {'name': 'Cleveland Browns', 'abbr': 'CLE', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/cle.png'},
    'DAL': {'name': 'Dallas Cowboys', 'abbr': 'DAL', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/dal.png'},
    'DEN': {'name': 'Denver Broncos', 'abbr': 'DEN', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/den.png'},
    'DET': {'name': 'Detroit Lions', 'abbr': 'DET', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/det.png'},
    'GB': {'name': 'Green Bay Packers', 'abbr': 'GB', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/gb.png'},
    'HOU': {'name': 'Houston Texans', 'abbr': 'HOU', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/hou.png'},
    'IND': {'name': 'Indianapolis Colts', 'abbr': 'IND', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/ind.png'},
    'JAX': {'name': 'Jacksonville Jaguars', 'abbr': 'JAX', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/jax.png'},
    'KC': {'name': 'Kansas City Chiefs', 'abbr': 'KC', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/kc.png'},
    'LA': {'name': 'Los Angeles Rams', 'abbr': 'LA', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/lar.png'},
    'LAC': {'name': 'Los Angeles Chargers', 'abbr': 'LAC', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/lac.png'},
    'LAR': {'name': 'Los Angeles Rams', 'abbr': 'LAR', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/lar.png'},
    'LV': {'name': 'Las Vegas Raiders', 'abbr': 'LV', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/lv.png'},
    'MIA': {'name': 'Miami Dolphins', 'abbr': 'MIA', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/mia.png'},
    'MIN': {'name': 'Minnesota Vikings', 'abbr': 'MIN', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/min.png'},
    'NE': {'name': 'New England Patriots', 'abbr': 'NE', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/ne.png'},
    'NO': {'name': 'New Orleans Saints', 'abbr': 'NO', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/no.png'},
    'NYG': {'name': 'New York Giants', 'abbr': 'NYG', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/nyg.png'},
    'NYJ': {'name': 'New York Jets', 'abbr': 'NYJ', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/nyj.png'},
    'PHI': {'name': 'Philadelphia Eagles', 'abbr': 'PHI', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/phi.png'},
    'PIT': {'name': 'Pittsburgh Steelers', 'abbr': 'PIT', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/pit.png'},
    'SEA': {'name': 'Seattle Seahawks', 'abbr': 'SEA', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/sea.png'},
    'SF': {'name': 'San Francisco 49ers', 'abbr': 'SF', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/sf.png'},
    'TB': {'name': 'Tampa Bay Buccaneers', 'abbr': 'TB', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/tb.png'},
    'TEN': {'name': 'Tennessee Titans', 'abbr': 'TEN', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/ten.png'},
    'WAS': {'name': 'Washington Commanders', 'abbr': 'WAS', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/wsh.png'},
}

# Known name inconsistencies in the data
SNAP_TYPES = {'run', 'pass', 'punt', 'field_goal', 'kickoff', 'extra_point', 'qb_kneel', 'qb_spike'}

NAME_FIXES = {
    'Ronald Torbert': 'Ron Torbert',
    'Adrian Hall': 'Adrian Hill',
    'Bradley Rogers': 'Brad Rogers',   # nflverse lists his 2019 games under his full first name
}


def slugify(name: str) -> str:
    """Convert name to URL-friendly slug."""
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    return slug.strip('-')


def get_team_info(abbr: str) -> dict:
    """Get team info with fallback for unknown teams."""
    return NFL_TEAMS.get(abbr, {
        'name': abbr,
        'abbr': abbr,
        'logo': f'https://a.espncdn.com/i/teamlogos/nfl/500/{abbr.lower()}.png'
    })


# =============================================================================
# DATA LOADING
# =============================================================================

def load_all_data(seasons: list[int], schedule_seasons: list[int] | None = None) -> dict:
    """Load all required data from nflreadpy.

    Raises DataLoadError if the schedules, the officials or any season of play-by-play
    fail to load: the run must stop before writing anything. Soft problems are returned
    in data['warnings'] and data['wp_status'] for run_status.json.
    """
    schedule_seasons = schedule_seasons or seasons
    print(f"\n📥 Loading data for seasons: {seasons}")
    print("=" * 60)

    data = {'warnings': [], 'wp_status': None}

    # Load schedules FIRST - we need it to map game IDs
    print("   Loading schedules...")
    try:
        forced_failure('load_schedules')
        sched_pl = nfl.load_schedules(schedule_seasons)
        raw_capture.get().capture_frame('nflverse-schedules', f'games_{min(schedule_seasons)}-{max(schedule_seasons)}', sched_pl)
        # Raw capture keeps the schedule as received; from here on its teams use today's
        # abbreviations, like play-by-play (STL/SD/OAK -> LA/LAC/LV, #105)
        schedules = normalize_teams(sched_pl.to_pandas())
    except Exception as e:
        raise DataLoadError(f"schedules: {short_error(e)}") from e
    # nflreadpy returns no rows (no error) for a season it hasn't published
    have = set(schedules['season'].unique()) if 'season' in schedules.columns else set()
    missing = [s for s in seasons if s not in have]
    if missing:
        raise DataLoadError(f"schedules: no games for {', '.join(map(str, missing))}")
    for s in schedule_seasons:
        if s not in have:
            print(f"   … {s} schedule not published yet")
            data['warnings'].append({'source': 'schedules', 'message': f'{s} schedule not published yet'})
    data['schedules'] = schedules
    print(f"   ✓ {len(schedules)} games")

    # Create game ID mapping (old_game_id -> game_id)
    # Officials use old_game_id format, PBP uses game_id format
    id_map = schedules[['game_id', 'old_game_id']].drop_duplicates()

    # Officials assignments
    print("   Loading officials...")
    try:
        forced_failure('load_officials')
        off_pl = nfl.load_officials(seasons)
        raw_capture.get().capture_frame('nflverse-officials', f'officials_{min(seasons)}-{max(seasons)}', off_pl)
        officials = off_pl.to_pandas()
        
        # Officials use old_game_id format - rename and merge to get new game_id
        officials = officials.rename(columns={'game_id': 'old_game_id', 'official_name': 'name'})
        
        # Merge with id_map to get the PBP-compatible game_id
        if not id_map.empty:
            officials = officials.merge(id_map, on='old_game_id', how='left')
        
        # Apply name fixes
        officials['name'] = officials['name'].replace(NAME_FIXES)

        # The officials feed lags during the season (in 2026 it only had Week 1),
        # but the schedule's `referee` column is filled in weekly. Use the schedule
        # as a fallback for any game that has no crew chief in the officials feed.
        sched = data['schedules']
        if not sched.empty and 'referee' in sched.columns:
            covered = set(officials.loc[officials['position'] == 'Referee', 'game_id'].dropna())
            fill = sched[sched['referee'].notna() & ~sched['game_id'].isin(covered)]
            if not fill.empty:
                fill = pd.DataFrame({
                    'game_id': fill['game_id'],
                    'name': fill['referee'].replace(NAME_FIXES),
                    'position': 'Referee',
                    'season': fill['season'],
                    'week': fill['week'],
                })
                officials = pd.concat([officials, fill], ignore_index=True)
                print(f"   ✓ Filled {len(fill)} crew chief assignments from schedule data")

            # Second fallback: crew assignments published before kickoff (Football Zebras,
            # saved weekly in frontend/data/assignments) for games already played that
            # neither feed covers yet, so this week's games count right away
            covered = set(officials.loc[officials['position'] == 'Referee', 'game_id'].dropna())
            played_ids = set(sched.loc[sched['result'].notna(), 'game_id'])
            rows = []
            for f in sorted((DATA_DIR / 'assignments').glob('*.json')):
                try:
                    for g in json.loads(f.read_text()).get('games', []):
                        if g.get('referee') and g['game_id'] in played_ids and g['game_id'] not in covered:
                            rows.append({'game_id': g['game_id'], 'name': NAME_FIXES.get(g['referee'], g['referee']),
                                         'position': 'Referee', 'season': int(g['game_id'][:4]),
                                         'week': int(g['game_id'].split('_')[1])})
                            covered.add(g['game_id'])
                except Exception as e:
                    # One unreadable week file shouldn't stop the run, but it's recorded
                    rel = f.relative_to(DATA_DIR).as_posix()
                    print(f"   ⚠️  Skipped unreadable assignment file {rel}: {short_error(e)}")
                    data['warnings'].append({'source': 'assignments', 'file': rel, 'error': short_error(e)})
                    continue
            if rows:
                officials = pd.concat([officials, pd.DataFrame(rows)], ignore_index=True)
                print(f"   ✓ Filled {len(rows)} crew chief assignments from published assignments")

        data['officials'] = officials
        print(f"   ✓ {len(officials)} official assignments")
    except Exception as e:
        raise DataLoadError(f"officials: {short_error(e)}") from e

    # Play-by-play for penalties — load season by season to handle errors gracefully
    print("   Loading play-by-play (this takes a minute)...")
    cols = [
        'game_id', 'play_id', 'season', 'week', 'qtr',
        'quarter_seconds_remaining', 'penalty', 'penalty_team',
        'penalty_type', 'penalty_yards', 'penalty_player_name',
        'home_team', 'away_team', 'posteam', 'score_differential',
        'down', 'ydstogo', 'play_type', 'season_type', 'first_down_penalty',
        # flag impact: value of each flag and what it did to the drive
        'defteam', 'epa', 'ep', 'wp', 'wpa', 'fixed_drive', 'fixed_drive_result', 'yardline_100',
        'two_point_attempt', 'time', 'desc', 'game_seconds_remaining'
    ]
    
    all_pbp = []
    plays_per_game = []
    for season in seasons:
        try:
            forced_failure('load_pbp')
            # Load full PBP then select columns (nflreadpy doesn't support column filtering on load)
            pbp_pl = nfl.load_pbp(season)
            raw_capture.get().capture_frame('nflverse-pbp', f'play_by_play_{season}', pbp_pl)
            season_pbp = pbp_pl.to_pandas()
            del pbp_pl
            if season_pbp.empty:
                raise ValueError('no plays')
            # Select only the columns we need (that exist in the data)
            available_cols = [c for c in cols if c in season_pbp.columns]
            # Play counts per game (for "% of plays with a flag"): real snaps plus
            # pre-snap penalty plays that never became a snap
            snaps = season_pbp['play_type'].isin(SNAP_TYPES) | (
                (season_pbp['play_type'] == 'no_play') & (season_pbp['penalty'] == 1))
            plays_per_game.append(season_pbp[snaps].groupby('game_id').size().rename('plays'))
            season_pbp = season_pbp[available_cols]
            all_pbp.append(season_pbp)
            print(f"      {season}: ✓ {len(season_pbp)} plays")
        except Exception as e:
            raise DataLoadError(f"play-by-play {season}: {short_error(e)}") from e

    if all_pbp:
        pbp = pd.concat(all_pbp, ignore_index=True)
        data['penalties'] = pbp[pbp['penalty'] == 1].copy()
        # Touchdowns wiped out by offsetting penalties: nflverse marks no penalty on these plays
        _d = pbp['desc'].fillna('')
        data['offsetting_tds'] = pbp[_d.str.contains('TOUCHDOWN NULLIFIED', case=False) & _d.str.contains('offsetting', case=False)][
            [c for c in ['game_id', 'season', 'week', 'season_type', 'posteam', 'defteam', 'play_type', 'desc'] if c in pbp.columns]].copy()
        # Win-probability context tables (what a point is worth by score and clock; a kicking
        # team's chances after a score) for valuing flags in win chances
        # Soft failure: recorded in run_status.json (the old wp_tables.json stays)
        try:
            forced_failure('wp_tables')
            from flag_impact import build_wp_tables
            data['wp_tables'] = build_wp_tables(pbp)
            # published for the live Gameday feed (Worker), which values flags the same way during games
            atomic_write(DATA_DIR / 'wp_tables.json', json.dumps({**data['wp_tables'],
                'pointsPerYard': 0.0615, 'seasons': f"{min(seasons)}-{max(seasons)}",
                'note': 'kick: "lead|clockBucket" -> [kicking team win chance, n]; lev: "clockBucket|marginBucket" -> [win chance per expected point, n]'}))
            data['wp_status'] = {'status': 'ok', 'outputs': ['wp_tables.json']}
        except Exception as e:
            print(f"   ⚠️  Win-probability tables failed: {type(e).__name__}: {e}")
            data['wp_status'] = {'status': 'failed', 'error': short_error(e), 'outputs': ['wp_tables.json']}
        # Every game with play-by-play (including any with zero accepted penalties)
        game_cols = [c for c in ['game_id', 'season', 'week', 'season_type'] if c in pbp.columns]
        data['games_played'] = pbp[game_cols].drop_duplicates('game_id')
        data['plays'] = pd.concat(plays_per_game).reset_index()
        print(f"   ✓ {len(data['penalties'])} total penalties")
    else:
        print("   ✗ No play-by-play data loaded")
        data['penalties'] = pd.DataFrame()
        data['games_played'] = pd.DataFrame()
        data['plays'] = pd.DataFrame(columns=['game_id', 'plays'])
    
    return data


# =============================================================================
# CALCULATIONS
# =============================================================================

def calculate_referee_stats(data: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calculate comprehensive stats for each crew chief."""
    print("\n📊 Calculating referee statistics...")
    
    officials = data['officials']
    penalties = data['penalties']
    schedules = data['schedules']
    
    if officials.empty or penalties.empty:
        print("   ✗ Missing required data")
        return pd.DataFrame(), pd.DataFrame()
    
    # Filter to crew chiefs only (position 'Referee')
    crew_chiefs = officials[officials['position'] == 'Referee'].copy()
    crew_chiefs = crew_chiefs.rename(columns={'name': 'referee'})
    
    # Get game-level penalty counts
    game_penalties = penalties.groupby('game_id').agg({
        'play_id': 'count',
        'home_team': 'first',
        'away_team': 'first',
        'penalty_team': lambda x: list(x),
        'penalty_type': lambda x: list(x),
        'qtr': lambda x: list(x),
        'penalty_yards': lambda x: pd.to_numeric(x, errors='coerce').fillna(0).abs().sum()
    }).reset_index()
    game_penalties.columns = ['game_id', 'total_penalties', 'home_team', 'away_team', 
                               'penalty_teams', 'penalty_types', 'quarters', 'penalty_yards']
    
    # Calculate home/away breakdown
    def count_home(row):
        return sum(1 for t in row['penalty_teams'] if t == row['home_team'])
    
    game_penalties['home_penalties'] = game_penalties.apply(count_home, axis=1)
    game_penalties['away_penalties'] = game_penalties['total_penalties'] - game_penalties['home_penalties']
    
    # Merge with crew chiefs
    ref_games = crew_chiefs[['game_id', 'referee', 'season']].merge(
        game_penalties, on='game_id', how='inner'
    )
    
    # Merge with schedule for game details
    if not schedules.empty:
        schedule_cols = ['game_id', 'game_type', 'gameday', 'gametime', 'home_score', 'away_score',
                         'stadium', 'roof', 'surface', 'temp', 'wind', 'weather', 'week']
        available_cols = [c for c in schedule_cols if c in schedules.columns]
        ref_games = ref_games.merge(
            schedules[available_cols], on='game_id', how='left'
        )
    
    # Career (#117; C1, C11): regular-season games in the seasons before the current one.
    # Seasons worked (first_season, last_season) count every game, the current season and
    # playoffs included; playoff games are counted separately, not in any rate.
    current = int(ref_games['season'].max())
    if 'game_type' in ref_games.columns:
        reg = weeks.regular_season(ref_games, 'game_type')
        playoffs = ref_games[ref_games['game_type'] != 'REG'].groupby('referee').size()
    else:
        reg, playoffs = ref_games, pd.Series(dtype=int)
    career_games = reg[reg['season'].isin(weeks.prior_seasons(ref_games['season'].unique(), current))]

    worked = ref_games.groupby('referee')['season'].agg(['min', 'max'])
    worked.columns = ['first_season', 'last_season']
    ref_stats = career_games.groupby('referee').agg({
        'game_id': 'count',
        'total_penalties': ['sum', 'mean', 'min', 'max', 'std'],
        'home_penalties': 'sum',
        'away_penalties': 'sum',
        'season': ['min', 'max']
    })
    ref_stats.columns = [
        'games', 'total_penalties', 'avg_per_game',
        'min_penalties', 'max_penalties', 'std_dev',
        'home_penalties', 'away_penalties', 'career_first_season', 'career_last_season'
    ]
    # Every crew chief who worked a game keeps a row; one with no career games yet (a
    # first-year crew chief) has games 0 and no career rates
    ref_stats = worked.join(ref_stats, how='left').rename_axis('name').reset_index()
    ref_stats['games'] = ref_stats['games'].fillna(0).astype(int)
    ref_stats['total_penalties'] = ref_stats['total_penalties'].fillna(0)
    ref_stats['playoff_games'] = ref_stats['name'].map(playoffs).fillna(0).astype(int)

    # Calculate derived stats
    ref_stats['home_bias_pct'] = (
        (ref_stats['away_penalties'] - ref_stats['home_penalties']) /
        ref_stats['total_penalties'].where(ref_stats['total_penalties'] > 0) * 100
    ).round(1)
    
    ref_stats['slug'] = ref_stats['name'].apply(slugify)
    
    def get_consistency(std):
        if pd.isna(std) or std < 2:
            return 'Very Consistent'
        elif std < 3:
            return 'Consistent'
        elif std < 4:
            return 'Variable'
        else:
            return 'Highly Variable'
    
    ref_stats['consistency'] = [get_consistency(s) if g else None
                                for s, g in zip(ref_stats['std_dev'], ref_stats['games'])]

    # Round numeric columns; whole numbers stay ints (None when there are no career games)
    ref_stats['avg_per_game'] = ref_stats['avg_per_game'].round(1)
    ref_stats['std_dev'] = ref_stats['std_dev'].round(2)
    ref_stats['total_penalties'] = ref_stats['total_penalties'].astype(int)
    for col in ('min_penalties', 'max_penalties', 'career_first_season', 'career_last_season'):
        ref_stats[col] = pd.Series([int(v) if pd.notna(v) else None for v in ref_stats[col]],
                                   index=ref_stats.index, dtype=object)
    
    # Sort by career games (ties by name, so the order is the same every run)
    ref_stats = ref_stats.sort_values(['games', 'name'], ascending=[False, True])
    
    print(f"   ✓ Calculated stats for {len(ref_stats)} crew chiefs")
    
    return ref_stats, ref_games


def calculate_league_trends(data: dict) -> dict:
    """League-wide trends, regular season only (#117, C1). trends.json holds bySeason,
    byType and homeVsAway; byQuarter is kept in memory for the "Let Them Play" card only."""
    print("\n📈 Calculating league trends...")
    
    penalties = data['penalties']
    if penalties.empty:
        return {}
    penalties = weeks.regular_season(penalties)
    
    trends = {}
    
    # By season
    by_season = penalties.groupby('season').agg({
        'play_id': 'count',
        'game_id': 'nunique'
    }).reset_index()
    by_season.columns = ['season', 'penalties', 'games']
    by_season['avg_per_game'] = (by_season['penalties'] / by_season['games']).round(1)
    trends['bySeason'] = by_season.to_dict('records')
    
    # By quarter (in memory only: written to the file it was unused, P2)
    by_qtr = penalties[penalties['qtr'].between(1, 4)].groupby('qtr').size().reset_index()
    by_qtr.columns = ['quarter', 'count']
    trends['byQuarter'] = by_qtr.to_dict('records')
    
    # By penalty type (top 10)
    by_type = penalties.groupby('penalty_type').size().reset_index()
    by_type.columns = ['type', 'count']
    by_type = by_type.sort_values('count', ascending=False).head(10)
    trends['byType'] = by_type.to_dict('records')
    
    # Home vs away
    home_count = int((penalties['penalty_team'] == penalties['home_team']).sum())
    away_count = int(len(penalties) - home_count)
    trends['homeVsAway'] = {
        'home': home_count,
        'away': away_count,
        # Road teams' share minus home teams' share, in percentage points
        'bias_pct': round((away_count - home_count) / len(penalties) * 100, 1),
        # How many more penalties road teams get than home teams, in percent
        'awayMorePct': round((away_count / home_count - 1) * 100, 1) if home_count else None,
    }
    
    print("   ✓ Generated trend data")
    return trends


def generate_hero_stats(data: dict, ref_stats: pd.DataFrame) -> dict:
    """Generate stats for the hero section."""
    penalties = data['penalties']
    
    stats = {
        'totalPenalties': int(len(penalties)) if not penalties.empty else 0,
        'totalGames': int(penalties['game_id'].nunique()) if not penalties.empty else 0,
        'totalReferees': int(len(ref_stats)) if not ref_stats.empty else 0,
        'seasonsRange': f"{HISTORICAL_START}-{CURRENT_SEASON}",
        'lastUpdated': datetime.utcnow().isoformat() + 'Z'
    }
    
    if not ref_stats.empty:
        variance = ref_stats['avg_per_game'].std() / ref_stats['avg_per_game'].mean() * 100
        stats['refereeVariance'] = f"{variance:.0f}%"
    
    return stats


def _season_block(games: int, penalties: float, yards: float):
    """Summary numbers for one crew chief (or the league) in one season."""
    if games == 0:
        return None
    return {
        'games': int(games),
        'penalties': int(penalties),
        'yards': int(round(yards)),
        'perGame': round(float(penalties) / games, 2),
        'yardsPerGame': round(float(yards) / games, 1),
        'yardsPerPenalty': round(float(yards) / penalties, 1) if penalties else 0.0,
    }


def calculate_season_comparison(data: dict) -> dict:
    """Current season vs several baselines, league-wide and per crew chief, with yardage.

    Baselines (the frontend toggles between them):
      sameWeeks  - previous season, through the same week as the current season
      lastSeason - all of the previous season
      last3      - the three seasons before the current one (games-weighted average)
      all        - every prior season in the data (games-weighted average)

    Regular season only: playoff games are worked by all-star crews and would
    skew crew-vs-crew comparisons.
    """
    print("\n📊 Calculating current season vs baselines...")

    penalties = data['penalties'].copy()
    games = data.get('games_played', pd.DataFrame()).copy()
    officials = data['officials']

    if penalties.empty or games.empty or officials.empty:
        print("   ✗ Missing required data")
        return {}

    if 'season_type' in games.columns:
        games = weeks.regular_season(games)
        penalties = weeks.regular_season(penalties)

    current = int(games['season'].max())
    previous = current - 1
    prior_seasons = weeks.prior_seasons(games['season'].unique(), current)
    penalties = penalties[penalties['game_id'].isin(games['game_id'])].copy()
    penalties['penalty_yards'] = pd.to_numeric(penalties['penalty_yards'], errors='coerce').fillna(0).abs()

    # "Through Week N" = the last week whose games have ALL been played. A Thursday game
    # alone doesn't make it "through Week 5"; those early games are counted as extras.
    through_week, partial = weeks.completed_week(data['schedules'], games, current)
    # The league's same-weeks comparison runs through the partial week while one is in
    # progress (#118), like each crew chief's: both sides then include that week.
    same_week = weeks.compare_week(through_week, games.loc[games['season'] == current, 'week'])

    per_game = penalties.groupby('game_id').agg(
        penalties=('game_id', 'size'),
        yards=('penalty_yards', 'sum'),
    ).reset_index()

    g = games[['game_id', 'season', 'week']].merge(per_game, on='game_id', how='left')
    g[['penalties', 'yards']] = g[['penalties', 'yards']].fillna(0)

    chiefs = (officials[officials['position'] == 'Referee'][['game_id', 'name']]
              .dropna(subset=['game_id'])
              .drop_duplicates('game_id'))
    g = g.merge(chiefs, on='game_id', how='left')

    def summarize(frame):
        return _season_block(len(frame), frame['penalties'].sum(), frame['yards'].sum())

    span = weeks.span_label

    # Baseline definitions: key -> (row filter, labels). Only include ones the loaded data supports.
    baselines = []
    if previous in prior_seasons:
        baselines.append({
            'key': 'sameWeeks', 'seasons': [previous],
            'label': weeks.through_label(previous, same_week),
            'short': weeks.short_through(previous, same_week),
            'mask': lambda f: (f['season'] == previous) & (f['week'] <= same_week),
        })
        baselines.append({
            'key': 'lastSeason', 'seasons': [previous],
            'label': f"All of {previous}", 'short': f"{previous}",
            'mask': lambda f: f['season'] == previous,
        })
    last3 = weeks.last_n(prior_seasons, 3)
    if len(last3) == 3:
        baselines.append({
            'key': 'last3', 'seasons': last3,
            'label': f"Last 3 seasons ({span(last3)})", 'short': f"{span(last3)} avg",
            'mask': lambda f, s=last3: f['season'].isin(s),
        })
    if len(prior_seasons) > 3:
        baselines.append({
            'key': 'all', 'seasons': prior_seasons,
            'label': f"All seasons ({span(prior_seasons)})", 'short': f"{span(prior_seasons)} avg",
            'mask': lambda f, s=prior_seasons: f['season'].isin(s),
        })

    league = {
        'current': summarize(g[g['season'] == current]),
        'baselines': {b['key']: summarize(g[b['mask'](g)]) for b in baselines},
    }

    crews = []
    inactive = []  # crew chiefs with history but no games this season (cards still need their numbers)
    for name, s in g.dropna(subset=['name']).groupby('name'):
        cur = summarize(s[s['season'] == current])
        if cur is None:  # hasn't worked a game this season
            inactive.append({
                'name': name,
                'slug': slugify(name),
                'current': None,
                'baselines': {b['key']: summarize(s[b['mask'](s)]) for b in baselines},
            })
            continue
        crew_week = max(through_week, int(s.loc[s['season'] == current, 'week'].max()))
        bl = {b['key']: summarize(s[b['mask'](s)]) for b in baselines}
        if 'sameWeeks' in bl and crew_week != same_week:   # own week differs from the league's (e.g. no game yet in a partial week)
            bl['sameWeeks'] = summarize(s[(s['season'] == previous) & (s['week'] <= crew_week)])
        crews.append({
            'name': name,
            'slug': slugify(name),
            'current': cur,
            'throughWeek': crew_week,
            'baselines': bl,
        })

    # Most penalties per game first
    crews.sort(key=lambda c: (c['current']['perGame'], c['current']['yardsPerGame']), reverse=True)

    print(f"   ✓ {current} through week {through_week}: {len(crews)} crew chiefs, "
          f"baselines: {', '.join(b['key'] for b in baselines)}")

    return {
        'currentSeason': current,
        'previousSeason': previous,
        'throughWeek': through_week,
        'partialWeek': partial,   # games already played in the next (unfinished) week
        'windows': weeks.windows_block(games['season'].unique(), current, through_week, partial, same_week),
        'regularSeasonOnly': True,
        'baselines': [{**{k: b[k] for k in ('key', 'label', 'short', 'seasons')},
                       'button': weeks.baseline_button(b['key'], b['seasons'], same_week)} for b in baselines],
        'defaultBaseline': 'sameWeeks' if previous in prior_seasons else (baselines[0]['key'] if baselines else None),
        'league': league,
        'crewChiefs': crews,
        'inactiveCrewChiefs': inactive,
        'generatedAt': datetime.utcnow().isoformat() + 'Z',
    }


# =============================================================================
# OUTPUT GENERATION
# =============================================================================

def save_json(data, filename: str, quiet: bool = False):
    """Save data to a JSON file atomically: convert first, write a temp file, then
    rename it into place. If anything fails, the old file is left untouched."""
    from jsonsafe import dumps as safe_dumps   # NaN-proof: one NaN breaks the whole file in browsers
    text = safe_dumps(data)
    forced_failure(f'save_json:{filename}')
    atomic_write(DATA_DIR / filename, text)

    if not quiet:
        print(f"   💾 {filename}")


def generate_referee_profiles(ref_stats: pd.DataFrame, ref_games: pd.DataFrame, 
                               penalties_df: pd.DataFrame, officials_df: pd.DataFrame,
                               league_career_rate: float | None = None):
    """Generate individual JSON files for each referee with penalty type breakdowns.

    Regular season only (#117, C1). Career figures (stats, penaltyTypes,
    quarterDistribution, tendencies) use the seasons before the current one; seasonStats
    and recentGames include the current season; playoff games are counted, not used.
    league_career_rate: the league's own regular-season rate over the career window
    (season_comparison.json baselines.all), the benchmark for tendencies (C10).

    Returns {slug: the profile's penaltyTypes[0].type or None}, for referees.json's
    top_penalty_type (the card footer, #148), so both files come from the same code."""
    print("\n📝 Generating referee profiles...")
    
    referee_dir = DATA_DIR / 'referee'
    referee_dir.mkdir(parents=True, exist_ok=True)
    
    # Get crew chief assignments to link penalties to referees
    crew_chiefs = officials_df[officials_df['position'] == 'Referee'][['game_id', 'name']].copy()
    crew_chiefs = crew_chiefs.rename(columns={'name': 'referee'})
    
    # Merge penalties with crew chief assignments
    penalties_with_ref = penalties_df.merge(crew_chiefs, on='game_id', how='inner')

    # Regular-season-only views for this-season vs prior-years comparisons
    current_season = int(ref_games['season'].max())
    reg_games_all = ref_games[ref_games['game_type'] == 'REG'] if 'game_type' in ref_games.columns else ref_games
    reg_pen_all = (penalties_with_ref[penalties_with_ref['season_type'] == 'REG']
                   if 'season_type' in penalties_with_ref.columns else penalties_with_ref)
    career_window = weeks.prior_seasons(ref_games['season'].unique(), current_season)
    career_games_all = reg_games_all[reg_games_all['season'].isin(career_window)]
    if league_career_rate is None and len(career_games_all):
        league_career_rate = career_games_all['total_penalties'].sum() / len(career_games_all)
    
    top_types = {}
    for _, ref in ref_stats.iterrows():
        name = ref['name']
        slug = ref['slug']

        # Get this referee's regular-season games (playoff games: counted in playoffGames only)
        games = reg_games_all[reg_games_all['referee'] == name].copy()
        
        # Sort by date (most recent first)
        if 'gameday' in games.columns:
            games = games.sort_values('gameday', ascending=False)
        else:
            games = games.sort_values(['season', 'game_id'], ascending=[False, False])
        
        # Season-by-season stats
        season_stats = games.groupby('season').agg({
            'game_id': 'count',
            'total_penalties': ['sum', 'mean'],
            'home_penalties': 'sum',
            'away_penalties': 'sum'
        }).reset_index()
        season_stats.columns = ['season', 'games', 'penalties', 'avg', 'home', 'away']
        season_stats['avg'] = season_stats['avg'].round(1)
        season_stats['homeBias'] = ((season_stats['away'] - season_stats['home']) / 
                                     season_stats['penalties'] * 100).round(1)
        season_stats = season_stats.sort_values('season', ascending=True)
        
        # === PENALTY TYPE BREAKDOWN (career window) ===
        ref_penalties = reg_pen_all[(reg_pen_all['referee'] == name) & reg_pen_all['season'].isin(career_window)]
        
        penalty_types = []
        if not ref_penalties.empty and 'penalty_type' in ref_penalties.columns:
            type_counts = ref_penalties['penalty_type'].value_counts().head(10)
            total_penalties = len(ref_penalties)
            
            for ptype, count in type_counts.items():
                if pd.notna(ptype):
                    penalty_types.append({
                        'type': str(ptype),
                        'count': int(count),
                        'pct': round(count / total_penalties * 100, 1)
                    })
        
        # === QUARTER DISTRIBUTION ===
        quarter_dist = []
        if not ref_penalties.empty and 'qtr' in ref_penalties.columns:
            qtr_counts = ref_penalties[ref_penalties['qtr'].between(1, 4)]['qtr'].value_counts().sort_index()
            total_qtr = qtr_counts.sum()
            
            for qtr in [1, 2, 3, 4]:
                count = qtr_counts.get(qtr, 0)
                quarter_dist.append({
                    'quarter': int(qtr),
                    'count': int(count),
                    'pct': round(count / total_qtr * 100, 1) if total_qtr > 0 else 0
                })
        
        # === THIS SEASON vs PRIOR YEARS (regular season, per game) ===
        reg_games = reg_games_all[reg_games_all['referee'] == name]
        reg_pen = reg_pen_all[reg_pen_all['referee'] == name]
        cur_g = int((reg_games['season'] == current_season).sum())
        prior_g = int((reg_games['season'] < current_season).sum())

        regular_season_stats = []
        for season, sg in reg_games.groupby('season'):
            n = len(sg)
            pens = int(sg['total_penalties'].sum())
            yds = float(sg['penalty_yards'].sum()) if 'penalty_yards' in sg.columns else 0.0
            regular_season_stats.append({
                'season': int(season), 'games': n, 'penalties': pens, 'yards': int(round(yds)),
                'perGame': round(pens / n, 2), 'yardsPerGame': round(yds / n, 1),
            })

        def per_game(count, games):
            return round(count / games, 2) if games else None

        cur_pen = reg_pen[reg_pen['season'] == current_season]
        prior_pen = reg_pen[reg_pen['season'] < current_season]
        cur_types = cur_pen['penalty_type'].value_counts()
        prior_types = prior_pen['penalty_type'].value_counts()
        # Top types this season plus top types historically, so new spikes and usual staples both show
        type_keys = list(dict.fromkeys(list(cur_types.head(8).index) + list(prior_types.head(6).index)))
        type_comparison = []
        for t in type_keys:
            if pd.isna(t):
                continue
            type_comparison.append({
                'type': str(t),
                'currentCount': int(cur_types.get(t, 0)),
                'currentPerGame': per_game(int(cur_types.get(t, 0)), cur_g),
                'priorCount': int(prior_types.get(t, 0)),
                'priorPerGame': per_game(int(prior_types.get(t, 0)), prior_g),
            })
        type_comparison.sort(key=lambda x: (x['currentPerGame'] or 0, x['priorPerGame'] or 0), reverse=True)

        quarter_comparison = []
        for q in [1, 2, 3, 4]:
            cq = int((cur_pen['qtr'] == q).sum())
            pq = int((prior_pen['qtr'] == q).sum())
            quarter_comparison.append({
                'quarter': q,
                'currentPerGame': per_game(cq, cur_g),
                'priorPerGame': per_game(pq, prior_g),
            })

        # Recent games with full details
        recent_games = []
        for _, g in games.head(20).iterrows():
            game = {
                'gameId': g['game_id'],
                'season': int(g['season']),
                'week': int(g.get('week', 0)) if pd.notna(g.get('week')) else None,
                'date': str(g['gameday']) if 'gameday' in g and pd.notna(g['gameday']) else None,
                'homeTeam': {
                    'abbr': g['home_team'],
                    **get_team_info(g['home_team'])
                },
                'awayTeam': {
                    'abbr': g['away_team'],
                    **get_team_info(g['away_team'])
                },
                'homeScore': int(g['home_score']) if 'home_score' in g and pd.notna(g.get('home_score')) else None,
                'awayScore': int(g['away_score']) if 'away_score' in g and pd.notna(g.get('away_score')) else None,
                'penalties': int(g['total_penalties']),
                'yards': int(round(g['penalty_yards'])) if 'penalty_yards' in g and pd.notna(g.get('penalty_yards')) else None,
                'gameType': str(g.get('game_type')) if pd.notna(g.get('game_type')) else None,
                'homePenalties': int(g['home_penalties']),
                'awayPenalties': int(g['away_penalties']),
                'stadium': str(g.get('stadium')) if pd.notna(g.get('stadium')) else None,
                'weather': str(g.get('weather')) if pd.notna(g.get('weather')) else None,
                'temp': int(g['temp']) if 'temp' in g and pd.notna(g.get('temp')) else None,
            }
            recent_games.append(game)
        
        # Tendencies: the crew's career rate vs the league's own rate over the same
        # window (C10), not the mean of crew chiefs' averages
        league_avg = league_career_rate
        ref_avg = ref['avg_per_game']
        has_career = bool(ref['games']) and league_avg and pd.notna(ref_avg)
        diff = ref_avg - league_avg if has_career else None
        diff_pct = (diff / league_avg * 100) if has_career else None
        
        if not has_career:
            tendency_desc = "No regular-season games before this season yet."
        elif diff_pct > 10:
            tendency_desc = f"Flag-heavy crew — expect more penalties than average. {name}'s games average {diff:.1f} more penalties per game than league average."
        elif diff_pct > 5:
            tendency_desc = "Above-average penalty rate. Slightly more flags than typical."
        elif diff_pct < -10:
            tendency_desc = f"Let-them-play style — fewer flags than average. {name}'s games average {abs(diff):.1f} fewer penalties per game."
        elif diff_pct < -5:
            tendency_desc = "Below-average penalty rate. Tends to let minor infractions go."
        else:
            tendency_desc = "League-average officiating style. Penalty rates are typical."
        
        # Build profile
        profile = {
            'name': name,
            'slug': slug,
            'firstSeason': int(ref['first_season']),
            'lastSeason': int(ref['last_season']),
            'experience': f"{int(ref['last_season'] - ref['first_season'] + 1)} seasons",
            # Career window for the rates below (#117): regular season, seasons before this one
            'careerSeasons': ([ref['career_first_season'], ref['career_last_season']]
                              if ref['career_first_season'] is not None else None),
            'playoffGames': int(ref['playoff_games']),   # worked, not in any rate (C1)
            'stats': {
                'games': int(ref['games']),
                'totalPenalties': int(ref['total_penalties']),
                'avgPerGame': float(ref['avg_per_game']) if pd.notna(ref['avg_per_game']) else None,
                'minGame': ref['min_penalties'],
                'maxGame': ref['max_penalties'],
                'stdDev': float(ref['std_dev']) if pd.notna(ref['std_dev']) else 0,
                'homeBiasPct': float(ref['home_bias_pct']) if pd.notna(ref['home_bias_pct']) else None,
                'consistency': ref['consistency']
            },
            'seasonStats': season_stats[['season', 'games', 'penalties', 'avg', 'homeBias']].to_dict('records'),
            'penaltyTypes': penalty_types,
            'quarterDistribution': quarter_dist,
            'recentGames': recent_games,
            'currentSeason': current_season,
            'currentSeasonGames': cur_g,
            'priorSeasonGames': prior_g,
            'regularSeasonStats': regular_season_stats,
            'penaltyTypeComparison': type_comparison,
            'quarterComparison': quarter_comparison,
            'tendencies': {
                'avgVsLeague': round(diff, 1) if has_career else None,
                'avgVsLeaguePct': round(diff_pct, 1) if has_career else None,
                'description': tendency_desc
            },
            'explanations': {
                'avgPerGame': 'Average number of accepted penalties per game in the regular-season games this referee worked before this season.',
                'homeBiasPct': "Road teams' share of this crew's penalties minus home teams' share, in percentage points. Positive = road teams penalized more.",
                'consistency': 'Based on standard deviation of penalties per game. Lower variance = more predictable.',
                'penaltyTypes': 'Breakdown of the most common penalty types called in games this referee works.',
                'quarterDistribution': 'When penalties occur during games — shows if ref is more active early or late.'
            },
            'generatedAt': datetime.utcnow().isoformat() + 'Z'
        }
        
        save_json(profile, f"referee/{slug}.json", quiet=True)
        top_types[slug] = penalty_types[0]['type'] if penalty_types else None

    print(f"   ✓ Generated {len(ref_stats)} profiles")
    return top_types


# =============================================================================
# MAIN
# =============================================================================

class RunStatus:
    """Runs each pipeline module, keeps going past failures, and records the result."""

    def __init__(self):
        self.modules = {}

    def run(self, name, outputs, fn, depends_on=None):
        dep = self.modules.get(depends_on) if depends_on else None
        if dep and dep['status'] != 'ok':
            print(f"   ⏭️  {name} skipped ({depends_on} {dep['status']})")
            self.modules[name] = {'status': 'skipped', 'reason': f'{depends_on} {dep["status"]}', 'outputs': outputs}
            return None
        try:
            forced_failure(name)
            result = fn()
        except Exception as e:
            import traceback
            print(f"   ⚠️  {name} failed: {type(e).__name__}: {e}")
            traceback.print_exc()
            self.modules[name] = {'status': 'failed', 'error': short_error(e), 'outputs': outputs}
            return None
        self.modules[name] = {'status': 'ok', 'outputs': outputs}
        return result


RAW_CAPTURE_STALE_HOURS = 24   # raw capture failing longer than this turns the run red


def raw_capture_status(raw: dict, prev: dict, run_at: str) -> dict:
    """rawCapture for run_status.json. lastSuccess carries forward; failingSince is set
    on the first failure and cleared by a success. 'stale' = failing for more than
    RAW_CAPTURE_STALE_HOURS, counted from lastSuccess (or failingSince if it never worked)."""
    out = dict(raw)
    prev = prev or {}
    if raw['status'] == 'ok':
        out['lastSuccess'] = run_at
    elif raw['status'] == 'failed':
        out['lastSuccess'] = prev.get('lastSuccess')
        out['failingSince'] = prev.get('failingSince') or run_at
        since = out['lastSuccess'] or out['failingSince']
        hours = (datetime.fromisoformat(run_at.replace('Z', '+00:00'))
                 - datetime.fromisoformat(since.replace('Z', '+00:00'))).total_seconds() / 3600
        out['failingHours'] = round(hours, 1)
        out['stale'] = hours > RAW_CAPTURE_STALE_HOURS
    else:   # off (local run): keep what the last real run recorded
        for k in ('lastSuccess', 'failingSince'):
            if prev.get(k):
                out[k] = prev[k]
    return out


def write_run_status(modules: dict, warnings: list, run_at: str, raw: dict | None = None) -> bool:
    """frontend/data/run_status.json: what failed this run and when each output was
    last refreshed. lastSuccess carries forward from the previous file. Returns ok:
    every module ok, and raw capture not failing for more than 24 hours."""
    try:
        prev_file = json.loads((DATA_DIR / 'run_status.json').read_text(encoding='utf-8'))
    except Exception:
        prev_file = {}
    prev = prev_file.get('modules', {})
    out = {}
    for name, m in modules.items():
        last = run_at if m['status'] == 'ok' else (prev.get(name) or {}).get('lastSuccess')
        out[name] = {**m, 'lastSuccess': last}
    ok = all(m['status'] == 'ok' for m in out.values())
    status = {'runAt': run_at, 'ok': ok, 'modules': out, 'warnings': warnings}
    if raw:
        rc = raw_capture_status(raw, prev_file.get('rawCapture'), run_at)
        status['rawCapture'] = rc
        if rc['status'] == 'failed':
            since = rc.get('lastSuccess') or rc.get('failingSince')
            msg = (f"raw capture failing for {rc['failingHours']} h (since {since}): {rc.get('error')}"
                   if rc['stale'] else f"raw capture failed: {rc.get('error')}")
            warnings.append({'source': 'raw_capture', 'message': msg})
            if rc['stale']:
                status['ok'] = ok = False
    save_json(status, 'run_status.json')
    return ok


def report(lines: list[str]):
    """Print the end-of-run summary, and add it to the GitHub Actions run page."""
    for line in lines:
        print(line)
    path = os.environ.get('GITHUB_STEP_SUMMARY')
    if path:
        with open(path, 'a', encoding='utf-8') as f:
            f.write('### Data update\n\n' + '\n'.join(f'- {x.strip()}' for x in lines if x.strip() and set(x.strip()) != {'='}) + '\n')


def main():
    parser = argparse.ArgumentParser(description='Update NFL Observatory data')
    parser.add_argument('--full', action='store_true', help='Full historical rebuild')
    args = parser.parse_args()

    # Determine seasons
    seasons, schedule_seasons = season_plan(args.full)

    print("\n" + "=" * 60)
    print("🏈 NFL OFFICIATING OBSERVATORY - DATA UPDATE")
    print("=" * 60)
    print(f"   Mode: {'Full Rebuild' if args.full else 'Incremental'}")
    print(f"   Seasons: {seasons}")
    if os.environ.get('NFLOBS_FAIL') and os.environ.get('GITHUB_ACTIONS'):
        print("WARNING: NFLOBS_FAIL is set but ignored in GitHub Actions")

    # Raw capture (R2): this step's pulls plus fetch_assignments.py's, one manifest per run
    cap = raw_capture.get()
    cap.load_handoff()

    # Load data. A required source that fails stops the run here, before anything is written.
    try:
        data = load_all_data(seasons, schedule_seasons)
    except DataLoadError as e:
        cap.write_manifest(error=f'data loading: {e}')
        report(['', '=' * 60, f"❌ FAILED (data loading): {e} — nothing written", '=' * 60])
        return 1

    if data['penalties'].empty:
        print("\n❌ No penalty data available. Exiting.")
        sys.exit(1)
    
    # Calculate
    ref_stats, ref_games = calculate_referee_stats(data)
    trends = calculate_league_trends(data)
    hero_stats = generate_hero_stats(data, ref_stats)
    season_comparison = calculate_season_comparison(data)
    
    # Save JSON files
    print("\n💾 Saving JSON files...")
    save_json(hero_stats, 'stats.json')
    save_json({k: v for k, v in trends.items() if k != 'byQuarter'}, 'trends.json')   # byQuarter: in memory only (P2)
    if season_comparison:
        save_json(season_comparison, 'season_comparison.json')
    
    # Individual profiles (with penalty type breakdown)
    career_rate = (((season_comparison or {}).get('league') or {}).get('baselines') or {}).get('all', {}) or {}
    top_types = generate_referee_profiles(ref_stats, ref_games, data['penalties'], data['officials'],
                                          career_rate.get('perGame'))

    # Referees summary. top_penalty_type is the profile's penaltyTypes[0].type, so the
    # home page cards don't have to load every profile (#148).
    ref_summary = ref_stats[[
        'name', 'slug', 'games', 'total_penalties', 'avg_per_game',
        'min_penalties', 'max_penalties', 'std_dev', 'home_bias_pct',
        'consistency', 'first_season', 'last_season',
        'career_first_season', 'career_last_season', 'playoff_games'
    ]].to_dict('records')
    for r in ref_summary:
        r['top_penalty_type'] = top_types.get(r['slug'])
    save_json(ref_summary, 'referees.json')

    # Modules: each one runs even if an earlier one failed; failures are recorded,
    # not hidden. Order and arguments are unchanged.
    status = RunStatus()
    if data['wp_status']:
        status.modules['wp_tables'] = data['wp_status']

    # Scoreboard (league totals by timeframe + weekly running log)
    def scoreboard_():
        from scoreboard import build_scoreboard
        save_json(build_scoreboard(data), 'scoreboard.json')
    status.run('scoreboard', ['scoreboard.json'], scoreboard_)

    # Penalty type trends (which calls are rising or falling)
    def type_trends_():
        from type_trends import build_type_trends
        save_json(build_type_trends(data), 'type_trends.json')
    status.run('type_trends', ['type_trends.json'], type_trends_)

    # Flag impact: what each flag cost, drive killers / extenders, big plays erased
    def flag_impact_():
        from flag_impact import build_flag_impact
        save_json(build_flag_impact(data), 'flag_impact.json')
    status.run('flag_impact', ['flag_impact.json'], flag_impact_)

    # Stat miner: ranked, luck-filtered shortlist of the week's most unusual stats (internal report)
    def stat_miner_():
        from stat_miner import build_stat_miner
        build_stat_miner(data)
    status.run('stat_miner', ['reports/miner/'], stat_miner_)

    # Crew styles: each active crew chief's calling fingerprint
    def crew_styles_():
        from crew_styles import build_crew_styles
        sc_path = DATA_DIR / 'season_comparison.json'
        active = [c['name'] for c in json.loads(sc_path.read_text()).get('crewChiefs', [])] if sc_path.exists() else []
        save_json(build_crew_styles(data, active), 'crew_styles.json')
    status.run('crew_styles', ['crew_styles.json'], crew_styles_)

    # Team pages (all 32 teams, by division)
    def team_pages_():
        from team_pages import build_team_pages
        build_team_pages(data, get_team_info, slugify, DATA_DIR)
    status.run('team_pages', ['teams/'], team_pages_)

    # Game previews for the next week (uses Football Zebras assignments if fetched)
    def previews_():
        from previews import build_previews
        return build_previews(data, slugify, get_team_info, NAME_FIXES, DATA_DIR)
    preview_out = status.run('previews', ['previews/'], previews_)

    # Prediction scorecard: freeze upcoming projections, backtest past weeks, grade
    def scorecard_():
        import scorecard
        from previews import build_previews
        scorecard.run(data, build_previews, (slugify, get_team_info, NAME_FIXES, DATA_DIR),
                      (preview_out or {}).get('weeks', []), DATA_DIR, PROJECT_DIR)
    status.run('scorecard', ['scorecard/'], scorecard_, depends_on='previews')

    # History ledger: permanent week-by-week record of predictions and outcomes
    def history_():
        from history import build_history
        build_history(data, DATA_DIR)
    status.run('history', ['history/'], history_, depends_on='previews')

    # Run status (written last) and summary
    run_at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    cap.write_manifest()
    raw = cap.status()
    ok = write_run_status(status.modules, data['warnings'], run_at, raw)
    failed = [f"{n} ({m['error']})" for n, m in status.modules.items() if m['status'] == 'failed']
    skipped = [f"{n} ({m['reason']})" for n, m in status.modules.items() if m['status'] == 'skipped']
    warns = [w.get('message') or f"{w.get('file')}: {w.get('error')}" for w in data['warnings']]

    lines = ['', '=' * 60, '✅ DATA UPDATE COMPLETE' if ok else '❌ DATA UPDATE FINISHED WITH FAILURES', '=' * 60]
    if failed:
        lines.append(f"   FAILED: {'; '.join(failed)}")
    if skipped:
        lines.append(f"   SKIPPED: {'; '.join(skipped)}")
    if warns:
        lines.append(f"   WARNINGS ({len(warns)}): {'; '.join(warns)}")
    lines.append(f"   Raw capture: {raw['status']}" +
                 (f" ({raw['new']} new, {raw['unchanged']} unchanged)" if raw['status'] != 'off' else ''))
    lines += [f"   Penalties: {hero_stats['totalPenalties']:,}",
              f"   Games: {hero_stats['totalGames']:,}",
              f"   Referees: {hero_stats['totalReferees']}",
              f"   Output: {DATA_DIR}"]
    report(lines)
    # 3 = some modules failed or were skipped, or raw capture has failed for over 24 hours;
    # everything else was written
    return 0 if ok else 3


def run():
    """main(), plus a run manifest even if the run crashes part-way."""
    try:
        return main()
    except BaseException as e:
        cap = raw_capture.get()
        if cap.mode == 'on' and cap.manifest_key is None:
            cap.write_manifest(error=f'crashed: {type(e).__name__}')
        raise


if __name__ == '__main__':
    sys.exit(run())
