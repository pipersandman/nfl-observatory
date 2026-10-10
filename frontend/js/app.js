/**
 * NFL Officiating Observatory - Main Application v2
 * With carousel, explainers, and enhanced referee profiles
 */

// =============================================================================
// CONFIGURATION
// =============================================================================

const CONFIG = {
    dataPath: './data',
    chartColors: {
        flag: '#ffc400',      // accent: "look here"
        data: '#f5f4f0',      // this season's numbers and bars
        neutral: '#9a9ea4',   // average / neither high nor low
        slate: '#7b8794',     // neutral bars in the crew chief chart
        current: '#ffc400',   // this season's bars: flag yellow
        hist: '#5c616a',      // comparison / history bars: solid mid-gray
        histDark: '#3e434a',  // older history (all prior years)
        green: '#3fb98a',     // fewer flags
        red: '#f0605d',       // more flags
        // Muted categorical palette for penalty-type charts (no strong red/green,
        // so it never reads as "more/fewer"); yellow marks the biggest category
        // High-contrast categorical palette for penalty-type charts. Every pair is
        // clearly different (perceptual distance >= 29), and none is a pure red or
        // green, so categories never read as "more/fewer flags". Biggest category first.
        categorical: ['#FFC400', '#4DA3FF', '#FF8F3F', '#E5E7EB', '#2EC4D6',
                      '#F472B6', '#B07CFF', '#D2B48C', '#8B95A7', '#7C3AED']
    }
};

// Explainer content for all metrics
const EXPLAINERS = {
    'data-methodology': {
        title: 'How is this data collected?',
        content: `
            <p>All penalty data comes from official NFL play-by-play records via the <strong>nflverse</strong> project, 
            which compiles data from the NFL's Game Statistics and Information System (GSIS).</p>
            <p>Important: The play-by-play data tells us <em>that</em> a penalty occurred, but not <em>which specific 
            official</em> threw the flag. That's why we track by <strong>Crew Chief</strong> — the head referee who 
            sets the standard for their crew.</p>
            <p>Data is updated weekly during the NFL season, typically on Tuesdays after Monday Night Football.</p>
        `
    },
    'crew-chief': {
        title: 'What is a Crew Chief?',
        content: `
            <p>Each NFL game has <strong>7 officials</strong> on the field:</p>
            <p>• <strong>Referee (R)</strong> — The Crew Chief, wears white cap<br>
            • Umpire (U)<br>
            • Down Judge (DJ)<br>
            • Line Judge (LJ)<br>
            • Back Judge (BJ)<br>
            • Side Judge (SJ)<br>
            • Field Judge (FJ)</p>
            <p>We track <strong>Crew Chiefs</strong> because they're publicly accountable, set the calling standard 
            for their crew, and work with consistent crew members all season. This is the same method used by 
            Vegas oddsmakers.</p>
        `
    },
    'home-bias': {
        title: 'What is Home Bias?',
        content: `
            <p><strong>Home Bias</strong> measures how much more (or less) the away team gets penalized compared to 
            the home team, shown as a percentage.</p>
            <p><strong>Positive number</strong> = Away team penalized more (typical)<br>
            <strong>Negative number</strong> = Home team penalized more (unusual)</p>
            <p>This likely reflects <strong>crowd influence</strong> on officials — not intentional favoritism. 
            Research shows home bias is strongest in Q1 and fades as the game progresses.</p>
        `
    },
    'avg-per-game': {
        title: 'Average Penalties Per Game',
        content: `
            <p>The average number of <strong>accepted penalties</strong> in games worked by this crew chief.</p>
            <p>League average is typically around <strong>11-12 penalties per game</strong>. Crew chiefs with 
            higher averages run "flag-heavy" crews, while lower averages indicate a "let them play" style.</p>
            <p>This metric helps predict how many penalties to expect when a particular crew is assigned.</p>
        `
    },
    'consistency': {
        title: 'What does Consistency mean?',
        content: `
            <p><strong>Consistency</strong> is based on the <strong>standard deviation</strong> of penalties per game.</p>
            <p>• <strong>Very Consistent</strong> — Std dev < 2. You know what to expect.<br>
            • <strong>Consistent</strong> — Std dev 2-3. Fairly predictable.<br>
            • <strong>Variable</strong> — Std dev 3-4. Can swing either way.<br>
            • <strong>Highly Variable</strong> — Std dev > 4. Wildcard crew.</p>
            <p>A consistent crew chief is more predictable for game planning and betting analysis.</p>
        `
    },
    'games': {
        title: 'Games Worked',
        content: `
            <p>Total number of games this crew chief has officiated during the analysis period (2020-2024).</p>
            <p>More games = more reliable statistics. Crew chiefs typically work <strong>16-18 games per season</strong> 
            during the regular season, plus playoffs for top-rated officials.</p>
        `
    },
    'week-of-season': {
        title: 'Penalties Per Game By Week Of Season',
        content: `
            <p>Average accepted penalties per game for each week of the regular season.</p>
            <p><strong>Yellow</strong> is this season. <strong>White</strong> is the average of past seasons for that
            week, and the <strong>shaded band</strong> shows the lowest-to-highest past season, so you can see what's normal.
            Add any past season with the season buttons above the chart (this season is always shown), switch the average or
            range off, or pick "All seasons".</p>
            <p>Historically, flags run highest early and fade late, with the last two weeks lowest of all (resting starters
            and games with nothing at stake play a part). The data can't separate player discipline from officiating or
            game context. A week appears once all of its games are played.</p>
        `
    },
    'season-trend': {
        title: 'Penalties Per Game By Season',
        content: `
            <p>This chart shows how the <strong>league-wide average</strong> of penalties per game has changed 
            over the seasons.</p>
            <p>Increases often reflect rule changes, points of emphasis from the NFL, or officiating directives. 
            The 2024 spike, for example, suggests new enforcement priorities.</p>
        `
    },
    'penalty-types': {
        title: 'Most Common Penalty Types',
        content: `
            <p>Distribution of the <strong>top 10 most frequently called penalties</strong> across all games.</p>
            <p><strong>Offensive Holding</strong> and <strong>False Start</strong> typically dominate — these 
            are the most common mistakes teams make. Understanding penalty mix helps with game strategy.</p>
        `
    },
    'quarter-penalties': {
        title: 'Penalty Types By Quarter',
        content: `
            <p>This chart breaks down <strong>what types of penalties</strong> occur in each quarter, not just totals.</p>
            <p>Patterns often emerge: more false starts early (pre-snap nerves), more holding late (tired players), 
            fewer overall calls in Q4 (refs "letting them play" in crunch time).</p>
        `
    },
    'season-penalties': {
        title: 'Penalties Per Game: This Season vs Last',
        content: `
            <p>Each crew chief's <strong>average accepted penalties per game</strong> this season (colored bar) 
            next to the comparison you pick above (gray bar). Ranked from most flags to fewest.</p>
            <p><strong>Same weeks</strong> compares against last season through the same week we're in now (updates 
            automatically each week). <strong>Last 3 seasons</strong> and <strong>All seasons</strong> are 
            games-weighted averages across those years.</p>
            <p>The <strong>percentage at the end of each bar</strong> is the change vs the comparison: 
            <span style="color:#ef4444">▲ red</span> = more flags, <span style="color:#10b981">▼ green</span> = fewer, 
            gray = within ±2% (basically flat). Faded labels mean the crew has worked fewer than 4 games this season.</p>
            <p>Regular season only — playoff games are worked by all-star crews, which would skew the comparison. 
            Early in the season each crew has only a handful of games, so one wild game can move the average a lot.</p>
        `
    },
    'season-yards': {
        title: 'Penalty Yards Per Game',
        content: `
            <p>Total <strong>yards assessed on accepted penalties</strong> per game, this season vs the comparison 
            you pick above. Each crew chief's yardage is listed next to their name. Ranked from most yards to fewest.</p>
            <p>Two crews can throw the same number of flags but cost teams very different yardage — a crew that calls 
            more pass interference and personal fouls will rank higher here than one that mostly calls false starts.</p>
        `
    },
    'previews': {
        title: 'How game previews work',
        content: `
            <p>Each projection starts from the <strong>league's current penalty rate</strong> for home and away teams, 
            penalty type by penalty type, and adjusts it for:</p>
            <p>• how often each team <strong>commits</strong> that type<br>
            • how often the opponent <strong>draws</strong> it (e.g. a pass rush that forces holding)<br>
            • how often the assigned <strong>crew chief calls</strong> it</p>
            <p>Every adjustment is measured against the league over the last three regular seasons, weighted toward 
            this season, and pulled toward average when the sample is small, so a team's four games or a crew's 
            handful of calls can't swing the projection wildly.</p>
            <p>The <strong>range</strong> covers 80% of likely outcomes, based on how much real game totals vary. 
            Context like primetime, division games, and rest is shown for reference but not added to the number.</p>
            <p>Crew assignments come from <strong>Football Zebras</strong>, usually posted Tuesday morning. 
            Until then, games show "Crew TBA" and use a neutral crew.</p>
        `
    },
    'penalties-by-ref': {
        title: 'Penalties By Crew Chief',
        content: `
            <p>This chart ranks crew chiefs by their <strong>average penalties per game</strong>, from most to fewest.</p>
            <p>Knowing which crews throw more flags can help predict game flow and total points.</p>
        `
    }
};

// =============================================================================
// STATE
// =============================================================================

let state = {
    stats: null,
    previews: null,
    scorecard: null,
    scoreboard: null,
    typeTrends: null,
    typeTrendsCompare: null,
    showAllOpponents: false,
    scoreboardFrame: null,
    teamsIndex: null,
    selectedDivision: null,
    teamProfiles: {},
    season: null,
    seasonBaseline: null,
    referees: [],
    trends: null,
    insights: [],
    currentReferee: null,
    charts: {},
    carouselIndex: 0,
    refereeProfiles: {}  // Cache loaded profiles
};

// =============================================================================
// DATA FETCHING
// =============================================================================

async function fetchJSON(filename) {
    try {
        // no-cache = always check the server for a newer copy (data changes weekly)
        const response = await fetch(`${CONFIG.dataPath}/${filename}`, { cache: "no-cache" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`Error fetching ${filename}:`, error);
        return null;
    }
}

async function loadAllData() {
    console.log('📥 Loading data...');
    
    const [season, referees, trends, insights] = await Promise.all([
        fetchJSON('season_comparison.json'),
        fetchJSON('referees.json'),
        fetchJSON('trends.json'),
        fetchJSON('insights.json')
    ]);
    
    state.season = season;

    // Next week's previews (latest.json points at the current week's file)
    state.teamsIndex = await fetchJSON('teams/index.json');
    state.scorecard = await fetchJSON('scorecard/public.json');
    state.scoreboard = await fetchJSON('scoreboard.json');
    state.typeTrends = await fetchJSON('type_trends.json');

    // Previews: remaining games this week (e.g. Monday night) + next week
    const latest = await fetchJSON('previews/latest.json');
    const files = latest?.weeks?.map(w => w.file) || (latest?.file ? [latest.file] : []);
    state.previews = (await Promise.all(files.map(f => fetchJSON(f)))).filter(Boolean);
    state.referees = referees || [];
    state.trends = trends;
    state.insights = insights || [];
    
    // Pre-load all referee profiles for card previews
    await preloadRefereeProfiles();
    
    console.log('✓ Data loaded');
    return { season, referees, trends, insights };
}

async function preloadRefereeProfiles() {
    // Load profiles in parallel for card previews
    const promises = state.referees.map(async (ref) => {
        const profile = await fetchJSON(`referee/${ref.slug}.json`);
        if (profile) {
            state.refereeProfiles[ref.slug] = profile;
        }
    });
    await Promise.all(promises);
    console.log(`✓ Loaded ${Object.keys(state.refereeProfiles).length} referee profiles`);
}

async function loadRefereeProfile(slug) {
    // Check cache first
    if (state.refereeProfiles[slug]) {
        return state.refereeProfiles[slug];
    }
    const profile = await fetchJSON(`referee/${slug}.json`);
    if (profile) {
        state.refereeProfiles[slug] = profile;
    }
    return profile;
}

// =============================================================================
// RENDERING - THIS SEASON VS LAST
// =============================================================================

function fmtNum(n, digits = 0) {
    if (n === null || n === undefined) return '—';
    return Number(n).toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

// Percent change vs the selected comparison.
// Red = more flags/yards, green = fewer, gray = within ±PCT_NEUTRAL (noise).
const PCT_NEUTRAL = 2;      // percent
const MIN_GAMES_FOR_PCT = 4; // crews below this get a dimmed badge (small sample)

function pctChange(cur, base) {
    if (cur === null || cur === undefined || !base) return null;
    return (cur - base) / base * 100;
}

function pctDirection(pct) {
    if (pct === null) return 'none';
    if (Math.abs(pct) < PCT_NEUTRAL) return 'flat';
    return pct > 0 ? 'up' : 'down';
}

function pctText(pct) {
    if (pct === null) return 'new';
    const abs = Math.abs(pct);
    const shown = abs < 10 ? abs.toFixed(1) : Math.round(abs).toString();
    const dir = pctDirection(pct);
    const arrow = dir === 'up' ? '▲' : dir === 'down' ? '▼' : '●';
    return `${arrow} ${shown}%`;
}

function pctBadge(cur, base, { small = false, title = '' } = {}) {
    const pct = pctChange(cur, base);
    const dir = pctDirection(pct);
    const tip = title || (pct === null ? 'No comparison data' : `${pct > 0 ? '+' : ''}${pct.toFixed(1)}%`);
    return `<span class="pct-badge pct-${dir}${small ? ' pct-small-sample' : ''}" title="${tip}">${pctText(pct)}</span>`;
}

const PCT_COLORS = {
    up: CONFIG.chartColors.red,
    down: CONFIG.chartColors.green,
    flat: 'rgba(255,255,255,0.45)',
    none: 'rgba(255,255,255,0.45)'
};

// Chart.js plugin: draws the % change at the end of each current-season bar
const pctLabelPlugin = {
    id: 'pctLabels',
    afterDatasetsDraw(chart, args, opts) {
        if (!opts || !opts.rows) return;
        const meta = chart.getDatasetMeta(0);
        if (!meta || meta.hidden) return;
        const { ctx } = chart;
        ctx.save();
        ctx.font = '600 11px "JetBrains Mono", monospace';
        ctx.textBaseline = 'middle';
        ctx.textAlign = 'left';
        meta.data.forEach((bar, i) => {
            const r = opts.rows[i];
            const b = opts.baseOf(r);
            const pct = pctChange(r.current[opts.field], b ? b[opts.field] : null);
            const dir = pctDirection(pct);
            ctx.globalAlpha = r.current.games < MIN_GAMES_FOR_PCT ? 0.5 : 1;
            ctx.fillStyle = PCT_COLORS[dir];
            ctx.fillText(pctText(pct), bar.x + 6, bar.y);
        });
        ctx.restore();
    }
};

function renderSeasonComparison() {
    const d = state.season;
    const body = document.getElementById('seasonBody');
    if (!body) return;

    if (!d || !d.crewChiefs?.length || !d.baselines?.length) {
        document.getElementById('seasonSubtitle').textContent = '';
        body.innerHTML = '<p class="season-error">Current-season data isn\'t available yet. Check back after this week\'s update.</p>';
        return;
    }

    if (!state.seasonBaseline || !d.baselines.some(b => b.key === state.seasonBaseline)) {
        state.seasonBaseline = d.defaultBaseline || d.baselines[0].key;
    }

    document.getElementById('seasonTitle').textContent = `${d.currentSeason} Season`;
    document.getElementById('seasonTableTitle').textContent = `Crew Chiefs in ${d.currentSeason}`;

    // Toggle buttons (built from whatever baselines the pipeline produced)
    document.getElementById('baselineToggle').innerHTML = d.baselines.map(b => `
        <button class="baseline-btn ${b.key === state.seasonBaseline ? 'active' : ''}"
                data-key="${b.key}" aria-pressed="${b.key === state.seasonBaseline}">
            ${b.key === 'sameWeeks' ? `${b.seasons[0]} thru Wk ${d.throughWeek}`
              : b.key === 'lastSeason' ? `All of ${b.seasons[0]}`
              : b.key === 'last3' ? 'Last 3 seasons'
              : 'All seasons'}
        </button>
    `).join('');
    document.querySelectorAll('#baselineToggle .baseline-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            state.seasonBaseline = btn.dataset.key;
            renderSeasonComparison();
        });
    });

    renderSeasonView();
}

function renderSeasonView() {
    const d = state.season;
    const key = state.seasonBaseline;
    const base = d.baselines.find(b => b.key === key);
    const cs = d.currentSeason, L = d.league;
    const LB = L.baselines[key];
    const baseOf = r => r.baselines?.[key] || null;

    document.getElementById('seasonSubtitle').textContent =
        `Regular season through Week ${d.throughWeek}` +
        (d.partialWeek ? ` (plus ${d.partialWeek.games} game${d.partialWeek.games === 1 ? '' : 's'} from Week ${d.partialWeek.week})` : '') +
        `, compared with ${base.label.charAt(0).toLowerCase() + base.label.slice(1)}.`;
    document.getElementById('seasonPrevHeader').textContent = base.short;

    // League strip
    const stat = (label, field, digits) => `
        <div class="season-stat">
            <div class="season-stat-label">${label}</div>
            <div class="season-stat-value">${fmtNum(L.current?.[field], digits)}</div>
            <div class="season-stat-compare">
                ${pctBadge(L.current?.[field], LB?.[field])}
                <span class="season-stat-vs">vs ${base.short}: <strong>${fmtNum(LB?.[field], digits)}</strong></span>
            </div>
        </div>`;

    document.getElementById('seasonLeague').innerHTML = `
        <div class="season-stat">
            <div class="season-stat-label">${cs} so far</div>
            <div class="season-stat-value">${fmtNum(L.current?.penalties)}</div>
            <div class="season-stat-compare">penalties for <strong>${fmtNum(L.current?.yards)}</strong> yards in ${fmtNum(L.current?.games)} games</div>
        </div>
        ${stat('Penalties per game', 'perGame', 1)}
        ${stat('Penalty yards per game', 'yardsPerGame', 1)}
        ${stat('Yards per penalty', 'yardsPerPenalty', 1)}
    `;

    // Charts: always most on down
    const byPenalties = [...d.crewChiefs].sort((a, b) => b.current.perGame - a.current.perGame);
    const byYards = [...d.crewChiefs].sort((a, b) => b.current.yardsPerGame - a.current.yardsPerGame);

    state.charts.seasonPenalties = renderSeasonBarChart({
        canvasId: 'seasonPenaltiesChart', existing: state.charts.seasonPenalties, rows: byPenalties,
        field: 'perGame', unit: 'penalties/game', axisTitle: 'Penalties per game',
        currentLabel: `${cs}`, baseLabel: base.short, baseOf
    });
    state.charts.seasonYards = renderSeasonBarChart({
        canvasId: 'seasonYardsChart', existing: state.charts.seasonYards, rows: byYards,
        field: 'yardsPerGame', unit: 'yds/game', axisTitle: 'Penalty yards per game',
        currentLabel: `${cs}`, baseLabel: base.short, baseOf,
        // Show the yardage on the axis next to each name: "Scott Novak" / "215 yds · vs 147"
        labelFn: r => [r.name, `${fmtNum(r.current.yardsPerGame)} yds` +
                       (baseOf(r) ? ` · vs ${fmtNum(baseOf(r).yardsPerGame)}` : '')],
        rowHeight: 44
    });

    // Table (most penalties per game first)
    document.getElementById('seasonTableBody').innerHTML = byPenalties.map(r => {
        const b = baseOf(r);
        const small = r.current.games < MIN_GAMES_FOR_PCT;
        return `
        <tr onclick="openRefereeModal('${r.slug}')">
            <td><strong>${r.name}</strong></td>
            <td>${r.current.games}</td>
            <td>${fmtNum(r.current.penalties)} for ${fmtNum(r.current.yards)} yds</td>
            <td>${fmtNum(r.current.perGame, 1)} ${pctBadge(r.current.perGame, b?.perGame, { small })}</td>
            <td>${fmtNum(r.current.yardsPerGame, 1)} ${pctBadge(r.current.yardsPerGame, b?.yardsPerGame, { small })}</td>
            <td class="season-prev">${b
                ? `${fmtNum(b.penalties)} for ${fmtNum(b.yards)} yds <span>(${fmtNum(b.perGame, 1)}/g, ${b.games} g)</span>`
                : '—'}</td>
        </tr>`;
    }).join('');
}

