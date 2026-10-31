"""Full pages are supersets of their home sections (#166; Ty, 2026-10-31).

Every full page ("See all ->" from a home section) carries all of that section's
charts, tables, cards and pop-outs, fully interactive, plus its own content. The
interactive parts are the home page's own blocks, copied by element id at build time
(build_static.py) and drawn by app.js, so there's one copy of each.

Standard library only. Used by build_static.py (which blocks a page shows), check.py
("Full pages": the superset rule) and tests.
"""

import re
from html.parser import HTMLParser

# blocks: home-page element ids the page shows, in the page's own order (visitor intent).
# explainers: "?" explainers from the section's header, which the page adds itself.
# pending: the issue that builds the page. The checks can't see issue states (no network),
# so that issue's work removes "pending" and lists the blocks.
FULL_PAGES = {
    '/crew/': {'section': 'referees', 'blocks': ['refereeGrid', 'data'], 'explainers': ['crew-chief']},
    '/assignments/': {'section': 'previews', 'pending': 167},
    '/team/': {'section': 'teams', 'blocks': ['divisionGrid', 'divisionTeams']},
    '/trends/': {'section': 'trends', 'pending': 169},
}

# The pop-up shells every interactive page needs (crew, team and game pop-outs; explainers)
SHELLS = ['modal', 'explainerModal']

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}
EXPLAINER_RE = re.compile(r"openExplainer\('([^']+)'\)")


class _Finder(HTMLParser):
    """Offsets of the element with a given id, from its start tag to its matching end tag."""

    def __init__(self, text, target):
        super().__init__(convert_charrefs=False)
        self.text, self.target = text, target
        self.line_starts = [0] + [i + 1 for i, ch in enumerate(text) if ch == '\n']
        self.tag, self.depth, self.start, self.end = None, 0, None, None

    def _offset(self):
        line, col = self.getpos()
        return self.line_starts[line - 1] + col

    def handle_starttag(self, tag, attrs):
        if self.end is not None:
            return
        if self.start is None:
            if dict(attrs).get('id') == self.target:
                self.tag, self.start, self.depth = tag, self._offset(), 1
                if tag in VOID:
                    self.end = self.text.index('>', self.start) + 1
        elif tag == self.tag and tag not in VOID:
            self.depth += 1

    def handle_endtag(self, tag):
        if self.start is None or self.end is not None or tag != self.tag:
            return
        self.depth -= 1
        if self.depth == 0:
            self.end = self.text.index('>', self._offset()) + 1


def element_by_id(text: str, element_id: str) -> str:
    """The element with that id, children included, exactly as written in text."""
    f = _Finder(text, element_id)
    f.feed(text)
    f.close()
    if f.start is None or f.end is None:
        raise ValueError(f'no element with id="{element_id}"')
    return text[f.start:f.end]


def ids_in(fragment: str) -> set[str]:
    """Every element id in an HTML fragment."""
    return set(re.findall(r'\sid="([^"]+)"', fragment))


def canvases_in(fragment: str) -> set[str]:
    return set(re.findall(r'<canvas[^>]*\sid="([^"]+)"', fragment))


def section_problems(home: str, path: str, spec: dict) -> list[str]:
    """What a done page's block list leaves out of its home section: every id and
    <canvas> in the section must be a listed block or inside one, and every "?"
    explainer outside the blocks must be listed under explainers."""
    section = element_by_id(home, spec['section'])
    blocks = spec.get('blocks', [])
    bad = []
    try:
        block_html = [element_by_id(section, b) for b in blocks]
    except ValueError as ex:
        return [f'{path}: {ex} in home section #{spec["section"]}']
    covered = set(blocks).union(*(ids_in(b) for b in block_html)) if block_html else set()
    for i in sorted(ids_in(section) - {spec['section']} - covered):
        bad.append(f'{path}: home section #{spec["section"]} has id="{i}", not on the page (add it to FULL_PAGES blocks)')
    for c in sorted(canvases_in(section) - covered):
        bad.append(f'{path}: chart <canvas id="{c}"> in #{spec["section"]} is not on the page')
    outside = section
    for b in block_html:
        outside = outside.replace(b, '')
    for key in sorted(set(EXPLAINER_RE.findall(outside)) - set(spec.get('explainers', []))):
        bad.append(f"{path}: explainer '{key}' in #{spec['section']} is not on the page (add it to FULL_PAGES explainers)")
    return bad


def see_all_targets(home: str) -> list[str]:
    """The pages the home page's "See all ->" links go to."""
    return re.findall(r'<p class="see-all"><a href="([^"]+)"', home)
