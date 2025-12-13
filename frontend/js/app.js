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
    
    const [stats, referees, trends, insights] = await Promise.all([
        fetchJSON('stats.json'),
        fetchJSON('referees.json'),
        fetchJSON('trends.json'),
        fetchJSON('insights.json')
    ]);
    
    state.stats = stats;
    state.referees = referees || [];
    state.trends = trends;
    state.insights = insights || [];
    
    // Pre-load all referee profiles for card previews
    await preloadRefereeProfiles();
    
    console.log('✓ Data loaded');
    return { stats, referees, trends, insights };
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
// RENDERING - HERO STATS
// =============================================================================

function renderHeroStats() {
    if (!state.stats) return;
    
    const container = document.getElementById('heroStats');
    if (!container) return;
    
    container.innerHTML = `
        <div class="stat-card">
            <div class="stat-value" data-count="${state.stats.totalPenalties}">0</div>
            <div class="stat-label">Total Penalties</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" data-count="${state.stats.totalGames}">0</div>
            <div class="stat-label">Games Analyzed</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" data-count="${state.stats.totalReferees}">0</div>
            <div class="stat-label">Crew Chiefs</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${state.stats.refereeVariance || '24%'}</div>
            <div class="stat-label">Ref Variance</div>
        </div>
    `;
    
    animateCounters();
}

function animateCounters() {
    document.querySelectorAll('[data-count]').forEach(el => {
        const target = parseInt(el.dataset.count);
        const duration = 2000;
        const start = performance.now();
        
        function update(now) {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            el.textContent = Math.floor(target * eased).toLocaleString();
            if (progress < 1) requestAnimationFrame(update);
        }
        requestAnimationFrame(update);
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
    
    container.innerHTML = state.referees.map((ref, index) => {
        // Get most common penalty from cached profile
        const profile = state.refereeProfiles[ref.slug];
        const topPenalty = profile?.penaltyTypes?.[0];
        const topPenaltyDisplay = topPenalty 
            ? topPenalty.type.replace('Offensive ', '').replace('Defensive ', '').replace(' (Offense)', '')
            : null;
        
        return `
            <div class="referee-card" onclick="openRefereeModal('${ref.slug}')" data-index="${index}">
                <div class="referee-name">${ref.name}</div>
                <div class="referee-meta">${ref.first_season}-${ref.last_season} • ${ref.games} games</div>
                ${topPenaltyDisplay ? `<div class="referee-top-penalty">🚩 Most common: <strong>${topPenaltyDisplay}</strong></div>` : ''}
                <div class="referee-stats">
                    <div class="referee-stat">
                        <div class="referee-stat-value">${ref.avg_per_game}</div>
                        <div class="referee-stat-label">Avg/Game</div>
                    </div>
                    <div class="referee-stat">
                        <div class="referee-stat-value">${ref.min_penalties}-${ref.max_penalties}</div>
                        <div class="referee-stat-label">Range</div>
                    </div>
                    <div class="referee-stat">
                        <div class="referee-stat-value ${ref.home_bias_pct > 5 ? 'cell-high' : ref.home_bias_pct < 0 ? 'cell-low' : ''}">${ref.home_bias_pct > 0 ? '+' : ''}${ref.home_bias_pct}%</div>
                        <div class="referee-stat-label">Home Bias</div>
                    </div>
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
    
    renderHeroStats();
    renderInsightsCarousel();
    renderRefereeCards();
    renderCharts();
    renderDataTable();
    
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