function renderSeasonBarChart({ canvasId, existing, rows, field, unit, axisTitle,
                                currentLabel, baseLabel, baseOf, labelFn, rowHeight = 34 }) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    if (existing) existing.destroy();

    // Grow the chart so every crew chief gets a readable row
    canvas.parentElement.style.height = `${Math.max(300, rows.length * rowHeight + 80)}px`;

    return new Chart(canvas.getContext('2d'), {
        type: 'bar',
        plugins: [pctLabelPlugin],
        data: {
            labels: rows.map(r => (labelFn ? labelFn(r) : r.name)),
            datasets: [
                {
                    label: currentLabel,
                    data: rows.map(r => r.current[field]),
                    backgroundColor: CONFIG.chartColors.current,
                    borderRadius: 4,
                    barPercentage: 0.9,
                    categoryPercentage: 0.75
                },
                {
                    label: baseLabel,
                    data: rows.map(r => (baseOf(r) ? baseOf(r)[field] : null)),
                    backgroundColor: CONFIG.chartColors.hist,
                    borderRadius: 4,
                    barPercentage: 0.9,
                    categoryPercentage: 0.75
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            animation: { duration: 400 },
            layout: { padding: { right: 64 } },
            plugins: {
                pctLabels: { rows, field, baseOf },
                legend: {
                    position: 'top',
                    align: 'end',
                    labels: { color: 'rgba(255,255,255,0.7)', boxWidth: 12 }
                },
                tooltip: {
                    callbacks: {
                        title: (items) => rows[items[0].dataIndex].name,
                        footer: (items) => {
                            const r = rows[items[0].dataIndex];
                            const b = baseOf(r);
                            if (!b) return 'No comparison data';
                            const pct = pctChange(r.current[field], b[field]);
                            const d = r.current[field] - b[field];
                            const note = r.current.games < MIN_GAMES_FOR_PCT ? `  (only ${r.current.games} games — small sample)` : '';
                            return `${pctText(pct)} (${d > 0 ? '+' : ''}${fmtNum(d, 1)}) vs ${baseLabel}${note}`;
                        },
                        label: (ctx) => {
                            const r = rows[ctx.dataIndex];
                            const b = ctx.datasetIndex === 0 ? r.current : baseOf(r);
                            if (!b) return `${ctx.dataset.label}: did not work`;
                            return `${ctx.dataset.label}: ${fmtNum(b[field], 1)} ${unit} ` +
                                   `(${fmtNum(b.penalties)} pen, ${fmtNum(b.yards)} yds, ${b.games} g)`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: 'rgba(255,255,255,0.5)' },
                    title: { display: true, text: axisTitle, color: 'rgba(255,255,255,0.5)' }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: 'rgba(255,255,255,0.75)', autoSkip: false }
                }
            },
            onClick: (evt, elements) => {
                if (elements.length) openRefereeModal(rows[elements[0].index].slug);
            }
        }
    });
}

// =============================================================================
// RENDERING - INSIGHTS CAROUSEL
// =============================================================================

function renderInsightsCarousel() {
    const container = document.getElementById('insightsCarousel');
    const dotsContainer = document.getElementById('carouselDots');
    
    if (!container) return;
    
    // Use loaded insights or generate from trends
    let insights = state.insights;
    
    if (!insights.length && state.trends) {
        insights = generateInsightsFromTrends();
    }
    
    if (!insights.length) {
        container.innerHTML = '<p>Loading insights...</p>';
        return;
    }
    
    container.innerHTML = insights.map((insight, i) => `
        <div class="insight-card ${insight.isPositive === true ? 'positive' : insight.isPositive === false ? 'negative' : ''}" data-index="${i}">
            ${['🏈', '⏱️'].includes(insight.icon) ? `<div class="insight-icon">${insight.icon}</div>` : ''}
            <div class="insight-title">${insight.title}</div>
            <div class="insight-value">${insight.value}</div>
            <p class="insight-desc">${insight.description}</p>
            <div class="insight-explainer">
                <strong>What this means:</strong>
                ${insight.explanation}
            </div>
        </div>
    `).join('');
    
    // Render dots
    if (dotsContainer) {
        dotsContainer.innerHTML = insights.map((_, i) => 
            `<div class="carousel-dot ${i === 0 ? 'active' : ''}" onclick="goToSlide(${i})"></div>`
        ).join('');
    }
}

function generateInsightsFromTrends() {
    const insights = [];
    const trends = state.trends;
    
    // Season trend
    const seasons = trends.bySeason || [];
    if (seasons.length >= 2) {
        const latest = seasons[seasons.length - 1];
        const previous = seasons[seasons.length - 2];
        const change = ((latest.avg_per_game - previous.avg_per_game) / previous.avg_per_game * 100).toFixed(0);
        
        insights.push({
            icon: '',
            title: `${latest.season} Penalty Trend`,
            value: `${change > 0 ? '+' : ''}${change}%`,
            description: `Penalties per game ${change > 0 ? 'jumped' : 'dropped'} from ${previous.avg_per_game} to ${latest.avg_per_game}`,
            explanation: 'This measures the average number of accepted penalties per game compared to the previous season.',
            isPositive: change < 0
        });
    }
    
    // Home bias
    const homeAway = trends.homeVsAway || {};
    if (homeAway.bias_pct !== undefined) {
        insights.push({
            icon: '',
            title: 'Home Field Bias',
            value: `${homeAway.bias_pct > 0 ? '+' : ''}${homeAway.bias_pct}%`,
            description: `Away teams are penalized ${Math.abs(homeAway.bias_pct)}% more than home teams`,
            explanation: 'Positive means away teams get more flags. This reflects crowd influence on officials, not intentional bias.',
            isPositive: Math.abs(homeAway.bias_pct) < 3
        });
    }
    
    // Add more insights...
    if (state.referees.length) {
        const maxAvg = Math.max(...state.referees.map(r => r.avg_per_game));
        const minAvg = Math.min(...state.referees.map(r => r.avg_per_game));
        
        insights.push({
            icon: '',
            title: 'Crew Chief Spread',
            value: `${minAvg.toFixed(1)} - ${maxAvg.toFixed(1)}`,
            description: `Penalty rates range from ${minAvg.toFixed(1)} to ${maxAvg.toFixed(1)} per game depending on crew`,
            explanation: 'This shows how much the referee assignment matters. Some crews call 3+ more penalties per game than others.',
            isPositive: null
        });
    }
    
    // Top penalty
    const types = trends.byType || [];
    if (types.length) {
        insights.push({
            icon: '',
            title: 'Most Common Call',
            value: types[0].type.replace('Offensive ', '').replace('Defensive ', ''),
            description: `${types[0].count.toLocaleString()} total calls (${(types[0].count / types.reduce((a, t) => a + t.count, 0) * 100).toFixed(0)}% of all penalties)`,
            explanation: 'Understanding which penalties dominate helps identify where teams lose yards and drives.',
            isPositive: null
        });
    }
    
    return insights;
}

function moveCarousel(direction) {
    const track = document.getElementById('insightsCarousel');
    const cards = track.querySelectorAll('.insight-card');
    
    if (!cards.length) return;
    
    state.carouselIndex += direction;
    
    if (state.carouselIndex < 0) state.carouselIndex = cards.length - 1;
    if (state.carouselIndex >= cards.length) state.carouselIndex = 0;
    
    goToSlide(state.carouselIndex);
}

function goToSlide(index) {
    const track = document.getElementById('insightsCarousel');
    const cards = track.querySelectorAll('.insight-card');
    const dots = document.querySelectorAll('.carousel-dot');
    
    if (!cards.length) return;
    
    state.carouselIndex = index;
    
    // Scroll to card
    cards[index].scrollIntoView({ behavior: 'smooth', inline: 'start', block: 'nearest' });
    
    // Update dots
    dots.forEach((dot, i) => {
        dot.classList.toggle('active', i === index);
    });
}

// =============================================================================
// TEAM COLORS (preview split bars + quarter-by-quarter chart only)
// Exact official team colors, never lightened. Home shows its signature color;
// if the away team's is too similar, the away team switches to one of its own
// alternate colors (like jerseys), else wears white. Pure black is never used as
// a fill. Checked on all 992 matchups: every pair is clearly different.
// =============================================================================
// Official team colors, in each team's own hex values. First = the color used
// by default (the team's signature color); the rest are its real alternates,
// used only when the opponent's color is too similar. No color is lightened or
// altered. Pure-black colors are never used as a fill (invisible on the dark site).
const TEAM_COLORS = {
    ARI: ['#97233F', '#FFB612', '#000000'],            // cardinal red, gold
    ATL: ['#A71930', '#A5ACAF', '#000000'],            // falcons red, silver
    BAL: ['#241773', '#9E7C0C', '#000000'],            // purple, metallic gold
    BUF: ['#00338D', '#C60C30'],                       // royal blue, red
    CAR: ['#0085CA', '#BFC0BF', '#101820'],            // panther blue, silver
    CHI: ['#0B162A', '#C83803'],                       // navy, orange
    CIN: ['#FB4F14', '#000000'],                       // orange
    CLE: ['#FF3C00', '#311D00'],                       // orange, brown
    DAL: ['#003594', '#869397', '#041E42'],            // royal blue, silver, navy
    DEN: ['#FB4F14', '#002244'],                       // orange, navy
    DET: ['#0076B6', '#B0B7BC'],                       // honolulu blue, silver
    GB:  ['#203731', '#FFB612'],                       // dark green, gold
    HOU: ['#03202F', '#A71930'],                       // deep steel blue, battle red
    IND: ['#002C5F', '#A2AAAD'],                       // speed blue, gray
    JAX: ['#006778', '#D7A22A', '#101820'],            // teal, gold
    KC:  ['#E31837', '#FFB81C'],                       // red, gold
    LA:  ['#003594', '#FFD100'],                       // royal blue, sol yellow
    LAC: ['#0080C6', '#FFC20E'],                       // powder blue, sunshine gold
    LV:  ['#A5ACAF', '#000000'],                       // silver (black isn't visible here)
    MIA: ['#008E97', '#FC4C02', '#005778'],            // aqua, orange, blue
    MIN: ['#4F2683', '#FFC62F'],                       // purple, gold
    NE:  ['#002244', '#C60C30', '#B0B7BC'],            // navy, red, silver
    NO:  ['#D3BC8D', '#101820'],                       // old gold
    NYG: ['#0B2265', '#A71930', '#A5ACAF'],            // blue, red, gray
    NYJ: ['#125740', '#FFFFFF'],                       // gotham green, white
    PHI: ['#004C54', '#A5ACAF', '#ACC0C6'],            // midnight green, silver
    PIT: ['#FFB612', '#101820'],                       // gold (black isn't visible here)
    SEA: ['#002244', '#69BE28', '#A5ACAF'],            // college navy, action green, wolf gray
    SF:  ['#AA0000', '#B3995D'],                       // red, gold
    TB:  ['#D50A0A', '#FF7900', '#34302B'],            // red, bay orange, pewter
    TEN: ['#4B92DB', '#0C2340', '#C8102E'],            // titans blue, navy, red
    WAS: ['#5A1414', '#FFB612'],                       // burgundy, gold
};
const MIN_DISTANCE = 45;                               // CIE76 deltaE between the two teams' colors
const AWAY_FALLBACKS = ['#E5E7EB', '#00F0FF'];         // "away team wears white"; site cyan if white is too close (e.g. vs silver)

function hexToRgb(h) { h = h.replace('#', ''); return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16)); }
function luminance(rgb) {
    const c = rgb.map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); });
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
}
function rgbToLab(rgb) {
    let [r, g, b] = rgb.map(v => { v /= 255; return v > 0.04045 ? Math.pow((v + 0.055) / 1.055, 2.4) : v / 12.92; });
    let x = (r * 0.4124 + g * 0.3576 + b * 0.1805) / 0.95047, y = r * 0.2126 + g * 0.7152 + b * 0.0722, z = (r * 0.0193 + g * 0.1192 + b * 0.9505) / 1.08883;
    [x, y, z] = [x, y, z].map(v => v > 0.008856 ? Math.cbrt(v) : 7.787 * v + 16 / 116);
    return [116 * y - 16, 500 * (x - y), 200 * (y - z)];
}
function deltaE(a, b) { const [p, q] = [rgbToLab(hexToRgb(a)), rgbToLab(hexToRgb(b))]; return Math.hypot(p[0] - q[0], p[1] - q[1], p[2] - q[2]); }
const isBlack = hex => luminance(hexToRgb(hex)) < 0.008;      // #000000, #101820 ...
const usable = team => (TEAM_COLORS[team] || []).filter(c => !isBlack(c));

// Home keeps its signature color; the away team switches to one of its own
// alternates if the colors are too close, else wears white.
function matchupColors(home, away) {
    const H = usable(home), A = usable(away);
    if (!H.length || !A.length) return null;
    const far = h => x => deltaE(x, h) >= MIN_DISTANCE;
    const a = A.find(far(H[0])) || AWAY_FALLBACKS.find(far(H[0]));
    if (a) return { home: H[0], away: a };
    for (const h of H.slice(1)) { const a2 = A.find(far(h)) || AWAY_FALLBACKS.find(far(h)); if (a2) return { home: h, away: a2 }; }
    return { home: H[0], away: AWAY_FALLBACKS[1] };
}

function gameColors(g) {
    return matchupColors(g.homeTeam.abbr, g.awayTeam.abbr)
        || { home: CONFIG.chartColors.data, away: CONFIG.chartColors.neutral };
}

function colorVars(g) {
    const c = gameColors(g);
    return `--home-c:${c.home};--away-c:${c.away};`;
}

// =============================================================================
// RENDERING - GAME PREVIEWS (upcoming games)
// =============================================================================

const WEEKDAY_SHORT = { Sunday: 'Sun', Monday: 'Mon', Tuesday: 'Tue', Wednesday: 'Wed', Thursday: 'Thu', Friday: 'Fri', Saturday: 'Sat' };

function fmtKickoff(g) {
    const d = g.gameday ? new Date(`${g.gameday}T12:00:00`) : null;
    const date = d ? d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '';
    let time = '';
    if (g.gametime) {
        const [h, m] = g.gametime.split(':').map(Number);
        time = `${((h + 11) % 12) + 1}:${String(m).padStart(2, '0')} ${h >= 12 ? 'PM' : 'AM'} ET`;
    }
    return [WEEKDAY_SHORT[g.weekday] || '', date, time].filter(Boolean).join(' · ');
}

function teamChip(t, home) {
    return `<span class="pv-team">
        ${t.logo ? `<img src="${t.logo}" alt="" class="pv-logo" onerror="this.style.display='none'">` : ''}
        <span class="pv-abbr">${t.abbr}</span>${home ? '<span class="pv-home-tag">home</span>' : ''}
    </span>`;
}

function previewCard(g, pv, maxTotal, todayET) {
    const p = g.projection;
    const league = pv.model?.leagueAveragePerGame;
    const homeW = p.total ? (p.home / p.total * 100) : 50;
    const isToday = g.gameday === todayET;
    return `
    <div class="preview-card ${isToday ? 'preview-card-today' : ''}" style="${colorVars(g)}" onclick="openPreviewModal('${g.gameId}')">
        <div class="pv-head">
            <div class="pv-matchup">${teamChip(g.awayTeam)}<span class="pv-at">@</span>${teamChip(g.homeTeam, true)}
                ${isToday ? '<span class="pv-today">Today</span>' : ''}</div>
            <div class="pv-when">${fmtKickoff(g)}${g.network ? ` · ${g.network}` : ''}</div>
        </div>
        <div class="pv-main">
            <div>
                <div class="pv-total">${fmtNum(p.total, 1)}</div>
                <div class="pv-total-label">projected flags · ${p.range[0]}–${p.range[1]} likely</div>
            </div>
            <div class="pv-vs">${pctBadge(p.total, league)}<span>vs league ${fmtNum(league, 1)}</span></div>
        </div>
        <div class="pv-range-track" title="Likely range ${p.range[0]}–${p.range[1]}">
            <div class="pv-range" style="left:${p.range[0] / maxTotal * 100}%; width:${(p.range[1] - p.range[0]) / maxTotal * 100}%"></div>
            <div class="pv-point" style="left:${p.total / maxTotal * 100}%"></div>
        </div>
        <div class="pv-split">
            <span>${g.awayTeam.abbr} <strong>${fmtNum(p.away, 1)}</strong></span>
            <div class="pv-split-bar"><div class="pv-split-away" style="width:${100 - homeW}%"></div><div class="pv-split-home" style="width:${homeW}%"></div></div>
            <span><strong>${fmtNum(p.home, 1)}</strong> ${g.homeTeam.abbr}</span>
        </div>
        <div class="pv-foot">
            <span class="${g.crew ? '' : 'pv-tba'}">${g.crew ? `Crew: ${g.crew.name}` : 'Crew TBA'}</span>
            <span>~${fmtNum(p.yards)} penalty yds</span>
        </div>
    </div>`;
}

function renderPreviews() {
    const grid = document.getElementById('previewGrid');
    if (!grid) return;
    const weeks = (state.previews || []).filter(w => w.games?.length);
    if (!weeks.length) {
        grid.innerHTML = '<p class="season-error">Upcoming game previews aren\'t available yet.</p>';
        return;
    }

    const todayET = new Date().toLocaleDateString('en-CA', { timeZone: 'America/New_York' });
    const full = weeks.find(w => !w.remainingOnly) || weeks[0];
    document.getElementById('previewsTitle').textContent =
        weeks.length > 1 ? `Week ${weeks[0].week} Finale & Week ${full.week} Previews` : `Week ${full.week} Previews`;

    const a = full.assignments || {};
    const crewNote = a.assigned >= a.games ? 'All crews assigned.'
        : a.assigned ? `Week ${full.week} crews assigned for ${a.assigned} of ${a.games} games.`
        : `Week ${full.week} crew assignments usually post Tuesday — projections update automatically.`;
    document.getElementById('previewsSubtitle').firstChild.textContent =
        `Projected penalties for every upcoming game, ranked most flags first. ${crewNote} `;

    // One shared scale for the range bars across all groups
    const maxTotal = Math.max(...weeks.flatMap(w => w.games.map(g => g.projection.range[1])), 1);

    grid.innerHTML = weeks.map(w => {
        const games = [...w.games].sort((x, y) => y.projection.total - x.projection.total);   // most flags first
        const label = w.remainingOnly
            ? `Week ${w.week} · ${games.every(g => g.gameday === todayET) ? 'Tonight' : 'Remaining'}`
            : `Week ${w.week}`;
        return `
            <div class="preview-group">
                <h3 class="preview-group-title">${label} <span class="modal-muted">${games.length} game${games.length > 1 ? 's' : ''}</span></h3>
                <div class="preview-grid-inner">${games.map(g => previewCard(g, w, maxTotal, todayET)).join('')}</div>
            </div>`;
    }).join('');

    const src = weeks.map(w => w.assignments?.source?.url).find(Boolean);
    document.getElementById('previewCredit').innerHTML = src
        ? `Crew assignments via <a href="${src}" target="_blank" rel="noopener">Football Zebras</a>.`
        : 'Crew assignments via <a href="https://www.footballzebras.com/category/assignments/" target="_blank" rel="noopener">Football Zebras</a> once posted.';
}

