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
        cyan: '#00f0ff',
        purple: '#a855f7',
        orange: '#ff6b35',
        green: '#10b981',
        red: '#ef4444',
        yellow: '#fbbf24',
        gold: '#FFD700'
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
        const response = await fetch(`${CONFIG.dataPath}/${filename}`);
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
        `Regular season through Week ${d.throughWeek}, compared with ${base.label.charAt(0).toLowerCase() + base.label.slice(1)}.`;
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
                    backgroundColor: CONFIG.chartColors.cyan,
                    borderRadius: 4,
                    barPercentage: 0.9,
                    categoryPercentage: 0.75
                },
                {
                    label: baseLabel,
                    data: rows.map(r => (baseOf(r) ? baseOf(r)[field] : null)),
                    backgroundColor: 'rgba(255, 255, 255, 0.22)',
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
            <div class="insight-icon">${insight.icon}</div>
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
            icon: '📈',
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
            icon: '🏠',
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
            icon: '🎯',
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
            icon: '🚩',
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
        || { home: CONFIG.chartColors.cyan, away: CONFIG.chartColors.purple };
}

function colorVars(g) {
    const c = gameColors(g);
    return `--home-c:${c.home};--away-c:${c.away};`;
}

// =============================================================================
// RENDERING - GAME PREVIEWS (next week)
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
            <span class="${g.crew ? '' : 'pv-tba'}">👨‍⚖️ ${g.crew ? g.crew.name : 'Crew TBA'}</span>
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
    const drivers = p.drivers.map(d => `
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
            <h4>👨‍⚖️ The crew: <a href="#" onclick="openRefereeModal('${g.crew.slug}'); return false;">${g.crew.name}</a></h4>
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
            <h4>👨‍⚖️ The crew</h4>
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
                    <span>${w.count} flags · ${w.yards} yds</span>
                    <span class="modal-muted">${w.types.map(x => `${x.type}${x.count > 1 ? ` ×${x.count}` : ''}`).join(', ')}</span></div>`).join('') || '<span class="modal-muted">No individual penalties yet</span>'}
            </div>
        </div>`;

    // Context
    const c = g.context, ref = pv.contextReference || {};
    const chips = [];
    if (c.primetime) chips.push('🌙 Primetime');
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
            <h4>🧭 What's driving the projection</h4>
            ${drivers}
            <p class="modal-footnote">Extra or fewer flags vs a league-average matchup with an average crew.</p>
        </div>

        <div class="modal-section">
            <h4>🚩 Projected penalties by type</h4>
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
            <h4>📍 Context</h4>
            <div class="pv-chips">${chips.map(x => `<span class="pv-chip">${x}</span>`).join('')}</div>
            <p class="modal-footnote">Shown for reference; not added into the projection.</p>
        </div>

        ${h2h ? `<div class="modal-section"><h4>🔁 Recent meetings</h4><div class="game-list">${h2h}</div></div>` : ''}

        <p class="modal-footnote">Projection uses ${pv.model.seasons.join(', ')} regular seasons, weighted toward ${pv.season}.
        ${pv.assignments?.source?.url ? `Crew assignments via <a href="${pv.assignments.source.url}" target="_blank" rel="noopener">Football Zebras</a>.` : ''}</p>
    `;
    modal.classList.add('active');
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
                    ${topPenaltyDisplay ? `<span>🚩 Most common: <strong>${topPenaltyDisplay}</strong></span>` : '<span></span>'}
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
                borderColor: CONFIG.chartColors.cyan,
                backgroundColor: 'rgba(0, 240, 255, 0.1)',
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
    
    const colors = [
        CONFIG.chartColors.cyan, CONFIG.chartColors.purple, CONFIG.chartColors.orange,
        CONFIG.chartColors.green, CONFIG.chartColors.red, CONFIG.chartColors.yellow,
        '#6366f1', '#ec4899', '#14b8a6', '#f97316'
    ];
    
    state.charts.type = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: state.trends.byType.map(t => t.type),
            datasets: [{
                data: state.trends.byType.map(t => t.count),
                backgroundColor: colors,
                borderWidth: 0
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
                    CONFIG.chartColors.cyan
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
        
        const colors = [CONFIG.chartColors.cyan, CONFIG.chartColors.purple, CONFIG.chartColors.orange,
                        CONFIG.chartColors.green, CONFIG.chartColors.red, CONFIG.chartColors.yellow];
        
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
                    backgroundColor: [
                        CONFIG.chartColors.cyan, CONFIG.chartColors.purple,
                        CONFIG.chartColors.orange, CONFIG.chartColors.green
                    ],
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
            <h4>📊 ${active ? `${cs} vs history` : 'Regular-season history'}</h4>
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
            <h4>🎯 ${cs} so far</h4>
            <p>${seasonTendency}</p>
            <p class="modal-tendency-career"><strong>Career:</strong> ${profile.tendencies?.description || 'League-average officiating style'}</p>
        </div>` : `
        <div class="modal-tendency">
            <h4>🎯 Tendencies</h4>
            <p>${profile.tendencies?.description || 'League-average officiating style'}</p>
        </div>`}

        <div class="chart-container modal-section">
            <div class="chart-title">📈 Penalties per game by season <span class="modal-muted">(regular season)</span></div>
            <div class="chart-wrapper" style="height: 200px;">
                <canvas id="modalSeasonChart"></canvas>
            </div>
        </div>

        ${typesHtml}

        ${quartersHtml}

        <div class="modal-section">
            <h4>🗂️ Career (all games incl. playoffs, ${profile.firstSeason}–${profile.lastSeason})</h4>
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
            <h4 style="margin-bottom: 0.75rem;">📋 Recent Games</h4>
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
        <span><i class="pair-swatch pair-prior"></i>${allLabel} avg</span>
        <span class="modal-muted">per game</span>
    </div>`;
}

function renderTypeComparison(types, cs, allLabel, small) {
    const rows = types.slice(0, 10);
    return `
        <div class="modal-section">
            <h4>🚩 What's being called: ${cs} vs ${allLabel}</h4>
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
            <h4 style="margin-bottom: 0.75rem;">🚩 Penalty Type Breakdown</h4>
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
        backgroundColor: seasons.map(s => s.season === cs ? CONFIG.chartColors.cyan : 'rgba(255,255,255,0.22)'),
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
                          labels: { color: 'rgba(255,255,255,0.6)', boxWidth: 12, font: { size: 10 } } },
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
    renderCharts();
    renderRefereeCards();   // uses state.season, so render after it loads
    renderDataTable();
    renderInsightsCarousel();
    
    initScrollAnimations();
    
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
window.closeModal = closeModal;
window.openExplainer = openExplainer;
window.closeExplainer = closeExplainer;
window.moveCarousel = moveCarousel;
window.goToSlide = goToSlide;
