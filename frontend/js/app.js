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
    
    document.getElementById('modalTitle').textContent = profile.name;
    document.getElementById('modalSubtitle').textContent = `${profile.experience} • ${profile.stats.games} games`;
    
    // Build penalty types HTML
    const penaltyTypesHtml = renderPenaltyTypesBreakdown(profile.penaltyTypes);
    
    // Build quarter distribution HTML
    const quarterDistHtml = renderQuarterDistribution(profile.quarterDistribution);
    
    modalBody.innerHTML = `
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
        
        <div class="chart-container" style="margin-bottom: 1.5rem;">
            <div class="chart-title">📈 Season Trend</div>
            <div class="chart-wrapper" style="height: 180px;">
                <canvas id="modalSeasonChart"></canvas>
            </div>
        </div>
        
        <div style="margin-bottom: 1.5rem; background: var(--bg-glass); border-radius: 12px; padding: 1rem; border-left: 3px solid var(--accent-purple);">
            <h4 style="margin-bottom: 0.5rem; color: var(--accent-cyan);">🎯 Tendencies</h4>
            <p style="color: var(--text-secondary); margin: 0;">${profile.tendencies?.description || 'League-average officiating style'}</p>
        </div>
        
        ${penaltyTypesHtml}
        
        ${quarterDistHtml}
        
        <div>
            <h4 style="margin-bottom: 0.75rem;">📋 Recent Games</h4>
            <div class="game-list">
                ${renderRecentGames(profile.recentGames)}
            </div>
        </div>
    `;
    
    setTimeout(() => renderModalChart(profile), 100);
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

function renderRecentGames(games) {
    if (!games || !games.length) {
        return '<p style="color: var(--text-muted);">No recent games available.</p>';
    }
    
    return games.slice(0, 10).map(g => `
        <div class="game-item">
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
                <div class="game-date">${g.date ? formatDate(g.date) : `Week ${g.week || '?'}, ${g.season}`}</div>
            </div>
            <div class="game-penalties">
                <div class="game-penalties-value">${g.penalties}</div>
                <div class="game-penalties-label">flags</div>
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

function renderModalChart(profile) {
    const ctx = document.getElementById('modalSeasonChart')?.getContext('2d');
    if (!ctx || !profile.seasonStats?.length) return;
    
    if (state.charts.modal) state.charts.modal.destroy();
    
    state.charts.modal = new Chart(ctx, {
        type: 'line',
        data: {
            labels: profile.seasonStats.map(s => s.season),
            datasets: [{
                label: 'Avg Penalties',
                data: profile.seasonStats.map(s => s.avg),
                borderColor: CONFIG.chartColors.cyan,
                backgroundColor: 'rgba(0, 240, 255, 0.1)',
                fill: true,
                tension: 0.4
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
window.closeModal = closeModal;
window.openExplainer = openExplainer;
window.closeExplainer = closeExplainer;
window.moveCarousel = moveCarousel;
window.goToSlide = goToSlide;