function openPreviewModal(gameId) {
    setDeepLink('game', gameId);
    const pv = (state.previews || []).find(w => w.games?.some(x => x.gameId === gameId));
    const g = pv?.games.find(x => x.gameId === gameId);
    const modal = document.getElementById('modal');
    const body = document.getElementById('modalBody');
    if (!g || !modal || !body) return;
    if (state.charts.modal) { state.charts.modal.destroy(); state.charts.modal = null; }

    const p = g.projection, H = g.homeTeam, A = g.awayTeam;
    const league = pv.model.leagueAveragePerGame;
    const crewSeason = g.crew
        ? [...(state.season?.crewChiefs || []), ...(state.season?.inactiveCrewChiefs || [])].find(c => c.slug === g.crew.slug)
        : null;

    document.getElementById('modalTitle').textContent = `${A.abbr} @ ${H.abbr}`;
    document.getElementById('modalSubtitle').textContent =
        `Week ${pv.week} · ${fmtKickoff(g)}${g.network ? ` · ${g.network}` : ''} · ${g.crew ? `Crew: ${g.crew.name}` : 'Crew TBA'}`;

    // Drivers (+/- flags vs a league-average matchup)
    const maxDrv = Math.max(...p.drivers.map(d => Math.abs(d.value)), 0.5);
    const drivers = p.drivers.map(d0 => ({ ...d0, value: Math.abs(d0.value) < 0.05 ? 0 : d0.value }))   // no "-0.0"
                             .map(d => `
        <div class="drv-row">
            <div class="drv-label">${d.label}</div>
            <div class="drv-track">
                <div class="drv-mid"></div>
                <div class="drv-bar ${d.value >= 0 ? 'drv-up' : 'drv-down'}"
                     style="${d.value >= 0 ? 'left:50%' : `right:50%`}; width:${Math.abs(d.value) / maxDrv * 50}%"></div>
            </div>
            <div class="drv-val ${d.value > 0.05 ? 'pct-up' : d.value < -0.05 ? 'pct-down' : ''}">${d.value > 0 ? '+' : ''}${fmtNum(d.value, 1)}</div>
        </div>`).join('');

    // Projected table: type x home/away
    const typeRows = g.byType.map(r => `
        <tr>
            <td>${r.type}</td>
            <td>${fmtNum(r.away, 1)}</td>
            <td>${fmtNum(r.home, 1)}</td>
            <td><strong>${fmtNum(r.total, 1)}</strong> ${pctBadge(r.total, r.leagueTotal)}</td>
            <td class="season-prev">${fmtNum(r.total * r.yardsEach)} yds</td>
        </tr>`).join('');

    // Quarters
    const qMax = Math.max(...p.byQuarter.map(q => q.home + q.away), 0.1);
    const quarters = p.byQuarter.map(q => `
        <div class="pvq">
            <div class="pvq-bars">
                <div class="pvq-stack" style="height:${(q.home + q.away) / qMax * 100}%">
                    <div class="pvq-away" style="flex:${q.away}"></div>
                    <div class="pvq-home" style="flex:${q.home}"></div>
                </div>
            </div>
            <div class="pvq-total">${fmtNum(q.home + q.away, 1)}</div>
            <div class="pvq-split">${A.abbr} ${fmtNum(q.away, 1)} · ${H.abbr} ${fmtNum(q.home, 1)}</div>
            <div class="pvq-label">Q${q.quarter}</div>
        </div>`).join('');

    // Crew
    const crewHtml = g.crew ? `
        <div class="modal-section">
            <h4>The crew: <a href="#" onclick="openRefereeModal('${g.crew.slug}'); return false;">${g.crew.name}</a></h4>
            <div class="pv-crew-grid">
                <div class="season-stat">
                    <div class="season-stat-label">Crew effect on this game</div>
                    <div class="season-stat-value">${p.drivers[0].value > 0 ? '+' : ''}${fmtNum(p.drivers[0].value, 1)}</div>
                    <div class="season-stat-compare">flags vs an average crew (${fmtNum((g.crew.overallFactor - 1) * 100, 0)}%)</div>
                </div>
                ${crewSeason?.current ? `
                <div class="season-stat">
                    <div class="season-stat-label">${state.season.currentSeason} pen/game</div>
                    <div class="season-stat-value">${fmtNum(crewSeason.current.perGame, 1)}</div>
                    <div class="season-stat-compare">${crewSeason.current.games} games ·
                        last season ${fmtNum(crewSeason.baselines?.lastSeason?.perGame, 1)}</div>
                </div>` : ''}
            </div>
            <div class="pv-tilts">
                ${g.crew.typeTilts.map(t => `<span class="pv-tilt">${t.type} ${pctBadge(t.factor, 1)}</span>`).join('')}
            </div>
            <p class="modal-footnote">Tilts compare how often this crew calls each type vs the league (last 3 seasons, ${g.crew.gamesInModel} games, shrunk toward average).</p>
        </div>` : `
        <div class="modal-section">
            <h4>The crew</h4>
            <p class="modal-footnote">Not assigned yet. Football Zebras usually posts assignments Tuesday morning; this projection will update with the crew factor once it's published.</p>
        </div>`;

    // Teams
    const teamCol = (t, d, side) => `
        <div class="pv-team-col">
            <h5>${t.abbr} <span class="modal-muted">${t.name || ''}</span></h5>
            <div class="pv-kv"><span>Penalties/game</span><strong>${fmtNum(d.perGame, 1)}</strong>
                ${d.lastSeasonPerGame != null ? pctBadge(d.perGame, d.lastSeasonPerGame, { small: d.games < MIN_GAMES_FOR_PCT, title: `vs ${d.lastSeasonPerGame} last season` }) : ''}</div>
            <div class="pv-kv"><span>Most-penalized rank</span><strong>${d.rank ? `#${d.rank} of 32` : '—'}</strong></div>
            <div class="pv-kv"><span>Offense / Defense</span><strong>${fmtNum(d.offensePerGame, 1)} / ${fmtNum(d.defensePerGame, 1)}</strong></div>
            <div class="pv-kv"><span>Drawn from opponents</span><strong>${fmtNum(d.drawnPerGame, 1)}</strong></div>
            <div class="pv-kv"><span>Penalty yds/game</span><strong>${fmtNum(d.yardsPerGame, 0)}</strong></div>
            <div class="pv-kv"><span>Most common</span><strong>${d.mostCommon || '—'}</strong></div>
            <div class="pv-watch">
                <div class="pv-watch-title">Watchlist (${pv.season})</div>
                ${(d.watchlist || []).map(w => `
                    <div class="pv-watch-row"><span>${w.player}</span>
                    <span>${w.count} flag${w.count === 1 ? "" : "s"} · ${w.yards} yds</span>
                    <span class="modal-muted">${w.types.map(x => `${x.type}${x.count > 1 ? ` ×${x.count}` : ''}`).join(', ')}</span></div>`).join('') || '<span class="modal-muted">No individual penalties yet</span>'}
            </div>
        </div>`;

    // Context
    const c = g.context, ref = pv.contextReference || {};
    const chips = [];
    if (c.primetime) chips.push('Primetime');
    if (g.weekday === 'Thursday') chips.push(`Thursday night${ref.thursday ? ` (avg ${ref.thursday} flags vs ${ref.sunday} Sunday)` : ''}`);
    if (c.divisionGame) chips.push(`Division game${ref.division ? ` (avg ${ref.division} vs ${ref.nonDivision})` : ''}`);
    if (c.neutralSite) chips.push('Neutral site');
    if (c.roof) chips.push(`Roof: ${c.roof}`);
    if (c.surface) chips.push(`Surface: ${c.surface}`);
    if (c.homeRest != null && c.awayRest != null) chips.push(`Rest: ${A.abbr} ${c.awayRest}d · ${H.abbr} ${c.homeRest}d`);
    if (c.spread != null) chips.push(`Spread: ${c.spread > 0 ? `${H.abbr} −${c.spread}` : c.spread < 0 ? `${A.abbr} −${Math.abs(c.spread)}` : 'Pick'}${Math.abs(c.spread) <= 3 ? ' (expected close — late flags tend to drop)' : ''}`);
    if (c.total != null) chips.push(`O/U ${c.total}`);
    if (c.temp != null) chips.push(`${c.temp}°F`);
    if (c.wind != null) chips.push(`Wind ${c.wind} mph`);
    if (c.awayQB && c.homeQB) chips.push(`QBs: ${c.awayQB} vs ${c.homeQB}`);

    const h2h = (g.headToHead || []).map(m => `
        <div class="game-item">
            <div class="game-teams"><span>${m.away}</span><span class="game-vs">@</span><span>${m.home}</span></div>
            <div class="game-info">
                ${m.awayScore != null ? `<div class="game-score">${m.awayScore} - ${m.homeScore}</div>` : ''}
                <div class="game-date">${m.season} Wk ${m.week}${m.crew ? ` · ${m.crew}` : ''}</div>
            </div>
            <div class="game-penalties">
                <div class="game-penalties-value">${m.flags}</div>
                <div class="game-penalties-label">${m.away} ${m.awayFlags} · ${m.home} ${m.homeFlags}</div>
            </div>
        </div>`).join('');

    body.setAttribute('style', colorVars(g));
    body.innerHTML = `
        <div class="modal-section">
            <div class="season-league pv-headline">
                <div class="season-stat">
                    <div class="season-stat-label">Projected flags</div>
                    <div class="season-stat-value">${fmtNum(p.total, 1)}</div>
                    <div class="season-stat-compare">${pctBadge(p.total, league)} likely ${p.range[0]}–${p.range[1]}</div>
                </div>
                <div class="season-stat">
                    <div class="season-stat-label">On ${A.abbr} (away)</div>
                    <div class="season-stat-value">${fmtNum(p.away, 1)}</div>
                    <div class="season-stat-compare">likely ${p.awayRange[0]}–${p.awayRange[1]} · ~${fmtNum(p.awayYards)} yds</div>
                </div>
                <div class="season-stat">
                    <div class="season-stat-label">On ${H.abbr} (home)</div>
                    <div class="season-stat-value">${fmtNum(p.home, 1)}</div>
                    <div class="season-stat-compare">likely ${p.homeRange[0]}–${p.homeRange[1]} · ~${fmtNum(p.homeYards)} yds</div>
                </div>
                <div class="season-stat">
                    <div class="season-stat-label">Chance of ${p.overThreshold + 1}+ flags</div>
                    <div class="season-stat-value">${Math.round(p.probOver * 100)}%</div>
                    <div class="season-stat-compare">league avg game: ${fmtNum(league, 1)}</div>
                </div>
            </div>
        </div>

        <div class="modal-section">
            <h4>What's driving the projection</h4>
            ${drivers}
            <p class="modal-footnote">Extra or fewer flags vs a league-average matchup with an average crew.</p>
        </div>

        <div class="modal-section">
            <h4>Projected penalties by type</h4>
            <div class="table-scroll">
                <table class="pv-table">
                    <thead><tr><th>Type</th><th>On ${A.abbr}</th><th>On ${H.abbr}</th><th>Total vs league</th><th>Yards</th></tr></thead>
                    <tbody>${typeRows}</tbody>
                </table>
            </div>
        </div>

        <div class="modal-section">
            <h4>⏱️ Quarter by quarter</h4>
            <div class="pair-legend"><span><i class="pair-swatch pvq-away"></i>${A.abbr}</span><span><i class="pair-swatch pvq-home"></i>${H.abbr}</span></div>
            <div class="pvq-grid">${quarters}</div>
        </div>

        ${crewHtml}

        <div class="modal-section">
            <h4>🏈 Team discipline (${pv.season})</h4>
            <div class="pv-teams">${teamCol(A, g.teams.away, 'away')}${teamCol(H, g.teams.home, 'home')}</div>
        </div>

        <div class="modal-section">
            <h4>Context</h4>
            <div class="pv-chips">${chips.map(x => `<span class="pv-chip">${x}</span>`).join('')}</div>
            <p class="modal-footnote">Shown for reference; not added into the projection.</p>
        </div>

        ${h2h ? `<div class="modal-section"><h4>Recent meetings</h4><div class="game-list">${h2h}</div></div>` : ''}

        <p class="modal-footnote">Projection uses ${pv.model.seasons.join(', ')} regular seasons, weighted toward ${pv.season}.
        ${pv.assignments?.source?.url ? `Crew assignments via <a href="${pv.assignments.source.url}" target="_blank" rel="noopener">Football Zebras</a>.` : ''}</p>
    `;
    modal.classList.add('active');
}

// =============================================================================
// TRACK RECORD (prediction scorecard)
// Live = published before kickoff. Backtest = rebuilt afterward using only data
// available before each week. Always labeled separately.
// =============================================================================

function renderTrackRecord() {
    const box = document.getElementById('trackRecord');
    const sc = state.scorecard;
    if (!box || !sc) return;
    const L = sc.live?.summary, B = sc.backtest?.lastSeason?.summary, C = sc.backtest?.currentSeason?.summary;
    const lastS = sc.backtest?.lastSeason?.season;
    const item = (label, s, note) => s ? `
        <div class="tr-item">
            <div class="tr-label">${label}</div>
            <div class="tr-nums"><strong>${fmtNum(s.avgMiss, 1)}</strong> avg miss · <strong>${fmtNum(s.hitRate, 0)}%</strong> in range</div>
            <div class="tr-note">${note}</div>
        </div>` : '';
    box.innerHTML = `
        <div class="tr-head">
            <span class="tr-title">Track record</span>
            <button class="info-trigger-inline" onclick="openScorecardModal()">See every game →</button>
        </div>
        <div class="tr-items">
            ${item('Published before kickoff', L, L ? `${L.games} game${L.games === 1 ? '' : 's'} graded so far` : '')}
            ${item(`${lastS} full season (backtest)`, B, B ? `${B.games} games` : '')}
            ${item(`${sc.season} so far (backtest)`, C, C ? `${C.games} games` : '')}
        </div>`;
}

function openScorecardModal() {
    const sc = state.scorecard;
    const modal = document.getElementById('modal');
    const body = document.getElementById('modalBody');
    if (!sc || !modal || !body) return;
    setDeepLink('scorecard', 'all');
    if (state.charts.modal) { state.charts.modal.destroy(); state.charts.modal = null; }
    body.removeAttribute('style');
    document.getElementById('modalTitle').textContent = 'Track Record';
    document.getElementById('modalSubtitle').textContent = 'How close our flag projections land, graded after every game';

    const tile = (label, v, sub) => `<div class="season-stat"><div class="season-stat-label">${label}</div>
        <div class="season-stat-value">${v}</div><div class="season-stat-compare">${sub}</div></div>`;
    const block = (title, s, note) => !s ? '' : `
        <div class="modal-section">
            <h4>${title}</h4>
            <div class="season-league pv-headline">
                ${tile('Average miss', `${fmtNum(s.avgMiss, 1)}`, 'flags per game')}
                ${tile('In the likely range', `${fmtNum(s.hitRate, 0)}%`, 'target ≈ 80%')}
                ${tile('Within ±3 flags', `${fmtNum(s.within3, 0)}%`, `${s.games} games`)}
                ${s.skillPct != null ? tile('vs guessing the average', `${s.skillPct > 0 ? '+' : ''}${fmtNum(s.skillPct, 1)}%`, `league-average guess misses by ${fmtNum(s.baselineAvgMiss, 1)}`) : ''}
            </div>
            ${note ? `<p class="modal-footnote">${note}</p>` : ''}
        </div>`;

    const live = sc.live?.games || [];
    const rows = live.map(g => `
        <tr onclick="openPreviewModal('${g.gameId}')">
            <td>Wk ${g.week}</td>
            <td><strong>${g.away} @ ${g.home}</strong></td>
            <td class="season-prev">${g.crew || '—'}</td>
            <td>${fmtNum(g.projected, 1)} <span class="modal-muted">(${g.low}–${g.high})</span></td>
            <td><strong>${g.actual}</strong></td>
            <td><span class="season-delta ${g.miss > 0 ? 'pct-up' : g.miss < 0 ? 'pct-down' : ''}">${g.miss > 0 ? '+' : ''}${fmtNum(g.miss, 1)}</span></td>
            <td>${g.inRange ? '✓' : '✗'}</td>
        </tr>`).join('');

    const weekRows = (sc.backtest?.currentSeason?.byWeek || []).map(w => `
        <tr><td>Wk ${w.week}</td><td>${w.games}</td><td>${fmtNum(w.avgMiss, 1)}</td><td>${fmtNum(w.hitRate, 0)}%</td></tr>`).join('');

    body.innerHTML = `
        ${block('Published before kickoff', sc.live?.summary, 'Projections exactly as they appeared on the site before each game. Grows every week.')}
        <div class="modal-section">
            <h4>Every published projection</h4>
            ${rows ? `<div class="table-scroll"><table class="pv-table">
                <thead><tr><th>Week</th><th>Game</th><th>Crew</th><th>Projected</th><th>Actual</th><th>Miss</th><th>In range</th></tr></thead>
                <tbody>${rows}</tbody></table></div>
                <p class="modal-footnote">Miss = actual − projected: <span class="pct-up">red</span> means more flags than projected, <span class="pct-down">green</span> fewer.</p>`
              : '<p class="modal-footnote">The first published projections are graded after this week\'s games.</p>'}
        </div>
        ${block(`${sc.backtest?.lastSeason?.season} full season (backtest)`, sc.backtest?.lastSeason?.summary,
                'Rebuilt afterward, game by game, using only data that existed before each week. Shows how the model would have done.')}
        ${block(`${sc.season} so far (backtest)`, sc.backtest?.currentSeason?.summary, '')}
        ${weekRows ? `<div class="modal-section"><h4>${sc.season} by week (backtest)</h4>
            <div class="table-scroll"><table class="pv-table"><thead><tr><th>Week</th><th>Games</th><th>Avg miss</th><th>In range</th></tr></thead>
            <tbody>${weekRows}</tbody></table></div></div>` : ''}
        <div class="modal-section">
            <h4>How it's graded</h4>
            <p class="modal-footnote">${Object.values(sc.definitions || {}).join(' · ')}</p>
        </div>`;
    modal.classList.add('active');
}

// =============================================================================
// SCOREBOARD (Data section): league running totals by timeframe + weekly log
// =============================================================================

// Week picker: the "Week N" option can be any week of this season (default: last completed)
function setScoreboardWeek(week) {
    state.scoreboardWeek = Number(week);
    state.scoreboardFrame = 'latestWeek';
    state.sbWeekMenuOpen = false;
    renderScoreboard(true);
}

// The arrow opens a list of every week (built into the page, so it works the same everywhere)
function toggleScoreboardWeekMenu(e) {
    e?.stopPropagation();
    state.sbWeekMenuOpen = !state.sbWeekMenuOpen;
    renderScoreboard(false);
    if (state.sbWeekMenuOpen) document.querySelector('.sb-week-menu .sel')?.focus();
}
document.addEventListener('click', (e) => {
    if (state.sbWeekMenuOpen && !e.target.closest('.sb-week')) { state.sbWeekMenuOpen = false; renderScoreboard(false); }
});
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && state.sbWeekMenuOpen) { state.sbWeekMenuOpen = false; renderScoreboard(false); }
});

function scoreboardFrame(sb) {
    const key = sb.frames.some(f => f.key === state.scoreboardFrame) ? state.scoreboardFrame : sb.defaultFrame;
    let f = sb.frames.find(x => x.key === key) || sb.frames[0];
    if (key === 'latestWeek' && sb.weekFrames?.length) {
        const wk = state.scoreboardWeek ?? sb.defaultWeek;
        f = { ...(sb.weekFrames.find(w => w.week === wk) || f), key: 'latestWeek' };
    }
    return { key, f };
}

function setScoreboardFrame(key) {
    state.scoreboardFrame = key;
    renderScoreboard(true);
}

function countUp(el, to, decimals, ms = 700) {
    if (to == null || isNaN(to)) { el.textContent = '—'; return; }
    if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) { el.textContent = fmtNum(to, decimals); return; }
    const from = parseFloat((el.dataset.v ?? '0')) || 0;
    const t0 = performance.now();
    const step = (t) => {
        const k = Math.min(1, (t - t0) / ms), e = 1 - Math.pow(1 - k, 3);
        el.textContent = fmtNum(from + (to - from) * e, decimals);
        if (k < 1) requestAnimationFrame(step); else el.dataset.v = String(to);
    };
    requestAnimationFrame(step);
}

function renderScoreboard(animate = false) {
    const box = document.getElementById('scoreboard');
    const sb = state.scoreboard;
    if (!box) return;
    if (!sb?.frames?.length) { box.innerHTML = '<p class="season-error">Scoreboard data isn\'t available yet.</p>'; return; }
    const { key, f } = scoreboardFrame(sb);
    const selWeek = state.scoreboardWeek ?? sb.defaultWeek;
    const chevron = '<svg class="sb-chev" viewBox="0 0 12 12" aria-hidden="true"><path d="M2.5 4.5 6 8l3.5-3.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>';
    const weekButton = (x) => {
        if (x.key !== 'latestWeek' || !sb.weekFrames?.length) return null;
        const on = key === 'latestWeek';
        const open = !!state.sbWeekMenuOpen;
        return `<span class="baseline-btn sb-week ${on ? 'active' : ''} ${open ? 'open' : ''}">
            <button class="sb-week-label" aria-pressed="${on}" onclick="setScoreboardWeek(${selWeek})">Week ${selWeek}</button>
            <button class="sb-week-arrow" aria-label="Choose a week" aria-haspopup="listbox" aria-expanded="${open}"
                    onclick="toggleScoreboardWeekMenu(event)">${chevron}</button>
            ${open ? `<div class="sb-week-menu" role="listbox" aria-label="Weeks">
                ${sb.weekFrames.slice().reverse().map(w => `
                    <button role="option" aria-selected="${w.week === selWeek}" class="${w.week === selWeek ? 'sel' : ''}"
                            onclick="setScoreboardWeek(${w.week})">
                        <span>Week ${w.week}</span>
                        <span class="sb-week-meta">${w.complete ? `${fmtNum(w.perGame, 1)} flags/game` : `in progress · ${w.games} of ${w.scheduled}`}</span>
                    </button>`).join('')}
            </div>` : ''}
        </span>`;
    };

    const big = (id, label, v, d = 0, sub = '') =>
        `<div class="sb-cell sb-big"><div class="sb-label">${label}</div><div class="sb-num" data-to="${v ?? ''}" data-d="${d}" id="${id}">${animate ? '' : fmtNum(v, d)}</div>${sub ? `<div class="sb-sub">${sub}</div>` : ''}</div>`;
    const cell = (id, label, v, d = 1, unit = '', sub = '') =>
        `<div class="sb-cell"><div class="sb-label">${label}</div><div class="sb-val"><span class="sb-num" data-to="${v ?? ''}" data-d="${d}" id="${id}">${animate ? '' : fmtNum(v, d)}</span>${unit}</div>${sub ? `<div class="sb-sub">${sub}</div>` : ''}</div>`;
    const split = (label, aLabel, aPct, bLabel) => `
        <div class="sb-cell sb-split">
            <div class="sb-label">${label}</div>
            <div class="sb-split-bar"><i style="width:${aPct ?? 0}%"></i></div>
            <div class="sb-split-legend"><span><strong>${fmtNum(aPct, 0)}%</strong> ${aLabel}</span><span>${bLabel} <strong>${fmtNum(100 - (aPct ?? 0), 0)}%</strong></span></div>
        </div>`;

    const log = (sb.weeklyLog || []).slice().reverse().map(w => `
        <tr>
            <td><strong>Wk ${w.week}</strong>${w.complete ? '' : ` <span class="sb-live">in progress · ${w.games} of ${w.scheduled}</span>`}</td>
            <td>${w.games}</td><td>${fmtNum(w.plays)}</td><td><strong>${fmtNum(w.penalties)}</strong></td><td>${fmtNum(w.yards)}</td>
            <td>${fmtNum(w.pctPlays, 1)}%</td>
            <td><span class="sb-mini"><i style="width:${Math.min(100, (w.perGame || 0) / 22 * 100)}%"></i></span>${fmtNum(w.perGame, 1)}</td>
            <td>${fmtNum(w.firstDowns)}</td>
        </tr>`).join('');

    box.innerHTML = `
        <div class="sb-head">
            <div>
                <div class="sb-title">The Scoreboard</div>
                <div class="modal-actions block-actions">
                    <button class="modal-share" onclick="copyBlockLink('scoreboard', this)">Copy link</button>
                    <button class="modal-share" onclick="exportBlock('scoreboard', 'png', this)">Save PNG</button>
                    <button class="modal-share" onclick="exportBlock('scoreboard', 'pdf', this)">Save PDF</button>
                </div>
                <div class="sb-desc">${f.description} · accepted penalties</div>
            </div>
            <div class="baseline-toggle sb-toggle" role="group" aria-label="Timeframe">${sb.frames.map(x => weekButton(x) ?? `
                <button class="baseline-btn ${x.key === key ? 'active' : ''}" aria-pressed="${x.key === key}"
                        onclick="setScoreboardFrame('${x.key}')">${x.label}</button>`).join('')}</div>
        </div>

        <div class="sb-grid sb-grid-4">
            ${big('sbGames', 'Games', f.games)}
            ${big('sbPlays', 'Plays', f.plays)}
            ${big('sbFlags', 'Flags', f.penalties, 0, 'accepted penalties')}
            ${big('sbYards', 'Penalty yards', f.yards)}
        </div>

        <div class="sb-grid sb-grid-4">
            ${cell('sbPct', 'Plays with a flag', f.pctPlays, 1, '<span class="sb-unit">%</span>', `a flag every <strong>${fmtNum(f.flagEveryPlays, 1)}</strong> plays`)}
            ${cell('sbPerGame', 'Flags per game', f.perGame, 1, '', `one every <strong>${fmtNum(f.minutesPerFlag, 1)}</strong> min of game clock`)}
            ${cell('sbYpg', 'Penalty yards per game', f.yardsPerGame, 1, '', `<strong>${fmtNum(f.yardsPerPenalty, 1)}</strong> yards per flag`)}
            ${cell('sbFd', 'First downs by penalty', f.firstDowns, 0, '', `<strong>${fmtNum(f.firstDownsPerGame, 1)}</strong> per game handed over`)}
        </div>

        <div class="sb-grid sb-grid-3">
            ${split('Who gets flagged', 'offense', f.offenseShare, 'defense')}
            ${split('Before or after the snap', 'pre-snap', f.preSnapShare, 'live ball')}
            ${split('Home or road', 'home team', f.homeShare, 'road team')}
        </div>

        <div class="sb-grid sb-grid-4 sb-leaders">
            <div class="sb-cell"><div class="sb-label">Most common call</div><div class="sb-lead">${f.mostCommon?.type ?? '—'}</div>
                <div class="sb-sub"><strong>${fmtNum(f.mostCommon?.count)}</strong> calls · ${fmtNum(f.mostCommon?.pct, 0)}% of all flags</div></div>
            <div class="sb-cell"><div class="sb-label">Most flagged team</div><div class="sb-lead">${f.mostFlaggedTeam?.team ?? '—'}</div>
                <div class="sb-sub"><strong>${fmtNum(f.mostFlaggedTeam?.perGame, 1)}</strong> flags per game</div></div>
            <div class="sb-cell"><div class="sb-label">Cleanest team</div><div class="sb-lead">${f.cleanestTeam?.team ?? '—'}</div>
                <div class="sb-sub"><strong>${fmtNum(f.cleanestTeam?.perGame, 1)}</strong> flags per game</div></div>
            <div class="sb-cell"><div class="sb-label">Flag-heaviest crew</div><div class="sb-lead">${f.topCrew?.name ?? '—'}</div>
                <div class="sb-sub"><strong>${fmtNum(f.topCrew?.perGame, 1)}</strong> flags per game</div></div>
        </div>

        ${log ? `<div class="sb-log">
            <div class="sb-label" style="margin-bottom:0.6rem">${sb.season} running log</div>
            <div class="table-scroll"><table class="pv-table">
                <thead><tr><th>Week</th><th>Games</th><th>Plays</th><th>Flags</th><th>Yards</th><th>% of plays</th><th>Flags / game</th><th>1st downs</th></tr></thead>
                <tbody>${log}</tbody>
            </table></div>
        </div>` : ''}
        <p class="modal-footnote" style="margin-top:0.75rem">${sb.notes}</p>`;

    if (animate) box.querySelectorAll('.sb-num').forEach(el => {
        const to = el.dataset.to === '' ? null : parseFloat(el.dataset.to);
        countUp(el, to, parseInt(el.dataset.d || '0', 10));
    });
    else box.querySelectorAll('.sb-num').forEach(el => { el.dataset.v = el.dataset.to; });
}

// =============================================================================
// FLAGS PER GAME BY WEEK OF SEASON (League Trends)
// =============================================================================

// Season chips: this season is always on; any past season can be added; the
// all-seasons average and the range band can be switched on/off
const SEASON_COLORS = ['#4DA3FF', '#FF8F3F', '#2EC4D6', '#F472B6', '#B07CFF', '#D2B48C', '#8B95A7', '#7C3AED'];
function seasonColor(season, seasons) {
    const past = seasons.filter(x => x !== state.typeTrends?.season);
    return SEASON_COLORS[past.indexOf(season) % SEASON_COLORS.length] || '#8B95A7';
}
function toggleWeekLayer(key) {
    if (!state.weekLayers) state.weekLayers = { avg: true, band: true, years: [] };
    const L = state.weekLayers;
    if (key === 'avg' || key === 'band') L[key] = !L[key];
    else if (key === 'none') { L.years = []; }
    else if (key === 'all') { L.years = (state.typeTrends?.weekly?.seasons || []).map(x => x.season).filter(x => x !== state.typeTrends.season); }
    else {
        const y = Number(key);
        L.years = L.years.includes(y) ? L.years.filter(x => x !== y) : [...L.years, y].sort();
    }
    renderWeekChart();
}

// Draws a label at the end of a line ("2026", "2020–25 average") so nobody needs the legend
const endLabelPlugin = {
    id: 'endLabels',
    afterDatasetsDraw(chart) {
        const { ctx } = chart;
        chart.data.datasets.forEach((ds, i) => {
            if (!ds._endLabel) return;
            const meta = chart.getDatasetMeta(i);
            if (meta.hidden) return;
            let k = ds.data.length - 1;
            while (k >= 0 && ds.data[k] == null) k--;
            if (k < 0) return;
            const pt = meta.data[k];
            ctx.save();
            ctx.font = `600 12px ${getComputedStyle(document.documentElement).getPropertyValue('--font-body') || 'sans-serif'}`;
            ctx.fillStyle = ds._labelColor || ds.borderColor;
            const text = ds._endLabel;
            const w = ctx.measureText(text).width;
            const right = chart.chartArea.right;
            const x = pt.x + 8 + w > right ? pt.x - w - 8 : pt.x + 8;
            ctx.fillText(text, x, pt.y + (ds._labelDy || -8));
            ctx.restore();
        });
    }
};

function renderWeekChart() {
    const canvas = document.getElementById('weekChart');
    const wk = state.typeTrends?.weekly;
    if (!canvas || !wk?.seasons?.length) return;
    if (state.charts.week) state.charts.week.destroy();
    const cur = state.typeTrends.season;
    const maxWeek = Math.max(18, ...wk.seasons.flatMap(s => s.weeks.map(w => w.week)));
    const labels = Array.from({ length: maxWeek }, (_, i) => i + 1);
    const series = (weeks, f = 'perGame') => labels.map(n => weeks.find(w => w.week === n)?.[f] ?? null);
    const now = wk.seasons.find(s => s.season === cur);
    const doneWeeks = (now?.weeks || []).filter(w => w.complete);           // only finished weeks are drawn
    const inProgress = (now?.weeks || []).find(w => !w.complete);
    const avgLabel = wk.priorLabel ? wk.priorLabel.replace(' avg', ' average') : 'Past seasons average';

    // Plain-English takeaway: this season vs the usual for the same weeks
    const take = document.getElementById('weekTakeaway');
    if (take && doneWeeks.length) {
        const n = doneWeeks.length;
        const curAvg = doneWeeks.reduce((a, w) => a + w.perGame * w.games, 0) / doneWeeks.reduce((a, w) => a + w.games, 0);
        const usual = doneWeeks.map(w => wk.priorAverage.find(p => p.week === w.week)?.perGame).filter(v => v != null);
        const usualAvg = usual.reduce((a, v) => a + v, 0) / usual.length;
        const pct = (curAvg / usualAvg - 1) * 100;
        const late = wk.priorAverage.filter(p => p.week >= 15), early = wk.priorAverage.filter(p => p.week <= 4);
        const fade = early.length && late.length
            ? (1 - (late.reduce((a, p) => a + p.perGame, 0) / late.length) / (early.reduce((a, p) => a + p.perGame, 0) / early.length)) * 100 : null;
        take.innerHTML = `Flags usually <strong>fade as the season goes on</strong>${fade ? ` (Weeks 15–18 average about ${fmtNum(fade, 0)}% fewer than Weeks 1–4)` : ''}. ` +
            `Through Week ${doneWeeks.at(-1).week}, ${cur} is averaging <strong class="y">${fmtNum(curAvg, 1)}</strong> per game, ` +
            `<strong>${fmtNum(Math.abs(pct), 0)}% ${pct >= 0 ? 'above' : 'below'}</strong> the usual ${fmtNum(usualAvg, 1)} for those weeks.` +
'';
    }
    const note = document.getElementById('weekNote');
    if (note) note.textContent = inProgress
        ? `Week ${inProgress.week} is added once all of its games are played (${inProgress.games} played so far).` : '';
    if (!state.weekLayers) state.weekLayers = { avg: true, band: true, years: [] };
    const L = state.weekLayers;
    const allSeasons = wk.seasons.map(x => x.season);
    const pastSeasons = allSeasons.filter(x => x !== cur);

    // Chips: this season (always on) · each past season · all-seasons average · range
    const chips = document.getElementById('weekChips');
    if (chips) {
        const chip = (key, label, on, color, locked = false, extra = '') =>
            `<button class="week-chip ${on ? 'on' : ''} ${locked ? 'locked' : ''} ${extra}" ${locked ? 'disabled aria-disabled="true" title="Always shown"' : ''}
                aria-pressed="${on}" onclick="toggleWeekLayer('${key}')"><i style="${color}"></i>${label}</button>`;
        chips.innerHTML =
            chip('cur', `${cur}`, true, `background:${CONFIG.chartColors.flag}`, true) +
            pastSeasons.slice().reverse().map(y => chip(String(y), String(y), L.years.includes(y), `background:${seasonColor(y, allSeasons)}`)).join('') +
            `<span class="week-chip-sep"></span>` +
            chip('avg', `${(wk.priorLabel || 'Past').replace(' avg', '')} average`, L.avg, 'background:#cfd2d6;height:3px') +
            chip('band', 'Range', L.band, 'background:rgba(255,255,255,0.18);height:10px') +
            (L.years.length < pastSeasons.length
                ? `<button class="week-chip week-chip-link" onclick="toggleWeekLayer('all')">All seasons</button>`
                : `<button class="week-chip week-chip-link" onclick="toggleWeekLayer('none')">Clear seasons</button>`);
    }

    const past = wk.seasons.filter(x => L.years.includes(x.season)).map(x => {
        const color = seasonColor(x.season, allSeasons);
        return { label: String(x.season), data: series(x.weeks), borderColor: color, backgroundColor: color, borderWidth: 2,
                 pointRadius: 0, pointHoverRadius: 4, tension: 0.3, spanGaps: true, order: 3,
                 _endLabel: String(x.season), _labelColor: color, _labelDy: 4 };
    });
    const datasets = [
        // shaded band: lowest to highest past season for each week
        L.band && { label: 'range-low', data: labels.map(n => wk.priorRange?.find(r => r.week === n)?.low ?? null),
          borderWidth: 0, pointRadius: 0, tension: 0.3, fill: false, order: 5, _band: true },
        L.band && { label: `${wk.priorLabel ? wk.priorLabel.replace(' avg', '') : 'Past'} range`, data: labels.map(n => wk.priorRange?.find(r => r.week === n)?.high ?? null),
          borderWidth: 0, pointRadius: 0, tension: 0.3, fill: '-1', backgroundColor: 'rgba(255,255,255,0.07)', order: 5, _band: true },
        ...past,
        L.avg && { label: avgLabel, data: series(wk.priorAverage), borderColor: '#cfd2d6', borderWidth: 2.5, pointRadius: 0,
          tension: 0.3, spanGaps: true, order: 2, _endLabel: avgLabel, _labelDy: 18 },
        doneWeeks.length && { label: String(cur), data: series(doneWeeks), borderColor: CONFIG.chartColors.flag,
          backgroundColor: CONFIG.chartColors.flag, borderWidth: 3.5, pointRadius: 5, pointHoverRadius: 7, tension: 0.25, order: 1,
          _endLabel: `${cur}`, _labelDy: -10 }
    ].filter(Boolean);

    state.charts.week = new Chart(canvas.getContext('2d'), {
        type: 'line',
        data: { labels, datasets },
        plugins: [endLabelPlugin],
        options: {
            responsive: true, maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            layout: { padding: { right: 8, top: 22 } },   // room for the end labels
            plugins: {
                legend: { display: false },
                tooltip: {
                    filter: (it) => it.raw != null && it.dataset.label !== 'range-low',
                    callbacks: {
                        title: (items) => `Week ${items[0].label}`,
                        label: (c) => {
                            if (c.dataset._band) {
                                const r = wk.priorRange?.find(x => x.week === Number(c.label));
                                return r ? `Past seasons ranged ${fmtNum(r.low, 1)}–${fmtNum(r.high, 1)}` : null;
                            }
                            return `${c.dataset.label}: ${fmtNum(c.raw, 1)} flags per game`;
                        }
                    }
                }
            },
            scales: {
                x: { title: { display: true, text: 'Week of the season', color: 'rgba(255,255,255,0.55)' },
                     grid: { display: false }, ticks: { color: 'rgba(255,255,255,0.65)' } },
                y: { grace: '6%', title: { display: true, text: 'Flags per game', color: 'rgba(255,255,255,0.55)' },
                     grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: 'rgba(255,255,255,0.65)' } }
            }
        }
    });
}

// =============================================================================
// PENALTY TYPE TRENDS (League Trends): which calls are rising or falling
// =============================================================================

function setTypeTrendsCompare(key) {
    state.typeTrendsCompare = key;
    renderTypeTrends();
}

function sparkline(points, w = 120, h = 30) {
    const vals = points.map(p => p.perGame ?? 0);
    const max = Math.max(...vals, 0.01), min = Math.min(...vals) * 0.9;   // scale to the data so changes are visible
    const x = i => 3 + i * (w - 6) / Math.max(1, vals.length - 1);
    const y = v => h - 3 - (v - min) / Math.max(0.0001, max - min) * (h - 6);
    const d = vals.map((v, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ');
    const last = vals.length - 1;
    return `<svg class="spark" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" aria-hidden="true">
        <path d="${d}" fill="none" stroke="#5c616a" stroke-width="1.6" stroke-linejoin="round"/>
        <circle cx="${x(last)}" cy="${y(vals[last])}" r="3" fill="#ffc400"/></svg>`;
}

function renderTypeTrends() {
    const box = document.getElementById('typeTrends');
    const tt = state.typeTrends;
    if (!box) return;
    if (!tt?.types?.length) { box.innerHTML = '<p class="season-error">Penalty trend data isn\'t available yet.</p>'; return; }
    const key = tt.comparisons.some(c => c.key === state.typeTrendsCompare) ? state.typeTrendsCompare : tt.defaultComparison;
    const comp = tt.comparisons.find(c => c.key === key);
    const first = tt.types[0].bySeason[0].season, last = tt.types[0].bySeason.at(-1).season;
    // Rising first: biggest increase in flags per game vs the comparison
    const rows = tt.types.map(t => ({ ...t, base: t.compare[key], diff: (t.current ?? 0) - (t.compare[key] ?? 0) }))
        .sort((a, b) => b.diff - a.diff);
    const btn = c => c.key === 'sameWeeks' ? c.label.replace(' through Week ', ' thru Wk ') : c.label;
    box.innerHTML = `
        <div class="table-header tt-head">
            <div>
                <div class="table-title">Which calls are rising?</div>
                <div class="modal-actions block-actions">
                    <button class="modal-share" onclick="copyBlockLink('typeTrends', this)">Copy link</button>
                    <button class="modal-share" onclick="exportBlock('typeTrends', 'png', this)">Save PNG</button>
                    <button class="modal-share" onclick="exportBlock('typeTrends', 'pdf', this)">Save PDF</button>
                </div>
                <div class="tt-sub">${tt.season} accepted penalties per game vs ${comp.label.charAt(0).toLowerCase() + comp.label.slice(1)}, all teams · biggest increases first</div>
            </div>
            <div class="baseline-toggle tt-toggle" role="group" aria-label="Compare against">${tt.comparisons.map(c => `
                <button class="baseline-btn ${c.key === key ? 'active' : ''}" aria-pressed="${c.key === key}" onclick="setTypeTrendsCompare('${c.key}')">${btn(c)}</button>`).join('')}</div>
        </div>
        <div class="table-scroll">
            <table class="tt-table">
                <thead><tr><th>Penalty</th><th>${tt.season} / game</th><th>${comp.short} / game</th><th>Change</th><th>${first}–${String(last).slice(2)} trend</th></tr></thead>
                <tbody>${rows.map(r => `
                    <tr>
                        <td><strong>${r.type}</strong> <span class="modal-muted">${fmtNum(r.currentCount)} this season</span></td>
                        <td><strong>${fmtNum(r.current, 2)}</strong></td>
                        <td class="season-prev">${fmtNum(r.base, 2)}</td>
                        <td><span class="season-delta ${r.diff > 0.005 ? 'pct-up' : r.diff < -0.005 ? 'pct-down' : ''}">${r.diff > 0 ? '+' : ''}${fmtNum(r.diff, 2)}</span> ${pctBadge(r.current, r.base)}</td>
                        <td>${sparkline(r.bySeason)}</td>
                    </tr>`).join('')}
                </tbody>
            </table>
        </div>
        <p class="modal-footnote" style="padding: 0 1.25rem 1rem">${tt.notes} Trend line: each season ${first}–${last}, this season in yellow. ${tt.season} is ${tt.currentGames} games in, so rare penalties can swing.</p>`;
}

function toggleAllOpponents() {
    state.showAllOpponents = !state.showAllOpponents;
    setTeamBaseline(state.teamBaseline || teamBaselineKey(null));
}

// =============================================================================
// RENDERING - TEAMS (division -> team -> full profile)
// =============================================================================

function renderTeams() {
    const grid = document.getElementById('divisionGrid');
    if (!grid) return;
    const idx = state.teamsIndex;
    if (!idx?.divisions?.length) {
        grid.innerHTML = '<p class="season-error">Team data isn\'t available yet.</p>';
        return;
    }
    if (!state.selectedDivision) state.selectedDivision = idx.divisions[0].name;

    grid.innerHTML = idx.divisions.map(d => `
        <button class="division-tile ${d.name === state.selectedDivision ? 'active' : ''}" onclick="selectDivision('${d.name}')">
            <span class="division-name">${d.name}</span>
            <span class="division-logos">${d.teams.map(t =>
                `<img src="${t.logo}" alt="${t.abbr}" title="${t.name}" onerror="this.style.display='none'">`).join('')}</span>
        </button>`).join('');
    renderDivisionTeams();
}

function selectDivision(name) {
    state.selectedDivision = name;
    renderTeams();
    // On phones the team cards sit below the division tiles: bring them into view
    if (window.innerWidth < 700) {
        document.getElementById('divisionTeams')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function renderDivisionTeams() {
    const box = document.getElementById('divisionTeams');
    const idx = state.teamsIndex;
    const div = idx?.divisions?.find(d => d.name === state.selectedDivision);
    if (!box || !div) return;
    const league = idx.leaguePerGame;
    const bKey = teamBaselineKey(null);
    const bDef = (idx.baselines || []).find(b => b.key === bKey);
    // Most penalties per game first
    const teams = [...div.teams].sort((a, b) => (b.perGame ?? 0) - (a.perGame ?? 0));
    box.innerHTML = `
        <div class="division-head">
            <h3 class="preview-group-title">${div.name} <span class="modal-muted">${idx.season} · ranked by penalties per game</span></h3>
            ${idx.baselines?.length ? teamToggleHtml(idx.baselines, bKey, 'setTeamBaseline') : ''}
        </div>
        <div class="team-grid">${teams.map(t => `
            <div class="team-card" onclick="openTeamModal('${t.abbr}')">
                <div class="team-card-head">
                    <img src="${t.logo}" alt="" class="team-card-logo" onerror="this.style.display='none'">
                    <div>
                        <div class="team-card-name">${t.name}</div>
                        <div class="referee-meta">${t.record} · ${t.games} games</div>
                    </div>
                </div>
                <div class="pv-main">
                    <div>
                        <div class="pv-total">${fmtNum(t.perGame, 1)}</div>
                        <div class="pv-total-label">penalties/game · ${fmtNum(t.yardsPerGame)} yds</div>
                    </div>
                    <div class="pv-vs">${pctBadge(t.perGame, league, { small: t.games < MIN_GAMES_FOR_PCT })}<span>vs league avg ${fmtNum(league, 1)}</span></div>
                </div>
                <div class="cc-foot">
                    <span>Most-penalized rank <strong>${t.rank ? `#${t.rank}` : '—'}</strong></span>
                    <span>${bKey === 'sameWeeks' && t.throughWeek ? `${idx.season - 1} Wk 1–${t.throughWeek}` : (bDef ? bDef.short : 'Last season')} ${fmtNum(t.baselinePerGame?.[bKey] ?? t.lastSeasonPerGame, 1)}/g ${pctBadge(t.perGame, t.baselinePerGame?.[bKey] ?? t.lastSeasonPerGame, { small: t.games < MIN_GAMES_FOR_PCT })}</span>
                </div>
            </div>`).join('')}
        </div>`;
}

async function openTeamModal(abbr) {
    setDeepLink('team', abbr);
    const modal = document.getElementById('modal');
    const body = document.getElementById('modalBody');
    if (!modal || !body) return;
    modal.classList.add('active');
    body.removeAttribute('style');
    body.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    if (state.charts.modal) { state.charts.modal.destroy(); state.charts.modal = null; }

    const t = state.teamProfiles[abbr] || await fetchJSON(`teams/${abbr}.json`);
    if (!t) { body.innerHTML = '<p class="season-error">Team profile unavailable.</p>'; return; }
    state.teamProfiles[abbr] = t;
    renderTeamProfile(t);
}

// Which comparison the team views use (shared by the team cards and the team pop-up).
// Default: last season through the same week as now, which moves forward every week.
function teamBaselineKey(t) {
    const keys = t?.baselines ? Object.keys(t.baselines) : (state.teamsIndex?.baselines || []).map(b => b.key);
    if (state.teamBaseline && keys.includes(state.teamBaseline)) return state.teamBaseline;
    return t?.defaultBaseline || state.teamsIndex?.defaultBaseline || keys[0];
}

function teamToggleHtml(baselines, active, onclickFn) {
    const label = (b) => b.key === 'sameWeeks' ? b.label.replace(' through Week ', ' thru Wk ')
        : b.key === 'lastSeason' ? b.label : b.key === 'last3' ? 'Last 3 seasons' : 'All seasons';
    return `<div class="baseline-toggle team-toggle" role="group" aria-label="Compare against">${baselines.map(b => `
        <button class="baseline-btn ${b.key === active ? 'active' : ''}" aria-pressed="${b.key === active}"
                onclick="${onclickFn}('${b.key}')">${label(b)}</button>`).join('')}</div>`;
}

function setTeamBaseline(key) {
    state.teamBaseline = key;
    renderDivisionTeams();
    const open = document.getElementById('modal')?.classList.contains('active') && location.hash.startsWith('#team=');
    if (open) {
        const abbr = decodeURIComponent(location.hash.split('=')[1] || '');
        const scroller = document.querySelector('#modal .modal');
        const y = scroller?.scrollTop || 0;
        if (state.teamProfiles[abbr]) renderTeamProfile(state.teamProfiles[abbr]);
        if (scroller) scroller.scrollTop = y;
    }
}

function renderTeamProfile(t) {
    const body = document.getElementById('modalBody');
    if (state.charts.modal) { state.charts.modal.destroy(); state.charts.modal = null; }
    const cs = t.season, cur = t.current;
    // Selected comparison (falls back to all prior seasons for profiles built before baselines existed)
    const bKey = teamBaselineKey(t);
    const base = t.baselines?.[bKey] || { ...(t.allPrior || {}), short: 'Prior avg', label: 'All prior seasons' };
    const all = base;
    const ps = t.priorSeasons || [];
    const allLabel = base.short;
    const small = !cur || cur.games < MIN_GAMES_FOR_PCT;
    const withBase = (rows, field) => (rows || []).map(r => ({ ...r, priorPerGame: base[field]?.[r.type] ?? r.priorPerGame }))
        .sort((a, b) => (b.currentPerGame ?? 0) - (a.currentPerGame ?? 0) || (b.priorPerGame ?? 0) - (a.priorPerGame ?? 0));
    const committedRows = t.baselines ? withBase(t.committedTypes, 'types') : t.committedTypes;
    const drawnRows = t.baselines ? withBase(t.drawnTypes, 'drawnTypes') : t.drawnTypes;
    const quarterRows = (t.quarters || []).map((q, i) => ({ ...q, priorPerGame: base.quarters?.[i] ?? q.priorPerGame }));
    const toggle = t.baselines ? teamToggleHtml(Object.entries(t.baselines).map(([key, b]) => ({ key, ...b })), bKey, 'setTeamBaseline') : '';

    // Next game (links to its preview when one exists)
    const nextPv = t.nextGame && (state.previews || []).some(w => w.games?.some(g => g.gameId === t.nextGame.gameId));
    const nextTxt = t.nextGame
        ? `Next: ${t.nextGame.home ? 'vs' : '@'} ${t.nextGame.opponent}, Wk ${t.nextGame.week}` : '';
    document.getElementById('modalTitle').innerHTML =
        `<span class="team-title"><img src="${t.logo}" alt="" onerror="this.style.display='none'">${t.name}</span>`;
    document.getElementById('modalSubtitle').textContent =
        `${t.division || ''} · ${cs} record ${t.record}${nextTxt ? ` · ${nextTxt}` : ''}`;

    // Rows: this season vs last vs all prior
    const maxRate = Math.max(...[cur, base].filter(b => b && b.perGame != null).map(b => b.perGame), 1);
    const row = (cls, label, b) => b ? `
        <div class="cc-row ${cls}">
            <div class="cc-label">${label}<span>${b.games} g</span></div>
            <div class="cc-bar-track"><div class="cc-bar" style="width:${Math.max(2, b.perGame / maxRate * 100)}%"></div></div>
            <div class="cc-value">${fmtNum(b.perGame, 1)}</div>
            <div class="cc-yards">${fmtNum(b.yardsPerGame)} yds</div>
            <div class="cc-yards">${fmtNum(b.drawnPerGame, 1)}</div>
        </div>` : `
        <div class="cc-row ${cls} cc-empty"><div class="cc-label">${label}</div><div class="cc-bar-track"></div>
            <div class="cc-value">—</div><div class="cc-yards">—</div><div class="cc-yards">—</div></div>`;

    const tile = (label, value, sub) => `
        <div class="season-stat"><div class="season-stat-label">${label}</div>
        <div class="season-stat-value">${value}</div><div class="season-stat-compare">${sub}</div></div>`;
    const net = cur?.netPerGame;

    const crews = (t.crews || []).map(c => `
        <tr onclick="openRefereeModal('${c.slug}')">
            <td><strong>${c.name}</strong></td><td>${c.games}</td>
            <td>${fmtNum(c.perGame, 1)} ${pctBadge(c.perGame, all?.perGame ?? cur?.perGame, { small: c.games < 4 })}</td>
            <td class="season-prev">${fmtNum(c.opponentPerGame, 1)}</td>
            <td class="season-prev">${c.lastSeason}</td>
        </tr>`).join('');

    // Every opponent faced in the data, most flags on this team per game first
    const opp = t.opponents || [];
    const oppShown = state.showAllOpponents ? opp : opp.slice(0, 10);
    const opponentsHtml = opp.length ? `<div class="modal-section">
        <h4>By opponent <span class="modal-muted">(${ps[0] ?? cs}–${cs}, every regular-season meeting)</span></h4>
        <div class="table-scroll"><table class="pv-table">
            <thead><tr><th>Opponent</th><th>Games</th><th>${t.abbr} flags/g</th><th>Opp flags/g</th><th>Net</th><th>Last met</th></tr></thead>
            <tbody>${oppShown.map(o => `
                <tr onclick="openTeamModal('${o.opponent}')">
                    <td><strong>${o.opponent}</strong> <span class="modal-muted">${o.seasons.length > 1 ? `${o.seasons[0]}–${String(o.seasons.at(-1)).slice(2)}` : o.seasons[0]}</span></td>
                    <td>${o.games}</td>
                    <td><strong>${fmtNum(o.flagsPerGame, 1)}</strong> <span class="modal-muted">${o.totalFlags} total</span></td>
                    <td class="season-prev">${fmtNum(o.oppFlagsPerGame, 1)}</td>
                    <td><span class="season-delta ${o.netPerGame > 0 ? 'pct-down' : o.netPerGame < 0 ? 'pct-up' : ''}">${o.netPerGame > 0 ? '+' : ''}${fmtNum(o.netPerGame, 1)}</span></td>
                    <td class="season-prev">${o.lastMet.season} Wk ${o.lastMet.week} · ${o.lastMet.home ? 'home' : 'away'}${o.lastMet.result ? ` · ${o.lastMet.result} ${o.lastMet.score}` : ''} · ${o.lastMet.flags}–${o.lastMet.oppFlags} flags</td>
                </tr>`).join('')}
            </tbody></table></div>
        ${opp.length > 10 ? `<button class="info-trigger-inline opp-more" onclick="toggleAllOpponents()">${state.showAllOpponents ? 'Show top 10' : `Show all ${opp.length} opponents`}</button>` : ''}
        <p class="modal-footnote">Sorted by flags on ${t.abbr} per game, most first. Net = opponent's flags minus ${t.abbr}'s per game (<span class="pct-down">green</span>: ${t.abbr} came out ahead). Few meetings = small samples.</p>
    </div>` : '';

    const log = (t.games || []).map(g => `
        <tr ${g.gameId ? '' : ''}>
            <td>Wk ${g.week}</td>
            <td>${g.home ? 'vs' : '@'} ${g.opponent}</td>
            <td>${g.result ? `<span class="team-result team-result-${g.result}">${g.result}</span> ${g.score}` : '—'}</td>
            <td><strong>${g.flags}</strong> <span class="modal-muted">${g.yards} yds</span></td>
            <td class="season-prev">${g.opponentFlags}</td>
            <td class="season-prev">${g.crew || '—'}</td>
        </tr>`).join('');

    body.innerHTML = `
        ${nextPv ? `<div class="team-next"><button class="baseline-btn active" onclick="openPreviewModal('${t.nextGame.gameId}')">Preview next game: ${t.nextGame.home ? 'vs' : '@'} ${t.nextGame.opponent} →</button></div>` : ''}

        ${toggle ? `<div class="modal-section team-toggle-wrap">${toggle}
            <p class="modal-footnote">Comparing ${cs} with <strong>${base.label}</strong>. Every comparison below follows this choice.</p></div>` : ''}

        <div class="modal-section">
            <h4>${cs} vs ${base.label.charAt(0).toLowerCase() + base.label.slice(1)}</h4>
            <div class="cc-rows cc-rows-lg">
                <div class="cc-row-head"><span></span><span></span><span>Pen/g</span><span>Yds/g</span><span>Drawn/g</span></div>
                ${row('cc-current', cs, cur)}
                ${row('cc-last', allLabel, base.games ? base : null)}
            </div>
            ${cur ? `<div class="cc-changes">
                <span>Pen/g ${pctBadge(cur.perGame, base?.perGame, { small })}</span>
                <span>Yds/g ${pctBadge(cur.yardsPerGame, base?.yardsPerGame, { small })}</span>
                <span>Drawn/g ${pctBadge(cur.drawnPerGame, base?.drawnPerGame, { small })}</span>
                <span class="modal-muted">vs ${allLabel}</span>
            </div>` : ''}
            ${small && cur ? `<div class="cc-note">Only ${cur.games} games this season — early numbers swing a lot.</div>` : ''}
        </div>

        ${cur ? `<div class="modal-section">
            <div class="season-league team-tiles">
                ${tile('Most-penalized rank', t.rank.current ? `#${t.rank.current}` : '—', `of ${t.rank.of} · last season ${t.rank.lastSeason ? `#${t.rank.lastSeason}` : '—'}`)}
                ${tile('Offense / Defense', `${fmtNum(cur.offensePerGame, 1)} / ${fmtNum(cur.defensePerGame, 1)}`, 'flags per game on each side')}
                ${tile('Home / Away', `${fmtNum(cur.homePerGame, 1)} / ${fmtNum(cur.awayPerGame, 1)}`, 'flags per game')}
                ${tile('Flag margin', `${net > 0 ? '+' : ''}${fmtNum(net, 1)}`, net > 0 ? 'drew more than committed per game' : net < 0 ? 'committed more than drew per game' : 'even')}
            </div>
        </div>` : ''}

        <div class="chart-container modal-section">
            <div class="chart-title">Penalties per game by season <span class="modal-muted">(regular season)</span></div>
            <div class="chart-wrapper" style="height: 200px;"><canvas id="modalSeasonChart"></canvas></div>
        </div>

        ${t.committedTypes?.length ? `<div class="modal-section">
            <h4>What they get flagged for: ${cs} vs ${allLabel}</h4>
            ${pairLegend(cs, allLabel)}
            ${renderPairedRows(committedRows, cs, allLabel, small, r => r.type.replace('Offensive ', 'Off. ').replace('Defensive ', 'Def. '))}
        </div>` : ''}

        ${t.drawnTypes?.length ? `<div class="modal-section">
            <h4>What they draw from opponents</h4>
            ${pairLegend(cs, allLabel)}
            ${renderPairedRows(drawnRows, cs, allLabel, small, r => r.type.replace('Offensive ', 'Off. ').replace('Defensive ', 'Def. '))}
        </div>` : ''}

        <div class="modal-section">
            <h4>⏱️ When they get flagged</h4>
            ${pairLegend(cs, allLabel)}
            ${renderPairedRows(quarterRows, cs, allLabel, small, q => `Q${q.quarter}`)}
        </div>

        ${crews ? `<div class="modal-section">
            <h4>Flags on ${t.abbr} by crew chief <span class="modal-muted">(${ps[0] ?? cs}–${cs}, 2+ games)</span></h4>
            <div class="table-scroll"><table class="pv-table">
                <thead><tr><th>Crew chief</th><th>Games</th><th>${t.abbr} flags/g</th><th>Opp flags/g</th><th>Last worked</th></tr></thead>
                <tbody>${crews}</tbody>
            </table></div>
            <p class="modal-footnote">Sorted by flags on ${t.abbr} per game, most first. Badge compares with ${t.abbr}'s rate in ${base.label.charAt(0).toLowerCase() + base.label.slice(1)}.</p>
        </div>` : ''}

        ${t.players?.length ? `<div class="modal-section">
            <h4>Watchlist (${cs})</h4>
            <div class="pv-team-col">${t.players.map(w => `
                <div class="pv-watch-row"><span>${w.player}</span><span>${w.count} flag${w.count === 1 ? "" : "s"} · ${w.yards} yds</span>
                <span class="modal-muted">${w.types.map(x => `${x.type}${x.count > 1 ? ` ×${x.count}` : ''}`).join(', ')}</span></div>`).join('')}
            </div>
        </div>` : ''}

        ${opponentsHtml}

        ${log ? `<div class="modal-section">
            <h4>${cs} game log</h4>
            <div class="table-scroll"><table class="pv-table">
                <thead><tr><th>Week</th><th>Opponent</th><th>Result</th><th>${t.abbr} flags</th><th>Opp flags</th><th>Crew</th></tr></thead>
                <tbody>${log}</tbody>
            </table></div>
        </div>` : ''}
    `;
    setTimeout(() => renderTeamChart(t, all), 100);
}

function renderTeamChart(t, priorAll) {
    const ctx = document.getElementById('modalSeasonChart')?.getContext('2d');
    if (!ctx || !t.history?.length) return;
    if (state.charts.modal) state.charts.modal.destroy();
    const h = t.history;
    const datasets = [{
        type: 'bar', label: 'Penalties/game', data: h.map(s => s.perGame),
        backgroundColor: h.map(s => s.season === t.season ? CONFIG.chartColors.current : CONFIG.chartColors.hist),
        borderRadius: 4, order: 2
    }];
    if (priorAll) datasets.push({
        type: 'line', label: priorAll.short ? `${priorAll.short} rate` : 'Prior-years avg', data: h.map(() => priorAll.perGame),
        borderColor: 'rgba(255,255,255,0.45)', borderDash: [5, 5], borderWidth: 1.5, pointRadius: 0, order: 1
    });
    state.charts.modal = new Chart(ctx, {
        data: { labels: h.map(s => s.season), datasets },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { display: !!priorAll, position: 'top', align: 'end',
                          labels: { color: 'rgba(255,255,255,0.6)', boxWidth: 12, font: { size: 10 }, filter: (item) => item.text !== 'Penalties/game' } },
                tooltip: { callbacks: { label: (c) => {
                    if (c.dataset.type === 'line') return `${c.dataset.label}: ${fmtNum(c.raw, 1)}/g`;
                    const s = h[c.dataIndex];
                    return `${fmtNum(s.perGame, 1)}/g · ${fmtNum(s.yardsPerGame)} yds/g · rank #${s.rank ?? '—'} · ${s.games} games`;
                } } }
            },
            scales: {
                x: { grid: { display: false }, ticks: { color: 'rgba(255,255,255,0.6)' } },
                y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: 'rgba(255,255,255,0.5)' } }
            }
        }
    });
}

