"""Exact official team colors + the no-clash matchup rule (same as the website)."""
import math

TEAM_COLORS = {
    'ARI': ['#97233F', '#FFB612'], 'ATL': ['#A71930', '#A5ACAF'], 'BAL': ['#241773', '#9E7C0C'],
    'BUF': ['#00338D', '#C60C30'], 'CAR': ['#0085CA', '#BFC0BF'], 'CHI': ['#0B162A', '#C83803'],
    'CIN': ['#FB4F14'], 'CLE': ['#FF3C00', '#311D00'], 'DAL': ['#003594', '#869397', '#041E42'],
    'DEN': ['#FB4F14', '#002244'], 'DET': ['#0076B6', '#B0B7BC'], 'GB': ['#203731', '#FFB612'],
    'HOU': ['#03202F', '#A71930'], 'IND': ['#002C5F', '#A2AAAD'], 'JAX': ['#006778', '#D7A22A'],
    'KC': ['#E31837', '#FFB81C'], 'LA': ['#003594', '#FFD100'], 'LAC': ['#0080C6', '#FFC20E'],
    'LV': ['#A5ACAF'], 'MIA': ['#008E97', '#FC4C02', '#005778'], 'MIN': ['#4F2683', '#FFC62F'],
    'NE': ['#002244', '#C60C30', '#B0B7BC'], 'NO': ['#D3BC8D'], 'NYG': ['#0B2265', '#A71930', '#A5ACAF'],
    'NYJ': ['#125740', '#FFFFFF'], 'PHI': ['#004C54', '#A5ACAF', '#ACC0C6'], 'PIT': ['#FFB612'],
    'SEA': ['#002244', '#69BE28', '#A5ACAF'], 'SF': ['#AA0000', '#B3995D'],
    'TB': ['#D50A0A', '#FF7900', '#34302B'], 'TEN': ['#4B92DB', '#0C2340', '#C8102E'],
    'WAS': ['#5A1414', '#FFB612'],
}
MIN_DISTANCE = 45
FALLBACKS = ['#E5E7EB', '#00F0FF']


def _lab(hex_):
    r, g, b = (int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5))
    f = lambda v: ((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92
    r, g, b = f(r), f(g), f(b)
    x = (r * 0.4124 + g * 0.3576 + b * 0.1805) / 0.95047
    y = r * 0.2126 + g * 0.7152 + b * 0.0722
    z = (r * 0.0193 + g * 0.1192 + b * 0.9505) / 1.08883
    t = lambda v: v ** (1 / 3) if v > 0.008856 else 7.787 * v + 16 / 116
    x, y, z = t(x), t(y), t(z)
    return 116 * y - 16, 500 * (x - y), 200 * (y - z)


def delta_e(a, b):
    return math.dist(_lab(a), _lab(b))


def matchup_colors(home, away):
    H, A = TEAM_COLORS.get(home, ['#E5E7EB']), TEAM_COLORS.get(away, ['#9A9EA4'])
    far = lambda h: (lambda x: delta_e(x, h) >= MIN_DISTANCE)
    a = next((x for x in A if far(H[0])(x)), None) or next((x for x in FALLBACKS if far(H[0])(x)), None)
    if a:
        return H[0], a
    for h in H[1:]:
        a = next((x for x in A + FALLBACKS if far(h)(x)), None)
        if a:
            return h, a
    return H[0], FALLBACKS[1]
