#!/usr/bin/env python3
"""
NFL Officiating Observatory - Complete Data Pipeline
=====================================================
Pulls real data from nflreadpy and generates accurate JSON files.
Includes game details, scores, weather, and team information.

Usage:
    python update_data.py          # Update current season only
    python update_data.py --full   # Full rebuild (2020-present)
    
Requirements:
    pip install nflreadpy pandas numpy pyarrow
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
import re
import sys

try:
    import nflreadpy as nfl
    import pandas as pd
    import numpy as np
except ImportError:
    print("❌ Missing dependencies. Run:")
    print("   pip install nflreadpy pandas numpy pyarrow")
    sys.exit(1)

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / 'frontend' / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)

CURRENT_YEAR = datetime.now().year
HISTORICAL_START = 2020

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
    'OAK': {'name': 'Las Vegas Raiders', 'abbr': 'LV', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/lv.png'},
    'PHI': {'name': 'Philadelphia Eagles', 'abbr': 'PHI', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/phi.png'},
    'PIT': {'name': 'Pittsburgh Steelers', 'abbr': 'PIT', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/pit.png'},
    'SEA': {'name': 'Seattle Seahawks', 'abbr': 'SEA', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/sea.png'},
    'SF': {'name': 'San Francisco 49ers', 'abbr': 'SF', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/sf.png'},
    'TB': {'name': 'Tampa Bay Buccaneers', 'abbr': 'TB', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/tb.png'},
    'TEN': {'name': 'Tennessee Titans', 'abbr': 'TEN', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/ten.png'},
    'WAS': {'name': 'Washington Commanders', 'abbr': 'WAS', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/wsh.png'},
}

# Known name inconsistencies in the data
NAME_FIXES = {
    'Ronald Torbert': 'Ron Torbert',
    'Adrian Hall': 'Adrian Hill',
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

def load_all_data(seasons: list[int]) -> dict:
    """Load all required data from nflreadpy."""
    print(f"\n📥 Loading data for seasons: {seasons}")
    print("=" * 60)
    
    data = {}
    
    # Load schedules FIRST - we need it to map game IDs
    print("   Loading schedules...")
    try:
        schedules = nfl.load_schedules(seasons).to_pandas()
        data['schedules'] = schedules
        print(f"   ✓ {len(schedules)} games")
        
        # Create game ID mapping (old_game_id -> game_id)
        # Officials use old_game_id format, PBP uses game_id format
        id_map = schedules[['game_id', 'old_game_id']].drop_duplicates()
    except Exception as e:
        print(f"   ✗ Schedules error: {e}")
        data['schedules'] = pd.DataFrame()
        id_map = pd.DataFrame()
    
    # Officials assignments
    print("   Loading officials...")
    try:
        officials = nfl.load_officials(seasons).to_pandas()
        
        # Officials use old_game_id format - rename and merge to get new game_id
        officials = officials.rename(columns={'game_id': 'old_game_id', 'official_name': 'name'})
        
        # Merge with id_map to get the PBP-compatible game_id
        if not id_map.empty:
            officials = officials.merge(id_map, on='old_game_id', how='left')
        
        # Apply name fixes
        officials['name'] = officials['name'].replace(NAME_FIXES)
        data['officials'] = officials
        print(f"   ✓ {len(officials)} official assignments")
    except Exception as e:
        print(f"   ✗ Officials error: {e}")
        data['officials'] = pd.DataFrame()
    
    # Play-by-play for penalties — load season by season to handle errors gracefully
    print("   Loading play-by-play (this takes a minute)...")
    cols = [
        'game_id', 'play_id', 'season', 'week', 'qtr',
        'quarter_seconds_remaining', 'penalty', 'penalty_team',
        'penalty_type', 'penalty_yards', 'penalty_player_name',
        'home_team', 'away_team', 'posteam', 'score_differential',
        'down', 'ydstogo', 'play_type'
    ]
    
    all_pbp = []
    for season in seasons:
        try:
            # Load full PBP then select columns (nflreadpy doesn't support column filtering on load)
            season_pbp = nfl.load_pbp(season).to_pandas()
            # Select only the columns we need (that exist in the data)
            available_cols = [c for c in cols if c in season_pbp.columns]
            season_pbp = season_pbp[available_cols]
            all_pbp.append(season_pbp)
            print(f"      {season}: ✓ {len(season_pbp)} plays")
        except Exception as e:
            print(f"      {season}: ✗ Skipped ({type(e).__name__}: {e})")
            continue
    
    if all_pbp:
        pbp = pd.concat(all_pbp, ignore_index=True)
        data['penalties'] = pbp[pbp['penalty'] == 1].copy()
        print(f"   ✓ {len(data['penalties'])} total penalties")
    else:
        print(f"   ✗ No play-by-play data loaded")
        data['penalties'] = pd.DataFrame()
    
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
        'qtr': lambda x: list(x)
    }).reset_index()
    game_penalties.columns = ['game_id', 'total_penalties', 'home_team', 'away_team', 
                               'penalty_teams', 'penalty_types', 'quarters']
    
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
        schedule_cols = ['game_id', 'gameday', 'gametime', 'home_score', 'away_score',
                         'stadium', 'roof', 'surface', 'temp', 'wind', 'weather', 'week']
        available_cols = [c for c in schedule_cols if c in schedules.columns]
        ref_games = ref_games.merge(
            schedules[available_cols], on='game_id', how='left'
        )
    
    # Calculate career stats per referee
    ref_stats = ref_games.groupby('referee').agg({
        'game_id': 'count',
        'total_penalties': ['sum', 'mean', 'min', 'max', 'std'],
        'home_penalties': 'sum',
        'away_penalties': 'sum',
        'season': ['min', 'max']
    }).reset_index()
    
    ref_stats.columns = [
        'name', 'games', 'total_penalties', 'avg_per_game',
        'min_penalties', 'max_penalties', 'std_dev',
        'home_penalties', 'away_penalties', 'first_season', 'last_season'
    ]
    
    # Calculate derived stats
    ref_stats['home_bias_pct'] = (
        (ref_stats['away_penalties'] - ref_stats['home_penalties']) /
        ref_stats['total_penalties'] * 100
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
    
    ref_stats['consistency'] = ref_stats['std_dev'].apply(get_consistency)
    
    # Round numeric columns
    ref_stats['avg_per_game'] = ref_stats['avg_per_game'].round(1)
    ref_stats['std_dev'] = ref_stats['std_dev'].round(2)
    ref_stats['total_penalties'] = ref_stats['total_penalties'].astype(int)
    ref_stats['min_penalties'] = ref_stats['min_penalties'].astype(int)
    ref_stats['max_penalties'] = ref_stats['max_penalties'].astype(int)
    
    # Sort by games
    ref_stats = ref_stats.sort_values('games', ascending=False)
    
    print(f"   ✓ Calculated stats for {len(ref_stats)} crew chiefs")
    
    return ref_stats, ref_games


def calculate_league_trends(data: dict) -> dict:
    """Calculate league-wide trends for charts."""
    print("\n📈 Calculating league trends...")
    
    penalties = data['penalties']
    if penalties.empty:
        return {}
    
    trends = {}
    
    # By season
    by_season = penalties.groupby('season').agg({
        'play_id': 'count',
        'game_id': 'nunique'
    }).reset_index()
    by_season.columns = ['season', 'penalties', 'games']
    by_season['avg_per_game'] = (by_season['penalties'] / by_season['games']).round(1)
    trends['bySeason'] = by_season.to_dict('records')
    
    # By quarter
    by_qtr = penalties[penalties['qtr'].between(1, 4)].groupby('qtr').size().reset_index()
    by_qtr.columns = ['quarter', 'count']
    trends['byQuarter'] = by_qtr.to_dict('records')
    
    # By penalty type (top 10)
    by_type = penalties.groupby('penalty_type').size().reset_index()
    by_type.columns = ['type', 'count']
    by_type = by_type.sort_values('count', ascending=False).head(10)
    trends['byType'] = by_type.to_dict('records')
    
    # Penalty types BY quarter (for the enhanced chart)
    penalty_qtr = penalties[penalties['qtr'].between(1, 4)].copy()
    top_types = penalty_qtr['penalty_type'].value_counts().head(6).index.tolist()
    penalty_qtr_filtered = penalty_qtr[penalty_qtr['penalty_type'].isin(top_types)]
    
    qtr_type_pivot = penalty_qtr_filtered.groupby(['qtr', 'penalty_type']).size().unstack(fill_value=0)
    qtr_type_pct = qtr_type_pivot.div(qtr_type_pivot.sum(axis=1), axis=0) * 100
    
    trends['byQuarterAndType'] = {
        'quarters': [1, 2, 3, 4],
        'types': top_types,
        'data': {col: qtr_type_pct[col].round(1).tolist() for col in qtr_type_pct.columns}
    }
    
    # Home vs away
    penalties['is_home_penalty'] = penalties['penalty_team'] == penalties['home_team']
    home_count = int(penalties['is_home_penalty'].sum())
    away_count = int(len(penalties) - home_count)
    trends['homeVsAway'] = {
        'home': home_count,
        'away': away_count,
        'bias_pct': round((away_count - home_count) / len(penalties) * 100, 1)
    }
    
    print(f"   ✓ Generated trend data")
    return trends


def generate_hero_stats(data: dict, ref_stats: pd.DataFrame) -> dict:
    """Generate stats for the hero section."""
    penalties = data['penalties']
    
    stats = {
        'totalPenalties': int(len(penalties)) if not penalties.empty else 0,
        'totalGames': int(penalties['game_id'].nunique()) if not penalties.empty else 0,
        'totalReferees': int(len(ref_stats)) if not ref_stats.empty else 0,
        'seasonsRange': f"{HISTORICAL_START}-{CURRENT_YEAR}",
        'lastUpdated': datetime.utcnow().isoformat() + 'Z'
    }
    
    if not ref_stats.empty:
        variance = ref_stats['avg_per_game'].std() / ref_stats['avg_per_game'].mean() * 100
        stats['refereeVariance'] = f"{variance:.0f}%"
    
    return stats


def generate_insights(data: dict, ref_stats: pd.DataFrame, trends: dict) -> list:
    """Generate insight cards with explanations."""
    insights = []
    
  # 1. Season trend (since 2022)
    seasons = trends.get('bySeason', [])
    if len(seasons) >= 2:
        latest = seasons[-1]
        # Use 2022 as baseline to show multi-year trend
        baseline = next((s for s in seasons if s['season'] == 2022), seasons[0])
        change = ((latest['avg_per_game'] - baseline['avg_per_game']) / baseline['avg_per_game'] * 100)
        insights.append({
            'id': 'season_trend',
            'icon': '📈',
            'title': 'Penalty Surge Since 2022',
            'value': f"{'+' if change > 0 else ''}{change:.0f}%",
            'description': f"Penalties per game {'jumped' if change > 0 else 'dropped'} from {baseline['avg_per_game']} to {latest['avg_per_game']}",
        })
        
    # 2. Home field bias
    home_away = trends.get('homeVsAway', {})
    bias = home_away.get('bias_pct', 0)
    insights.append({
        'id': 'home_bias',
        'icon': '🏠',
        'title': 'Home Field Bias',
        'value': f"{'+' if bias > 0 else ''}{bias}%",
        'description': f"Away teams are penalized {abs(bias):.1f}% more than home teams",
        'explanation': "Home Field Bias measures how much more (or less) the away team gets penalized compared to the home team. Positive = away team penalized more. This likely reflects crowd influence on officials, not intentional favoritism.",
        'isPositive': abs(bias) < 3
    })
    
    # 3. Referee variance
    if not ref_stats.empty:
        max_avg = ref_stats['avg_per_game'].max()
        min_avg = ref_stats['avg_per_game'].min()
        spread = max_avg - min_avg
        variance_pct = (ref_stats['avg_per_game'].std() / ref_stats['avg_per_game'].mean() * 100)
        
        insights.append({
            'id': 'ref_variance',
            'icon': '🎯',
            'title': 'Referee Variance',
            'value': f"{variance_pct:.0f}%",
            'description': f"Crew chiefs range from {min_avg:.1f} to {max_avg:.1f} penalties/game",
            'explanation': "Referee Variance shows how much penalty rates differ between crews. Higher variance means the referee assignment significantly impacts expected penalty count. The spread tells you the difference between the most lenient and strictest crews.",
            'isPositive': variance_pct < 15
        })
    
    # 4. Let them play effect (Q4 reduction)
    quarters = trends.get('byQuarter', [])
    if len(quarters) >= 4:
        q1_count = quarters[0]['count']
        q4_count = quarters[3]['count']
        q4_change = ((q4_count - q1_count) / q1_count * 100)
        
        insights.append({
            'id': 'let_them_play',
            'icon': '🏈',
            'title': '"Let Them Play" Effect',
            'value': f"{q4_change:+.0f}%",
            'description': f"Q4 has {abs(q4_change):.0f}% {'more' if q4_change > 0 else 'fewer'} penalties than Q1",
            'explanation': "The 'Let Them Play' effect measures whether refs call fewer penalties in crucial moments. A negative Q4 value suggests refs are reluctant to 'decide' games with late flags. Compare Q4 to Q1 to see if refs ease up as games progress.",
            'isPositive': q4_change < 0
        })
    
    # 5. Most common penalty
    types = trends.get('byType', [])
    if types:
        top = types[0]
        total_penalties = sum(t['count'] for t in types)
        insights.append({
            'id': 'top_penalty',
            'icon': '🚩',
            'title': 'Most Common Call',
            'value': top['type'].replace('Offensive ', '').replace('Defensive ', ''),
            'description': f"{top['count']:,} total calls ({top['count'] / total_penalties * 100:.0f}% of all penalties)",
            'explanation': f"{top['type']} is the most frequently called penalty. Understanding which penalties dominate helps identify where teams lose yards and drives.",
            'isPositive': None
        })
    
    # 6. Crew chief spread
    if not ref_stats.empty:
        most_flags = ref_stats.loc[ref_stats['avg_per_game'].idxmax()]
        fewest_flags = ref_stats.loc[ref_stats['avg_per_game'].idxmin()]
        insights.append({
            'id': 'crew_spread',
            'icon': '👨‍⚖️',
            'title': 'Crew Chief Spread',
            'value': f"{fewest_flags['avg_per_game']:.1f} - {most_flags['avg_per_game']:.1f}",
            'description': f"{fewest_flags['name'].split()[-1]} ({fewest_flags['avg_per_game']:.1f}/g) vs {most_flags['name'].split()[-1]} ({most_flags['avg_per_game']:.1f}/g)",
            'explanation': "This shows the range between the most lenient and strictest crews. When you see who's calling your game, check where they fall in this range.",
            'isPositive': None
        })
    
    return insights


# =============================================================================
# OUTPUT GENERATION
# =============================================================================

def save_json(data, filename: str):
    """Save data to JSON file."""
    filepath = DATA_DIR / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    print(f"   💾 {filename}")


def generate_referee_profiles(ref_stats: pd.DataFrame, ref_games: pd.DataFrame, 
                               penalties_df: pd.DataFrame, officials_df: pd.DataFrame):
    """Generate individual JSON files for each referee with penalty type breakdowns."""
    print("\n📝 Generating referee profiles...")
    
    referee_dir = DATA_DIR / 'referee'
    referee_dir.mkdir(parents=True, exist_ok=True)
    
    # Get crew chief assignments to link penalties to referees
    crew_chiefs = officials_df[officials_df['position'] == 'Referee'][['game_id', 'name']].copy()
    crew_chiefs = crew_chiefs.rename(columns={'name': 'referee'})
    
    # Merge penalties with crew chief assignments
    penalties_with_ref = penalties_df.merge(crew_chiefs, on='game_id', how='inner')
    
    for _, ref in ref_stats.iterrows():
        name = ref['name']
        slug = ref['slug']
        
        # Get this referee's games
        games = ref_games[ref_games['referee'] == name].copy()
        
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
        
        # === PENALTY TYPE BREAKDOWN ===
        ref_penalties = penalties_with_ref[penalties_with_ref['referee'] == name]
        
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
                'homePenalties': int(g['home_penalties']),
                'awayPenalties': int(g['away_penalties']),
                'stadium': str(g.get('stadium')) if pd.notna(g.get('stadium')) else None,
                'weather': str(g.get('weather')) if pd.notna(g.get('weather')) else None,
                'temp': int(g['temp']) if 'temp' in g and pd.notna(g.get('temp')) else None,
            }
            recent_games.append(game)
        
        # Calculate tendencies
        league_avg = ref_stats['avg_per_game'].mean()
        ref_avg = ref['avg_per_game']
        diff = ref_avg - league_avg
        diff_pct = (diff / league_avg * 100)
        
        if diff_pct > 10:
            tendency_desc = f"Flag-heavy crew — expect more penalties than average. {name}'s games average {diff:.1f} more penalties per game than league average."
        elif diff_pct > 5:
            tendency_desc = f"Above-average penalty rate. Slightly more flags than typical."
        elif diff_pct < -10:
            tendency_desc = f"Let-them-play style — fewer flags than average. {name}'s games average {abs(diff):.1f} fewer penalties per game."
        elif diff_pct < -5:
            tendency_desc = f"Below-average penalty rate. Tends to let minor infractions go."
        else:
            tendency_desc = "League-average officiating style. Penalty rates are typical."
        
        # Build profile
        profile = {
            'name': name,
            'slug': slug,
            'firstSeason': int(ref['first_season']),
            'lastSeason': int(ref['last_season']),
            'experience': f"{int(ref['last_season'] - ref['first_season'] + 1)} seasons",
            'stats': {
                'games': int(ref['games']),
                'totalPenalties': int(ref['total_penalties']),
                'avgPerGame': float(ref['avg_per_game']),
                'minGame': int(ref['min_penalties']),
                'maxGame': int(ref['max_penalties']),
                'stdDev': float(ref['std_dev']) if pd.notna(ref['std_dev']) else 0,
                'homeBiasPct': float(ref['home_bias_pct']),
                'consistency': ref['consistency']
            },
            'seasonStats': season_stats[['season', 'games', 'penalties', 'avg', 'homeBias']].to_dict('records'),
            'penaltyTypes': penalty_types,
            'quarterDistribution': quarter_dist,
            'recentGames': recent_games,
            'tendencies': {
                'avgVsLeague': round(diff, 1),
                'avgVsLeaguePct': round(diff_pct, 1),
                'description': tendency_desc
            },
            'explanations': {
                'avgPerGame': 'Average number of accepted penalties per game this referee has worked.',
                'homeBiasPct': 'How much more the away team is penalized vs home team. Positive = away penalized more.',
                'consistency': 'Based on standard deviation of penalties per game. Lower variance = more predictable.',
                'penaltyTypes': 'Breakdown of the most common penalty types called in games this referee works.',
                'quarterDistribution': 'When penalties occur during games — shows if ref is more active early or late.'
            },
            'generatedAt': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Save
        with open(referee_dir / f"{slug}.json", 'w') as f:
            json.dump(profile, f, indent=2)
    
    print(f"   ✓ Generated {len(ref_stats)} profiles")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Update NFL Observatory data')
    parser.add_argument('--full', action='store_true', help='Full historical rebuild')
    args = parser.parse_args()
    
    # Determine seasons
    if args.full:
        seasons = list(range(HISTORICAL_START, CURRENT_YEAR + 1))
    else:
        seasons = [CURRENT_YEAR - 1, CURRENT_YEAR]
    
    print("\n" + "=" * 60)
    print("🏈 NFL OFFICIATING OBSERVATORY - DATA UPDATE")
    print("=" * 60)
    print(f"   Mode: {'Full Rebuild' if args.full else 'Incremental'}")
    print(f"   Seasons: {seasons}")
    
    # Load data
    data = load_all_data(seasons)
    
    if data['penalties'].empty:
        print("\n❌ No penalty data available. Exiting.")
        sys.exit(1)
    
    # Calculate
    ref_stats, ref_games = calculate_referee_stats(data)
    trends = calculate_league_trends(data)
    hero_stats = generate_hero_stats(data, ref_stats)
    insights = generate_insights(data, ref_stats, trends)
    
    # Save JSON files
    print("\n💾 Saving JSON files...")
    save_json(hero_stats, 'stats.json')
    save_json(trends, 'trends.json')
    save_json(insights, 'insights.json')
    
    # Referees summary
    ref_summary = ref_stats[[
        'name', 'slug', 'games', 'total_penalties', 'avg_per_game',
        'min_penalties', 'max_penalties', 'std_dev', 'home_bias_pct',
        'consistency', 'first_season', 'last_season'
    ]].to_dict('records')
    save_json(ref_summary, 'referees.json')
    
    # Individual profiles (with penalty type breakdown)
    generate_referee_profiles(ref_stats, ref_games, data['penalties'], data['officials'])
    
    print("\n" + "=" * 60)
    print("✅ DATA UPDATE COMPLETE")
    print("=" * 60)
    print(f"   Penalties: {hero_stats['totalPenalties']:,}")
    print(f"   Games: {hero_stats['totalGames']:,}")
    print(f"   Referees: {hero_stats['totalReferees']}")
    print(f"   Output: {DATA_DIR}")


if __name__ == '__main__':
    main()