// =============================================================================
// RENDERING - REFEREE CARDS (with most common penalty)
// =============================================================================

function renderRefereeCards() {
    const container = document.getElementById('refereeGrid');
    if (!container) return;
    
    if (!state.referees.length) {
        container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
        return;
    }

    const d = state.season;
    const cs = d?.currentSeason;
    const lastKey = 'lastSeason', allKey = 'all';
    const lastBase = d?.baselines?.find(b => b.key === lastKey);
    const allBase = d?.baselines?.find(b => b.key === allKey);
    const allLabel = allBase
        ? `${allBase.seasons[0]}–${String(allBase.seasons[allBase.seasons.length - 1]).slice(2)}`
        : 'All';

    // Season numbers by slug (regular season only, from season_comparison.json)
    const bySlug = {};
    [...(d?.crewChiefs || []), ...(d?.inactiveCrewChiefs || [])].forEach(c => { bySlug[c.slug] = c; });

    // Active crews first, most penalties/game this season on down; then inactive by all-years rate
    const cards = state.referees.map(ref => ({ ref, cmp: bySlug[ref.slug] || null }));
    cards.sort((a, b) => {
        const ac = a.cmp?.current, bc = b.cmp?.current;
        if (ac && bc) return bc.perGame - ac.perGame;
        if (ac) return -1;
        if (bc) return 1;
        const aa = a.cmp?.baselines?.[allKey]?.perGame ?? a.ref.avg_per_game;
        const ba = b.cmp?.baselines?.[allKey]?.perGame ?? b.ref.avg_per_game;
        return ba - aa;
    });

    // One shared scale so bar lengths are comparable across every card
    const allRates = cards.flatMap(({ cmp }) => [
        cmp?.current?.perGame, cmp?.baselines?.[lastKey]?.perGame, cmp?.baselines?.[allKey]?.perGame
    ]).filter(v => v != null);
    const maxRate = Math.max(...allRates, 1);

    const row = (cls, label, block) => {
        if (!block) {
            return `
                <div class="cc-row ${cls} cc-empty">
                    <div class="cc-label">${label}</div>
                    <div class="cc-bar-track"></div>
                    <div class="cc-value">—</div>
                    <div class="cc-yards">—</div>
                </div>`;
        }
        const width = Math.max(2, block.perGame / maxRate * 100);
        return `
            <div class="cc-row ${cls}">
                <div class="cc-label">${label}<span>${block.games} g</span></div>
                <div class="cc-bar-track"><div class="cc-bar" style="width:${width}%"></div></div>
                <div class="cc-value">${fmtNum(block.perGame, 1)}</div>
                <div class="cc-yards">${fmtNum(block.yardsPerGame)} yds</div>
            </div>`;
    };

    container.innerHTML = cards.map(({ ref, cmp }, index) => {
        const profile = state.refereeProfiles[ref.slug];
        const topPenalty = profile?.penaltyTypes?.[0];
        const topPenaltyDisplay = topPenalty 
            ? topPenalty.type.replace('Offensive ', '').replace('Defensive ', '').replace(' (Offense)', '')
            : null;

        const cur = cmp?.current || null;
        const last = cmp?.baselines?.[lastKey] || null;
        const all = cmp?.baselines?.[allKey] || null;
        const active = !!cur;
        const small = active && cur.games < MIN_GAMES_FOR_PCT;

        const bias = `<span class="${ref.home_bias_pct > 5 ? 'cell-high' : ref.home_bias_pct < 0 ? 'cell-low' : ''}">
                        ${ref.home_bias_pct > 0 ? '+' : ''}${ref.home_bias_pct}%</span>`;

        return `
            <div class="referee-card ${active ? '' : 'referee-card-inactive'}" onclick="openRefereeModal('${ref.slug}')" data-index="${index}">
                <div class="cc-head">
                    <div>
                        <div class="referee-name">${ref.name}</div>
                        <div class="referee-meta">${ref.first_season}–${ref.last_season} • ${ref.games} games</div>
                    </div>
                    <span class="cc-status ${active ? 'cc-status-active' : ''}">${active ? `Active ${cs}` : `Not active in ${cs ?? 'current season'}`}</span>
                </div>

                ${cmp ? `
                <div class="cc-rows">
                    <div class="cc-row-head">
                        <span></span><span></span><span>Pen/g</span><span>Yds/g</span>
                    </div>
                    ${row('cc-current', cs ?? 'This season', cur)}
                    ${row('cc-last', lastBase ? lastBase.seasons[0] : 'Last season', last)}
                    ${row('cc-all', allLabel, all)}
                </div>

                ${active ? `
                <div class="cc-changes">
                    <span>vs ${lastBase?.seasons[0] ?? 'last season'} ${pctBadge(cur.perGame, last?.perGame, { small })}</span>
                    <span>vs ${allLabel} ${pctBadge(cur.perGame, all?.perGame, { small })}</span>
                </div>
                ${small ? `<div class="cc-note">Only ${cur.games} games this season — early numbers swing a lot.</div>` : ''}
                ` : ''}
                ` : `
                <div class="referee-stats">
                    <div class="referee-stat">
                        <div class="referee-stat-value">${ref.avg_per_game}</div>
                        <div class="referee-stat-label">Avg/Game</div>
                    </div>
                </div>`}

                <div class="cc-foot">
                    ${topPenaltyDisplay ? `<span>Most common: <strong>${topPenaltyDisplay}</strong></span>` : '<span></span>'}
                    <span>Home bias ${bias}</span>
                </div>
            </div>
        `;
    }).join('');
}

// =============================================================================
// RENDERING - CHARTS
// =============================================================================

function renderCharts() {
    if (!state.trends) return;
    
    renderSeasonTrendChart();
    renderPenaltyTypeChart();
    renderPenaltiesByRefChart();  // Changed from home bias to penalties by ref
    renderQuarterChart();
}

function renderSeasonTrendChart() {
    renderWeekChart();
    const ctx = document.getElementById('seasonChart')?.getContext('2d');
    if (!ctx || !state.trends.bySeason) return;
    
    if (state.charts.season) state.charts.season.destroy();
    
    state.charts.season = new Chart(ctx, {
        type: 'line',
        data: {
            labels: state.trends.bySeason.map(s => s.season),
            datasets: [{
                label: 'Avg Penalties/Game',
                data: state.trends.bySeason.map(s => s.avg_per_game),
                borderColor: CONFIG.chartColors.flag,
                backgroundColor: 'rgba(255, 196, 0, 0.08)',
                fill: true,
                tension: 0.4,
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: 'rgba(255,255,255,0.5)' } },
                y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: 'rgba(255,255,255,0.5)' } }
            }
        }
    });
}

function renderPenaltyTypeChart() {
    const ctx = document.getElementById('typeChart')?.getContext('2d');
    if (!ctx || !state.trends.byType) return;
    
    if (state.charts.type) state.charts.type.destroy();
    
    const colors = CONFIG.chartColors.categorical;
    
    state.charts.type = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: state.trends.byType.map(t => t.type),
            datasets: [{
                data: state.trends.byType.map(t => t.count),
                backgroundColor: colors,
                borderColor: '#16181b',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { color: 'rgba(255,255,255,0.7)', padding: 10, font: { size: 10 } }
                }
            }
        }
    });
}

// CHANGED: Now shows penalties by ref (sorted descending) instead of home bias
function renderPenaltiesByRefChart() {
    const ctx = document.getElementById('biasChart')?.getContext('2d');
    if (!ctx || !state.referees.length) return;
    
    if (state.charts.bias) state.charts.bias.destroy();
    
    // Sort referees by avg penalties descending
    const sortedRefs = [...state.referees].sort((a, b) => b.avg_per_game - a.avg_per_game);
    const topRefs = sortedRefs.slice(0, 12);
    
    // Calculate league average
    const leagueAvg = state.referees.reduce((sum, r) => sum + r.avg_per_game, 0) / state.referees.length;
    
    state.charts.bias = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: topRefs.map(r => r.name.split(' ').pop()),
            datasets: [{
                label: 'Avg Penalties/Game',
                data: topRefs.map(r => r.avg_per_game),
                backgroundColor: topRefs.map(r => 
                    r.avg_per_game > leagueAvg + 1 ? CONFIG.chartColors.red :
                    r.avg_per_game < leagueAvg - 1 ? CONFIG.chartColors.green :
                    CONFIG.chartColors.slate
                ),
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: { 
                legend: { display: false },
                annotation: {
                    annotations: {
                        line1: {
                            type: 'line',
                            xMin: leagueAvg,
                            xMax: leagueAvg,
                            borderColor: 'rgba(255,255,255,0.3)',
                            borderWidth: 2,
                            borderDash: [5, 5]
                        }
                    }
                }
            },
            scales: {
                x: { 
                    grid: { color: 'rgba(255,255,255,0.05)' }, 
                    ticks: { color: 'rgba(255,255,255,0.5)' },
                    title: { display: true, text: 'Avg Penalties/Game', color: 'rgba(255,255,255,0.5)' }
                },
                y: { grid: { display: false }, ticks: { color: 'rgba(255,255,255,0.7)' } }
            }
        }
    });
}

// FIXED: Now shows actual counts, not percentages (which made equal height bars)
function renderQuarterChart() {
    const ctx = document.getElementById('quarterChart')?.getContext('2d');
    if (!ctx) return;
    
    if (state.charts.quarter) state.charts.quarter.destroy();
    
    // Check for enhanced quarter-by-type data
    const qtrTypeData = state.trends.byQuarterAndType;
    const byQuarter = state.trends.byQuarter;
    
    if (qtrTypeData && qtrTypeData.types && byQuarter) {
        // Get actual counts per quarter for scaling
        const quarterTotals = {};
        byQuarter.forEach(q => { quarterTotals[q.quarter] = q.count; });
        
        const colors = CONFIG.chartColors.categorical;
        
        // Convert percentages back to approximate counts for each type per quarter
        const datasets = qtrTypeData.types.map((type, i) => {
            const percentages = qtrTypeData.data[type] || [0, 0, 0, 0];
            const counts = percentages.map((pct, qIdx) => {
                const qtrTotal = quarterTotals[qIdx + 1] || 0;
                return Math.round(qtrTotal * pct / 100);
            });
            
            return {
                label: type.replace('Offensive ', 'Off ').replace('Defensive ', 'Def '),
                data: counts,
                backgroundColor: colors[i % colors.length],
                borderColor: '#16181b',
                borderWidth: 1,
                borderRadius: 2
            };
        });
        
        state.charts.quarter = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Q1', 'Q2', 'Q3', 'Q4'],
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { color: 'rgba(255,255,255,0.7)', font: { size: 9 }, boxWidth: 10 }
                    }
                },
                scales: {
                    x: { stacked: true, grid: { display: false }, ticks: { color: 'rgba(255,255,255,0.7)' } },
                    y: { 
                        stacked: true, 
                        grid: { color: 'rgba(255,255,255,0.05)' }, 
                        ticks: { color: 'rgba(255,255,255,0.5)' },
                        title: { display: true, text: 'Penalty Count', color: 'rgba(255,255,255,0.5)' }
                    }
                }
            }
        });
    } else if (byQuarter) {
        // Fallback to simple quarter totals
        state.charts.quarter = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: byQuarter.map(q => `Q${q.quarter}`),
                datasets: [{
                    label: 'Penalties',
                    data: byQuarter.map(q => q.count),
                    backgroundColor: CONFIG.chartColors.categorical.slice(0, 4),
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false }, ticks: { color: 'rgba(255,255,255,0.7)' } },
                    y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: 'rgba(255,255,255,0.5)' } }
                }
            }
        });
    }
}

// =============================================================================
// RENDERING - DATA TABLE
// =============================================================================

function renderDataTable() {
    const container = document.getElementById('dataTable');
    if (!container || !state.referees.length) return;
    
    const tbody = container.querySelector('tbody');
    if (!tbody) return;
    
    tbody.innerHTML = state.referees.map(ref => `
        <tr onclick="openRefereeModal('${ref.slug}')">
            <td><strong>${ref.name}</strong></td>
            <td>${ref.games}</td>
            <td>${ref.avg_per_game}</td>
            <td>${ref.min_penalties}-${ref.max_penalties}</td>
            <td class="${ref.home_bias_pct > 5 ? 'cell-high' : ref.home_bias_pct < 0 ? 'cell-low' : ''}">
                ${ref.home_bias_pct > 0 ? '+' : ''}${ref.home_bias_pct}%
            </td>
            <td>${ref.consistency}</td>
        </tr>
    `).join('');
}

// =============================================================================
// MODAL - REFEREE PROFILE (with penalty types breakdown)
// =============================================================================

async function openRefereeModal(slug) {
    setDeepLink('crew', slug);
    const modal = document.getElementById('modal');
    const modalBody = document.getElementById('modalBody');
    
    if (!modal || !modalBody) return;
    
    modal.classList.add('active');
    modalBody.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    
    const profile = await loadRefereeProfile(slug);
    
    if (!profile) {
        modalBody.innerHTML = '<p style="text-align:center;color:var(--text-muted);">Error loading profile. Data may not be available yet.</p>';
        return;
    }
    
    state.currentReferee = profile;

    const d = state.season;
    const cs = profile.currentSeason ?? d?.currentSeason;
    const cmp = [...(d?.crewChiefs || []), ...(d?.inactiveCrewChiefs || [])].find(c => c.slug === slug) || null;
    const cur = cmp?.current || null;
    const last = cmp?.baselines?.lastSeason || null;
    const all = cmp?.baselines?.all || null;
    const allBase = d?.baselines?.find(b => b.key === 'all');
    const allLabel = allBase
        ? `${allBase.seasons[0]}–${String(allBase.seasons[allBase.seasons.length - 1]).slice(2)}`
        : 'Prior years';
    const lastLabel = d?.baselines?.find(b => b.key === 'lastSeason')?.seasons[0] ?? 'Last season';
    const active = !!cur;
    const small = active && cur.games < MIN_GAMES_FOR_PCT;

    document.getElementById('modalTitle').textContent = profile.name;
    document.getElementById('modalSubtitle').textContent = active
        ? `Active ${cs} • ${cur.games} games this season • ${profile.stats.games} career games`
        : `Not active in ${cs} • ${profile.experience} • ${profile.stats.games} career games`;

    // --- This season vs history (same rows as the card, bigger) ---
    const maxRate = Math.max(...[cur, last, all].filter(Boolean).map(b => b.perGame), 1);
    const row = (cls, label, block) => block ? `
        <div class="cc-row ${cls}">
            <div class="cc-label">${label}<span>${block.games} g</span></div>
            <div class="cc-bar-track"><div class="cc-bar" style="width:${Math.max(2, block.perGame / maxRate * 100)}%"></div></div>
            <div class="cc-value">${fmtNum(block.perGame, 1)}</div>
            <div class="cc-yards">${fmtNum(block.yardsPerGame)} yds</div>
            <div class="cc-yards">${fmtNum(block.yardsPerPenalty, 1)}</div>
        </div>` : `
        <div class="cc-row ${cls} cc-empty">
            <div class="cc-label">${label}</div>
            <div class="cc-bar-track"></div>
            <div class="cc-value">—</div><div class="cc-yards">—</div><div class="cc-yards">—</div>
        </div>`;

    const leagueCur = d?.league?.current;
    const vsLeaguePct = active && leagueCur ? pctChange(cur.perGame, leagueCur.perGame) : null;
    const seasonTendency = active && leagueCur ? `
        In ${cs}, ${profile.name.split(' ').pop()}'s crew is calling <strong>${fmtNum(cur.perGame, 1)}</strong> penalties per game
        vs a league average of <strong>${fmtNum(leagueCur.perGame, 1)}</strong>
        ${pctBadge(cur.perGame, leagueCur.perGame, { small })}
        ${vsLeaguePct === null ? '' : Math.abs(vsLeaguePct) < 5 ? '— right at league pace.'
            : vsLeaguePct > 0 ? '— one of the more flag-heavy crews this season.' : '— letting them play more than most this season.'}
        ${small ? `<br><span class="cc-note">Only ${cur.games} games so far, so this can still move a lot.</span>` : ''}` : '';

    const comparisonHtml = cmp ? `
        <div class="modal-section">
            <h4>${active ? `${cs} vs history` : 'Regular-season history'}</h4>
            <div class="cc-rows cc-rows-lg">
                <div class="cc-row-head"><span></span><span></span><span>Pen/g</span><span>Yds/g</span><span>Yds/pen</span></div>
                ${row('cc-current', cs, cur)}
                ${row('cc-last', lastLabel, last)}
                ${row('cc-all', allLabel, all)}
            </div>
            ${active ? `
            <div class="cc-changes">
                <span>Pen/g vs ${lastLabel} ${pctBadge(cur.perGame, last?.perGame, { small })}</span>
                <span>vs ${allLabel} ${pctBadge(cur.perGame, all?.perGame, { small })}</span>
                <span>Yds/g vs ${lastLabel} ${pctBadge(cur.yardsPerGame, last?.yardsPerGame, { small })}</span>
                <span>vs ${allLabel} ${pctBadge(cur.yardsPerGame, all?.yardsPerGame, { small })}</span>
            </div>` : ''}
        </div>` : '';

    // --- Penalty types & quarters: this season vs prior years, per game ---
    const typesHtml = active && profile.penaltyTypeComparison?.length
        ? renderTypeComparison(profile.penaltyTypeComparison, cs, allLabel, small)
        : renderPenaltyTypesBreakdown(profile.penaltyTypes);
    const quartersHtml = active && profile.quarterComparison?.length
        ? renderQuarterComparison(profile.quarterComparison, cs, allLabel, small)
        : renderQuarterDistribution(profile.quarterDistribution);

    modalBody.innerHTML = `
        ${comparisonHtml}

        ${active ? `
        <div class="modal-tendency">
            <h4>${cs} so far</h4>
            <p>${seasonTendency}</p>
            <p class="modal-tendency-career"><strong>Career:</strong> ${profile.tendencies?.description || 'League-average officiating style'}</p>
        </div>` : `
        <div class="modal-tendency">
            <h4>Tendencies</h4>
            <p>${profile.tendencies?.description || 'League-average officiating style'}</p>
        </div>`}

        <div class="chart-container modal-section">
            <div class="chart-title">Penalties per game by season <span class="modal-muted">(regular season)</span></div>
            <div class="chart-wrapper" style="height: 200px;">
                <canvas id="modalSeasonChart"></canvas>
            </div>
        </div>

        ${typesHtml}

        ${quartersHtml}

        <div class="modal-section">
            <h4>Career (all games incl. playoffs, ${profile.firstSeason}–${profile.lastSeason})</h4>
            <div class="modal-stats-grid">
                <div class="modal-stat">
                    <div class="modal-stat-value">${profile.stats.avgPerGame}</div>
                    <div class="modal-stat-label">Avg/Game</div>
                </div>
                <div class="modal-stat">
                    <div class="modal-stat-value">${profile.stats.minGame}-${profile.stats.maxGame}</div>
                    <div class="modal-stat-label">Range</div>
                </div>
                <div class="modal-stat">
                    <div class="modal-stat-value">${profile.stats.homeBiasPct > 0 ? '+' : ''}${profile.stats.homeBiasPct}%</div>
                    <div class="modal-stat-label">Home Bias</div>
                </div>
                <div class="modal-stat">
                    <div class="modal-stat-value">${profile.stats.consistency}</div>
                    <div class="modal-stat-label">Style</div>
                </div>
            </div>
        </div>

        <div>
            <h4 style="margin-bottom: 0.75rem;">Recent Games</h4>
            <div class="game-list">
                ${renderRecentGames(profile.recentGames, cs)}
            </div>
        </div>
    `;
    
    setTimeout(() => renderModalChart(profile, all), 100);
}

// Paired bars: this season (cyan) vs prior years (gray), per game, shared scale
function renderPairedRows(rows, cs, allLabel, small, labelFn) {
    const max = Math.max(...rows.flatMap(r => [r.currentPerGame || 0, r.priorPerGame || 0]), 0.1);
    return rows.map(r => `
        <div class="pair-row">
            <div class="pair-label">${labelFn(r)}</div>
            <div class="pair-bars">
                <div class="pair-bar-track"><div class="pair-bar pair-current" style="width:${(r.currentPerGame || 0) / max * 100}%"></div></div>
                <div class="pair-bar-track"><div class="pair-bar pair-prior" style="width:${(r.priorPerGame || 0) / max * 100}%"></div></div>
            </div>
            <div class="pair-values">
                <span class="pair-cur">${fmtNum(r.currentPerGame, 1)}</span>
                <span class="pair-prior-val">${fmtNum(r.priorPerGame, 1)}</span>
            </div>
            <div class="pair-pct">${pctBadge(r.currentPerGame, r.priorPerGame, { small })}</div>
        </div>
    `).join('');
}

function pairLegend(cs, allLabel) {
    return `<div class="pair-legend">
        <span><i class="pair-swatch pair-current"></i>${cs}</span>
        <span><i class="pair-swatch pair-prior"></i>${/avg$/.test(allLabel) ? allLabel : `${allLabel} avg`}</span>
        <span class="modal-muted">per game</span>
    </div>`;
}

function renderTypeComparison(types, cs, allLabel, small) {
    const rows = types.slice(0, 10);
    return `
        <div class="modal-section">
            <h4>What's being called: ${cs} vs ${allLabel}</h4>
            ${pairLegend(cs, allLabel)}
            ${renderPairedRows(rows, cs, allLabel, small, r => r.type.replace('Offensive ', 'Off. ').replace('Defensive ', 'Def. '))}
            <p class="modal-footnote">Penalties per game of each type in this crew's regular-season games. Sorted by ${cs} rate, most first.</p>
        </div>`;
}

function renderQuarterComparison(quarters, cs, allLabel, small) {
    return `
        <div class="modal-section">
            <h4>⏱️ When flags fly: ${cs} vs ${allLabel}</h4>
            ${pairLegend(cs, allLabel)}
            ${renderPairedRows(quarters, cs, allLabel, small, q => `Q${q.quarter}`)}
        </div>`;
}

function renderPenaltyTypesBreakdown(penaltyTypes) {
    if (!penaltyTypes || !penaltyTypes.length) {
        return '';
    }
    
    const maxPct = Math.max(...penaltyTypes.map(p => p.pct));
    
    return `
        <div style="margin-bottom: 1.5rem;">
            <h4 style="margin-bottom: 0.75rem;">Penalty Type Breakdown</h4>
            <div class="penalty-types-list">
                ${penaltyTypes.slice(0, 8).map(p => `
                    <div class="penalty-type-item">
                        <div class="penalty-type-header">
                            <span class="penalty-type-name">${p.type}</span>
                            <span class="penalty-type-pct">${p.pct}%</span>
                        </div>
                        <div class="penalty-type-bar-bg">
                            <div class="penalty-type-bar" style="width: ${(p.pct / maxPct) * 100}%"></div>
                        </div>
                    </div>
                `).join('')}
            </div>
            <p style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.5rem;">
                Percentage of all penalties in games this referee works
            </p>
        </div>
    `;
}

function renderQuarterDistribution(quarterDist) {
    if (!quarterDist || !quarterDist.length) {
        return '';
    }
    
    const maxPct = Math.max(...quarterDist.map(q => q.pct));
    
    return `
        <div style="margin-bottom: 1.5rem;">
            <h4 style="margin-bottom: 0.75rem;">⏱️ Penalties By Quarter</h4>
            <div class="quarter-dist-grid">
                ${quarterDist.map(q => `
                    <div class="quarter-dist-item">
                        <div class="quarter-label">Q${q.quarter}</div>
                        <div class="quarter-bar-container">
                            <div class="quarter-bar" style="height: ${(q.pct / maxPct) * 100}%"></div>
                        </div>
                        <div class="quarter-pct">${q.pct}%</div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

function renderRecentGames(games, currentSeason) {
    if (!games || !games.length) {
        return '<p style="color: var(--text-muted);">No recent games available.</p>';
    }
    
    return games.slice(0, 10).map(g => `
        <div class="game-item ${g.season === currentSeason ? 'game-item-current' : ''}">
            <div class="game-teams">
                ${g.awayTeam?.logo ? `<img src="${g.awayTeam.logo}" alt="${g.awayTeam.abbr}" class="team-logo" onerror="this.style.display='none'">` : ''}
                <span>${g.awayTeam?.abbr || g.away || '?'}</span>
                <span class="game-vs">@</span>
                <span>${g.homeTeam?.abbr || g.home || '?'}</span>
                ${g.homeTeam?.logo ? `<img src="${g.homeTeam.logo}" alt="${g.homeTeam.abbr}" class="team-logo" onerror="this.style.display='none'">` : ''}
            </div>
            <div class="game-info">
                ${g.awayScore !== null && g.homeScore !== null ? 
                    `<div class="game-score">${g.awayScore} - ${g.homeScore}</div>` : ''}
                <div class="game-date">${g.season === currentSeason ? `<span class="game-season-tag">${g.season} Wk ${g.week ?? '?'}</span> ` : ''}${g.date ? formatDate(g.date) : `Week ${g.week || '?'}, ${g.season}`}</div>
            </div>
            <div class="game-penalties">
                <div class="game-penalties-value">${g.penalties}</div>
                <div class="game-penalties-label">flags${g.yards != null ? ` · ${g.yards} yds` : ''}</div>
            </div>
        </div>
    `).join('');
}

function formatDate(dateStr) {
    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
        return dateStr;
    }
}

function renderModalChart(profile, priorAll) {
    const ctx = document.getElementById('modalSeasonChart')?.getContext('2d');
    if (!ctx) return;
    
    if (state.charts.modal) state.charts.modal.destroy();

    const reg = profile.regularSeasonStats?.length ? profile.regularSeasonStats : null;
    const seasons = reg || (profile.seasonStats || []).map(s => ({ season: s.season, perGame: s.avg, games: s.games }));
    if (!seasons.length) return;

    const cs = profile.currentSeason;
    const datasets = [{
        type: 'bar',
        label: 'Penalties/game',
        data: seasons.map(s => s.perGame),
        backgroundColor: seasons.map(s => s.season === cs ? CONFIG.chartColors.current : CONFIG.chartColors.hist),
        borderRadius: 4,
        order: 2
    }];
    if (priorAll) {
        datasets.push({
            type: 'line',
            label: 'Prior-years avg',
            data: seasons.map(() => priorAll.perGame),
            borderColor: 'rgba(255,255,255,0.45)',
            borderDash: [5, 5],
            borderWidth: 1.5,
            pointRadius: 0,
            order: 1
        });
    }
    
    state.charts.modal = new Chart(ctx, {
        data: { labels: seasons.map(s => s.season), datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: !!priorAll, position: 'top', align: 'end',
                          labels: { color: 'rgba(255,255,255,0.6)', boxWidth: 12, font: { size: 10 }, filter: (item) => item.text !== 'Penalties/game' } },
                tooltip: {
                    callbacks: {
                        label: (c) => {
                            if (c.dataset.type === 'line') return `Prior-years avg: ${fmtNum(c.raw, 1)}/g`;
                            const s = seasons[c.dataIndex];
                            return `${fmtNum(s.perGame, 1)}/g` +
                                   (s.yardsPerGame != null ? ` · ${fmtNum(s.yardsPerGame)} yds/g` : '') +
                                   ` · ${s.games} games`;
                        }
                    }
                }
            },
            scales: {
                x: { grid: { display: false }, ticks: { color: 'rgba(255,255,255,0.6)' } },
                y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: 'rgba(255,255,255,0.5)' } }
            }
        }
    });
}

function closeModal() {
    document.getElementById('modal')?.classList.remove('active');
    state.currentReferee = null;
    clearDeepLink();
}

// =============================================================================
// DEEP LINKS — every report has its own shareable address
//   #game=2026_05_TB_DAL   game preview (or, once played, the home team's profile)
//   #team=DAL              team profile
//   #crew=scott-novak      crew chief profile
//   #division=NFC East     teams section, that division selected
// Works alongside tracking parameters: /?utm_source=x#game=...
// =============================================================================

const DEEP_LINK_RE = /^#(game|team|crew|division|scorecard)=(.+)$/;

function setDeepLink(key, value) {
    const url = `${location.pathname}${location.search}#${key}=${encodeURIComponent(value)}`;
    history.replaceState(null, '', url);
}

function clearDeepLink() {
    if (DEEP_LINK_RE.test(location.hash)) {
        history.replaceState(null, '', `${location.pathname}${location.search}`);
    }
}

function handleDeepLink() {
    const m = location.hash.match(DEEP_LINK_RE);
    if (!m) return false;
    const key = m[1], value = decodeURIComponent(m[2]);

    if (key === 'game') {
        const inPreviews = (state.previews || []).some(w => w.games?.some(g => g.gameId === value));
        if (inPreviews) { openPreviewModal(value); return true; }
        // Already played: show the home team's profile (its game log has the result and flags)
        const home = value.split('_').pop();
        if (home) { openTeamModal(home); return true; }
    }
    if (key === 'team') { openTeamModal(value.toUpperCase()); return true; }
    if (key === 'scorecard') { openScorecardModal(); return true; }
    if (key === 'crew') { openRefereeModal(value); return true; }
    if (key === 'division') {
        const div = state.teamsIndex?.divisions?.find(d => d.name.toLowerCase() === value.toLowerCase());
        if (div) {
            document.getElementById('modal')?.classList.remove('active');
            selectDivision(div.name);
            document.getElementById('teams')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
            return true;
        }
    }
    return false;
}

// =============================================================================
// EXPORT — save any report pop-up as a full-length PNG or PDF
// Libraries load only when someone clicks Export (pinned versions on cdnjs).
// =============================================================================

const EXPORT_LIBS = {
    html2canvas: 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js',
    jspdf: 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js'
};
const _scriptPromises = {};

function loadScriptOnce(src) {
    if (!_scriptPromises[src]) {
        _scriptPromises[src] = new Promise((resolve, reject) => {
            const el = document.createElement('script');
            el.src = src;
            el.onload = resolve;
            el.onerror = () => { delete _scriptPromises[src]; reject(new Error('Could not load ' + src)); };
            document.head.appendChild(el);
        });
    }
    return _scriptPromises[src];
}

function exportFileName(ext) {
    const m = location.hash.match(DEEP_LINK_RE);
    const slug = m ? `${m[1]}-${decodeURIComponent(m[2])}` : (document.getElementById('modalTitle')?.textContent || 'report');
    const safe = slug.toLowerCase().replace(/[^a-z0-9_-]+/g, '-').replace(/^-+|-+$/g, '');
    return `nfl-observatory-${safe}.${ext}`;
}

// Export any on-page panel (e.g. "Which calls are rising?") as a branded PNG / PDF,
// same look as pop-up exports: buttons hidden, full width, footer with the link.
async function renderBlockCanvas(el) {
    await loadScriptOnce(EXPORT_LIBS.html2canvas);
    const id = el.id;
    return window.html2canvas(el, {
        // match the panel's own background so the export has no mismatched frame
        backgroundColor: (() => { const c = getComputedStyle(el).backgroundColor; return c && c !== 'rgba(0, 0, 0, 0)' ? c : '#16181b'; })(),
        scale: 2, useCORS: true, logging: false,
        windowWidth: Math.max(document.documentElement.clientWidth, 1100),
        onclone: (doc) => {
            const b = doc.getElementById(id);
            // boxShadow off: the export library draws inset shadows as a lighter frame
            Object.assign(b.style, { width: '1000px', maxWidth: '1000px', margin: '0', transform: 'none', opacity: '1', boxShadow: 'none' });
            b.querySelectorAll('.block-actions').forEach(x => { x.style.display = 'none'; });
            b.querySelectorAll('.baseline-toggle').forEach(x => {
                const active = x.querySelector('.baseline-btn.active');
                if (x.classList.contains('sb-toggle') && active) {          // scoreboard: show which timeframe
                    x.querySelectorAll('.baseline-btn:not(.active)').forEach(btn => { btn.style.display = 'none'; });
                } else {
                    x.style.display = 'none';
                }
            });
            b.querySelectorAll('.table-scroll').forEach(x => { x.style.overflow = 'visible'; });
            const foot = doc.createElement('div');
            foot.style.cssText = 'padding:16px 24px 22px;border-top:1px solid #262a2f;display:flex;justify-content:space-between;' +
                'align-items:center;font:500 14px Inter,system-ui,sans-serif;color:#9a9ea4';
            const when = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
            foot.innerHTML = `<span style="display:flex;align-items:center;gap:10px;color:#ecebe7;font-weight:600">` +
                `<span style="width:22px;height:22px;border-radius:5px;background:#16181b;border:1px solid #2a2d32;display:inline-flex;align-items:center;justify-content:center">` +
                `<span style="width:11px;height:11px;background:#ffc400;transform:rotate(-18deg);display:block;border-radius:1px"></span></span>` +
                `nflobservatory.com</span><span>${when} · ${location.host}/#${id}</span>`;
            b.appendChild(foot);
        }
    });
}

async function exportBlock(id, format, btn) {
    const el = document.getElementById(id);
    if (!el) return;
    const label = btn?.textContent;
    if (btn) { btn.disabled = true; btn.textContent = 'Preparing…'; }
    try {
        const canvas = await renderBlockCanvas(el);
        const title = (el.querySelector('.table-title, .sb-title')?.textContent.trim() || id) +
            (id === 'scoreboard' && state.scoreboard ? ` ${scoreboardFrame(state.scoreboard).f.label || ''}` : '');
        const name = `nfl-observatory-${title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')}.${format}`;
        if (format === 'png') {
            const blob = await new Promise(res => canvas.toBlob(res, 'image/png'));
            deliverPng(blob, name);
        } else {
            await loadScriptOnce(EXPORT_LIBS.jspdf);
            const { jsPDF } = window.jspdf;
            const w = canvas.width / 2, h = canvas.height / 2;
            const pdf = new jsPDF({ orientation: h > w ? 'portrait' : 'landscape', unit: 'px', format: [w, h], hotfixes: ['px_scaling'] });
            pdf.addImage(canvas.toDataURL('image/jpeg', 0.92), 'JPEG', 0, 0, w, h);
            pdf.setProperties({ title, creator: 'nflobservatory.com' });
            pdf.save(name);
        }
        if (btn) btn.textContent = 'Saved ✓';
    } catch (err) {
        console.error('Export failed:', err);
        if (btn) btn.textContent = 'Export failed';
    } finally {
        setTimeout(() => { if (btn) { btn.textContent = label; btn.disabled = false; } }, 1800);
    }
}

async function copyBlockLink(id, btn) {
    const url = `${location.origin}${location.pathname}#${id}`;
    const label = btn?.textContent;
    try {
        await navigator.clipboard.writeText(url);
        if (btn) btn.textContent = 'Copied ✓';
    } catch {
        if (btn) btn.textContent = url;
    }
    setTimeout(() => { if (btn) btn.textContent = label; }, 1800);
}

async function renderModalCanvas() {
    await loadScriptOnce(EXPORT_LIBS.html2canvas);
    const modal = document.querySelector('#modal .modal');
    const fullHeight = modal.scrollHeight;
    return window.html2canvas(modal, {
        backgroundColor: getComputedStyle(document.documentElement).getPropertyValue('--bg-secondary').trim() || '#121417',
        scale: 2,                       // sharp on retina screens and when zoomed
        useCORS: true,                 // team logos load cross-origin; skipped if the host doesn't allow it
        logging: false,
        windowWidth: Math.max(document.documentElement.clientWidth, 1000),
        windowHeight: fullHeight + 400,
        onclone: (doc) => {
            // Unroll the scrolling pop-up so the whole report is captured, not just what's on screen
            const overlay = doc.getElementById('modal');
            Object.assign(overlay.style, { position: 'absolute', inset: 'auto', top: '0', left: '0', height: 'auto',
                display: 'block', padding: '0', background: 'none', backdropFilter: 'none', overflow: 'visible' });
            const m = overlay.querySelector('.modal');
            Object.assign(m.style, { maxHeight: 'none', height: 'auto', overflow: 'visible', width: '900px', maxWidth: '900px' });
            const head = m.querySelector('.modal-header');
            if (head) head.style.position = 'static';
            m.querySelectorAll('.modal-actions, .modal-close, .info-trigger-small, .team-next').forEach(el => { el.style.display = 'none'; });
            // Branded footer with the report's address
            const foot = doc.createElement('div');
            foot.style.cssText = 'padding:18px 32px 26px;border-top:1px solid #262a2f;display:flex;justify-content:space-between;' +
                'align-items:center;font:500 14px Inter,system-ui,sans-serif;color:#9a9ea4';
            const when = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
            foot.innerHTML = `<span style="display:flex;align-items:center;gap:10px;color:#ecebe7;font-weight:600">` +
                `<span style="width:22px;height:22px;border-radius:5px;background:#16181b;border:1px solid #2a2d32;display:inline-flex;align-items:center;justify-content:center">` +
                `<span style="width:11px;height:11px;background:#ffc400;transform:rotate(-18deg);display:block;border-radius:1px"></span></span>` +
                `nflobservatory.com</span><span>${when} · ${location.host}${location.pathname}${location.hash}</span>`;
            m.appendChild(foot);
        }
    });
}

async function exportModal(format) {
    const btn = document.getElementById(format === 'pdf' ? 'modalExportPdf' : 'modalExportPng');
    const label = btn?.textContent;
    if (btn) { btn.disabled = true; btn.textContent = 'Preparing…'; }
    try {
        const canvas = await renderModalCanvas();
        if (format === 'png') {
            const blob = await new Promise(res => canvas.toBlob(res, 'image/png'));
            deliverPng(blob, exportFileName('png'));
        } else {
            await loadScriptOnce(EXPORT_LIBS.jspdf);
            const { jsPDF } = window.jspdf;
            // One continuous page sized to the report, so nothing is split mid-chart
            const w = canvas.width / 2, h = canvas.height / 2;
            const pdf = new jsPDF({ orientation: h > w ? 'portrait' : 'landscape', unit: 'px', format: [w, h], hotfixes: ['px_scaling'] });
            pdf.addImage(canvas.toDataURL('image/jpeg', 0.92), 'JPEG', 0, 0, w, h);
            pdf.setProperties({ title: document.getElementById('modalTitle')?.textContent || 'NFL Officiating Observatory',
                                subject: location.href, creator: 'nflobservatory.com' });
            pdf.save(exportFileName('pdf'));
        }
        if (btn) btn.textContent = 'Saved ✓';
    } catch (err) {
        console.error('Export failed:', err);
        if (btn) btn.textContent = 'Export failed';
    } finally {
        setTimeout(() => { if (btn) { btn.textContent = label; btn.disabled = false; } }, 1800);
    }
}

// =============================================================================
// CHART DOWNLOADS — every chart on the page gets PNG / PDF buttons
// The export is a branded card: chart title, the chart at 3x resolution, and a footer.
// =============================================================================

function slugify_(t) { return (t || 'chart').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, ''); }

// =============================================================================
// NAV: hamburger menu on phones + highlight the section you're in
// =============================================================================

function initNav() {
    const nav = document.querySelector('nav');
    const toggle = document.getElementById('navToggle');
    const links = document.getElementById('navLinks');
    if (!nav || !toggle || !links) return;

    const setOpen = (open) => {
        nav.classList.toggle('nav-open', open);
        toggle.setAttribute('aria-expanded', String(open));
        toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    };
    toggle.addEventListener('click', (e) => { e.stopPropagation(); setOpen(!nav.classList.contains('nav-open')); });
    links.querySelectorAll('a').forEach(a => a.addEventListener('click', () => setOpen(false)));
    document.addEventListener('click', (e) => { if (!nav.contains(e.target)) setOpen(false); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') setOpen(false); });
    window.addEventListener('resize', () => { if (window.innerWidth > 768) setOpen(false); });

    // Highlight the current section in the menu
    const map = new Map();
    links.querySelectorAll('a[href^="#"]').forEach(a => {
        const sec = document.querySelector(a.getAttribute('href'));
        if (sec) map.set(sec, a);
    });
    if (!('IntersectionObserver' in window) || !map.size) return;
    const io = new IntersectionObserver((entries) => {
        entries.forEach(en => {
            if (en.isIntersecting) {
                links.querySelectorAll('a').forEach(a => a.classList.remove('active'));
                map.get(en.target)?.classList.add('active');
            }
        });
    }, { rootMargin: '-45% 0px -50% 0px' });
    map.forEach((_, sec) => io.observe(sec));
}

function addChartDownloadButtons() {
    document.querySelectorAll('main .chart-container, section .chart-container').forEach(box => {
        if (box.closest('.modal-overlay') || box.querySelector('.chart-dl')) return;
        const canvas = box.querySelector('canvas');
        const header = box.querySelector('.chart-header');
        if (!canvas || !header) return;
        const wrap = document.createElement('span');
        wrap.className = 'chart-dl';
        wrap.innerHTML = `<button title="Download PNG" data-fmt="png">PNG</button><button title="Download PDF" data-fmt="pdf">PDF</button>`;
        wrap.querySelectorAll('button').forEach(b => b.addEventListener('click', (e) => {
            e.stopPropagation();
            downloadChart(box, b.dataset.fmt, b);
        }));
        const help = header.querySelector('.info-trigger-small');
        help ? header.insertBefore(wrap, help) : header.appendChild(wrap);
    });
}

function chartImage(canvas, ratio = 3) {
    // Re-render the chart at high resolution, grab it, then restore the on-screen chart
    const chart = window.Chart?.getChart?.(canvas);
    if (!chart) return { src: canvas.toDataURL('image/png'), w: canvas.clientWidth, h: canvas.clientHeight };
    const prev = chart.options.devicePixelRatio;
    chart.options.devicePixelRatio = ratio;
    chart.resize();
    chart.update('none');
    const src = chart.toBase64Image('image/png', 1);
    const w = canvas.clientWidth, h = canvas.clientHeight;
    chart.options.devicePixelRatio = prev;
    chart.resize();
    chart.update('none');
    return { src, w, h };
}

async function composeChartCard(box) {
    const title = box.querySelector('.chart-title')?.textContent.trim() || 'Chart';
    const section = box.closest('section');
    const kicker = section?.querySelector('.section-number')?.textContent.trim() || '';
    const img = chartImage(box.querySelector('canvas'));
    const css = getComputedStyle(document.documentElement);
    const v = (n, f) => css.getPropertyValue(n).trim() || f;
    const S = 3, pad = 40;
    const W = Math.round(Math.max(img.w + pad * 2, 720));          // a minimum width keeps titles and footers readable
    const inner = W - pad * 2;

    // Measure text first so the title shrinks to fit and the footer wraps instead of overlapping
    const m = document.createElement('canvas').getContext('2d');
    let tSize = 30;
    m.font = `700 ${tSize}px ${v('--font-display', 'sans-serif')}`;
    while (m.measureText(title).width > inner && tSize > 16) { tSize -= 1; m.font = `700 ${tSize}px ${v('--font-display', 'sans-serif')}`; }
    const when = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    const right = `${when} · data through ${state.season?.currentSeason ?? ''} Week ${state.season?.throughWeek ?? ''}`;
    m.font = `600 15px ${v('--font-body', 'sans-serif')}`; const leftW = 26 + m.measureText('nflobservatory.com').width;
    m.font = `400 13px ${v('--font-body', 'sans-serif')}`; const rightW = m.measureText(right).width;
    const footTwoLines = leftW + rightW + 24 > inner;
    const headH = 58 + tSize + 12, footH = footTwoLines ? 82 : 60;
    const H = Math.round(headH + img.h + footH + 16);

    const c = document.createElement('canvas');
    c.width = W * S; c.height = H * S;
    const ctx = c.getContext('2d');
    ctx.scale(S, S);
    ctx.fillStyle = v('--bg-card', '#16181b'); ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = v('--accent', '#ffc400');
    ctx.font = `600 12px ${v('--font-mono', 'monospace')}`;
    ctx.fillText(kicker.toUpperCase(), pad, pad + 4);
    ctx.fillStyle = v('--text-primary', '#ecebe7');
    ctx.font = `700 ${tSize}px ${v('--font-display', 'sans-serif')}`;
    ctx.fillText(title, pad, pad + 14 + tSize);

    const im = new Image();
    await new Promise((res, rej) => { im.onload = res; im.onerror = rej; im.src = img.src; });
    ctx.drawImage(im, Math.round((W - img.w) / 2), headH, img.w, img.h);

    const fy = headH + img.h + 22;
    ctx.strokeStyle = v('--border-subtle', '#262a2f'); ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(pad, fy); ctx.lineTo(W - pad, fy); ctx.stroke();
    const ly = fy + 30;
    ctx.save(); ctx.translate(pad + 8, ly - 5); ctx.rotate(-0.31); ctx.fillStyle = '#ffc400'; ctx.fillRect(-6, -6, 12, 12); ctx.restore();
    ctx.fillStyle = v('--text-primary', '#ecebe7'); ctx.font = `600 15px ${v('--font-body', 'sans-serif')}`;
    ctx.fillText('nflobservatory.com', pad + 26, ly);
    ctx.fillStyle = v('--text-muted', '#6d7178'); ctx.font = `400 13px ${v('--font-body', 'sans-serif')}`;
    if (footTwoLines) ctx.fillText(right, pad, ly + 24);
    else ctx.fillText(right, W - pad - rightW, ly);
    return { canvas: c, title, w: W, h: H };
}

async function downloadChart(box, fmt, btn) {
    const label = btn.textContent;
    btn.disabled = true; btn.textContent = '…';
    try {
        const { canvas, title, w, h } = await composeChartCard(box);
        const name = `nfl-observatory-${slugify_(title)}.${fmt}`;
        if (fmt === 'png') {
            const blob = await new Promise(res => canvas.toBlob(res, 'image/png'));
            deliverPng(blob, name);
        } else {
            await loadScriptOnce(EXPORT_LIBS.jspdf);
            const { jsPDF } = window.jspdf;
            const pdf = new jsPDF({ orientation: w > h ? 'landscape' : 'portrait', unit: 'px', format: [w, h], hotfixes: ['px_scaling'] });
            pdf.addImage(canvas.toDataURL('image/jpeg', 0.92), 'JPEG', 0, 0, w, h);   // JPEG keeps the PDF small
            pdf.setProperties({ title, creator: 'nflobservatory.com' });
            pdf.save(name);
        }
        btn.textContent = '✓';
    } catch (err) {
        console.error('Chart download failed:', err);
        btn.textContent = '✗';
    } finally {
        setTimeout(() => { btn.textContent = label; btn.disabled = false; }, 1500);
    }
}

// =============================================================================
// SAVE TO PHOTOS (phones)
// Browsers can't save straight to the camera roll; downloads land in Files /
// Downloads. The share sheet can ("Save Image" on iPhone, Photos/Gallery on
// Android), but it only opens directly from a tap, and building the image takes
// longer than that. So on phones we show the finished image with a
// "Save to Photos" button: that tap opens the share sheet instantly.
// Desktop keeps the normal one-click download.
// =============================================================================

function isPhoneLike() {
    return window.matchMedia?.('(pointer: coarse)').matches && /Android|iPhone|iPad|iPod/i.test(navigator.userAgent || '')
        || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);   // iPadOS reports as Mac
}

function downloadBlob(blob, name) {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
}

function deliverPng(blob, name) {
    const file = new File([blob], name, { type: 'image/png' });
    const canShareFile = !!(navigator.canShare && navigator.canShare({ files: [file] }));
    if (!isPhoneLike()) { downloadBlob(blob, name); return; }
    showSaveSheet(blob, file, name, canShareFile);
}

function showSaveSheet(blob, file, name, canShareFile) {
    document.getElementById('saveSheet')?.remove();
    const url = URL.createObjectURL(blob);
    const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    const sheet = document.createElement('div');
    sheet.id = 'saveSheet';
    sheet.className = 'save-sheet';
    sheet.innerHTML = `
        <div class="save-sheet-panel" role="dialog" aria-label="Save image">
            <div class="save-sheet-head">
                <span>Your image is ready</span>
                <button class="save-sheet-x" aria-label="Close">✕</button>
            </div>
            <div class="save-sheet-img"><img src="${url}" alt="Exported image"></div>
            ${canShareFile ? `<button class="save-sheet-btn" id="saveSheetShare">Save to Photos</button>` : ''}
            <p class="save-sheet-hint">${canShareFile
                ? (isIOS ? 'Tap <b>Save to Photos</b>, then choose <b>Save Image</b>.' : 'Tap <b>Save to Photos</b>, then choose Photos or Gallery.')
                : (isIOS ? 'Press and hold the image, then tap <b>Save to Photos</b>.' : 'Press and hold the image, then tap <b>Download image</b>.')}
                ${canShareFile ? `<br>Or press and hold the image to save it.` : ''}</p>
            <button class="save-sheet-link" id="saveSheetFile">Save as a file instead</button>
        </div>`;
    document.body.appendChild(sheet);
    const close = () => { sheet.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000); };
    sheet.querySelector('.save-sheet-x').onclick = close;
    sheet.addEventListener('click', (e) => { if (e.target === sheet) close(); });
    sheet.querySelector('#saveSheetFile').onclick = () => downloadBlob(blob, name);
    const shareBtn = sheet.querySelector('#saveSheetShare');
    if (shareBtn) shareBtn.onclick = async () => {
        try {
            await navigator.share({ files: [file], title: name.replace(/\.png$/, '') });
            close();
        } catch (err) {
            if (err?.name !== 'AbortError') shareBtn.textContent = 'Press and hold the image instead';
        }
    };
}

async function copyModalLink() {
    const btn = document.getElementById('modalShare');
    try {
        await navigator.clipboard.writeText(location.href);
        if (btn) { btn.textContent = 'Copied ✓'; setTimeout(() => { btn.textContent = 'Copy link'; }, 1800); }
    } catch {
        if (btn) btn.textContent = location.href;
    }
}

// =============================================================================
// EXPLAINER MODAL
// =============================================================================

function openExplainer(key) {
    const explainer = EXPLAINERS[key];
    if (!explainer) return;
    
    document.getElementById('explainerTitle').textContent = explainer.title;
    document.getElementById('explainerContent').innerHTML = explainer.content;
    document.getElementById('explainerModal').classList.add('active');
}

function closeExplainer() {
    document.getElementById('explainerModal')?.classList.remove('active');
}

// =============================================================================
// SCROLL ANIMATIONS
// =============================================================================

function initScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, { threshold: 0.1 });
    
    document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));
}

// =============================================================================
// INITIALIZATION
// =============================================================================

async function init() {
    console.log('🏈 NFL Officiating Observatory v2 initializing...');
    
    await loadAllData();
    
    renderSeasonComparison();
    renderPreviews();
    renderTrackRecord();
    renderCharts();
    renderRefereeCards();   // uses state.season, so render after it loads
    renderTeams();
    renderScoreboard();
    renderTypeTrends();
    renderDataTable();
    renderInsightsCarousel();
    
    initScrollAnimations();

    // PNG / PDF download buttons on every chart (charts exist by now)
    addChartDownloadButtons();
    initNav();

    // Open a specific report if the URL asks for one (e.g. from a social post)
    handleDeepLink();
    // Plain section links (#typeTrends, #teams): the content is drawn after load,
    // so scroll once it exists
    if (location.hash.length > 1 && !DEEP_LINK_RE.test(location.hash)) {
        setTimeout(() => { try { document.querySelector(location.hash)?.scrollIntoView({ block: 'start' }); } catch {} }, 250);
    }
    window.addEventListener('hashchange', () => {
        // A section link (#teams) or a new report link: close any open pop-up first
        document.getElementById('modal')?.classList.remove('active');
        handleDeepLink();
    });
    
    // Event listeners
    document.getElementById('modal')?.addEventListener('click', (e) => {
        if (e.target.id === 'modal') closeModal();
    });
    
    document.getElementById('explainerModal')?.addEventListener('click', (e) => {
        if (e.target.id === 'explainerModal') closeExplainer();
    });
    
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeModal();
            closeExplainer();
        }
    });
    
    console.log('✅ Initialization complete');
}

document.addEventListener('DOMContentLoaded', init);

// Global exports
window.openRefereeModal = openRefereeModal;
window.openPreviewModal = openPreviewModal;
window.openTeamModal = openTeamModal;
window.setTeamBaseline = setTeamBaseline;
window.setScoreboardFrame = setScoreboardFrame;
window.setScoreboardWeek = setScoreboardWeek;
window.toggleScoreboardWeekMenu = toggleScoreboardWeekMenu;
window.toggleWeekLayer = toggleWeekLayer;
window.setTypeTrendsCompare = setTypeTrendsCompare;
window.toggleAllOpponents = toggleAllOpponents;
window.openScorecardModal = openScorecardModal;
window.selectDivision = selectDivision;
window.closeModal = closeModal;
window.copyModalLink = copyModalLink;
window.exportModal = exportModal;
window.exportBlock = exportBlock;
window.copyBlockLink = copyBlockLink;
window.openExplainer = openExplainer;
window.closeExplainer = closeExplainer;
window.moveCarousel = moveCarousel;
window.goToSlide = goToSlide;
