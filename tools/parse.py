"""Builds corpus.d/10-lei-organica.json for the Município de Fortaleza from the Câmara Municipal's SAPL (no network).

    python -X utf8 parse.py --today YYYY-MM-DD

SAPL keeps the Lei Orgânica (2006) as a "Texto Articulado" (TA 44) with one view per period of vigência
("/ta/44/text/vigencia/<n>,<from>,<to>:..."), plus the norma page for the text in force now: the text as in force
from <from>, and the act that gave it ("Dada por
Emenda à Lei Orgânica nº ..."). Each view is one version, dated by its <from> day and credited to that act (the first
to the Lei Orgânica itself). Each provision is one line: its label ("Art. 1º.", "§ 1º", "XV –") and its text; the
notes SAPL keeps under a provision or links into it ("Inclusão feita pelo ..."), any provision it marks as superseded
("desativado") and the amending act's own blocks it shows inside the text ("bloco_alteracao") are left out.
"""
import argparse, html, json, re, sys
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import br_lib  # noqa: E402
from br_lib import units_of, write_part, sha, norm  # noqa: E402

# The Lei Orgânica's closing part: "Ato das Disposições Orgânicas Transitórias" (articles numbered from 1 again).
br_lib.ADT = re.compile(r'DISPOSI[ÇC][ÕO]ES\s+(?:ORG[ÂA]NICAS\s+|GERAIS\s+E\s+|CONSTITUCIONAIS\s+)?TRANSIT[ÓO]RIAS', re.I)

BASE = 'https://sapl.fortaleza.ce.leg.br'
RAW = HERE / '.cache' / 'sapl' / 'raw'
BLOCK = {'p', 'div', 'br', 'tr', 'li', 'table', 'tbody', 'thead', 'ul', 'ol', 'center', 'blockquote', 'h1', 'h2', 'h3',
         'h4', 'h5', 'h6'}
VOID = {'br', 'img', 'meta', 'link', 'hr', 'input', 'col', 'area', 'base', 'wbr'}


class TA(HTMLParser):
    """Lines of a SAPL Texto Articulado view: one per provision (div.dptt), table rows one line each."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.lines, self.buf, self.label = [], [], None, []

    def flush(self):
        if self.buf is not None:
            ls = [norm(l).strip(' |').strip() for l in ''.join(self.buf).split('\n')]
            ls = [l for l in ls if l and re.search(r'\w', l)]
            label = norm(''.join(self.label))
            # the provision's label ("Art. 1º.", "§ 1º", "TÍTULO I") and its text are one line
            if label and len(ls) > 1 and ls[0].rstrip(' -–.') == label.rstrip(' -–.'):
                ls[:2] = [ls[0] + ' ' + ls[1]]
            self.lines += ls
            self.buf, self.label = [], []

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            if tag == 'br' and self.buf is not None:
                self.buf.append('\n')
            return
        cls = (dict(attrs).get('class') or '').split()
        role = None
        if tag == 'div' and 'bloco_alteracao' in cls:
            role = 'skip'  # the amending act's own block, shown inside the text: not the Lei Orgânica's words
        elif tag == 'div' and 'dptt' in cls:
            role = 'skip' if 'desativado' in cls else 'dptt'
            if role == 'dptt':
                self.flush()
                self.buf = []
        elif tag == 'div' and 'dn' in cls:
            role = 'skip'
        elif tag == 'a' and 'nota-alteracao' in cls:
            role = 'skip'  # SAPL's note "Inclusão feita pelo Art. 1º. - Emenda à Lei Orgânica nº ..."
        elif tag == 'a' and 'dpt-link' in cls:
            role = 'label'
        self.stack.append((tag, role))
        if self.buf is not None and not self.skipping():
            if tag in BLOCK:
                self.buf.append('\n')
            elif tag in ('td', 'th'):
                self.buf.append(' | ')

    def skipping(self):
        return any(r == 'skip' for _, r in self.stack)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                closed = self.stack[i:]
                del self.stack[i:]
                if any(r == 'dptt' for _, r in closed):
                    self.flush()
                    self.buf = None
                break
        if self.buf is not None and not self.skipping() and tag in BLOCK:
            self.buf.append('\n')

    def handle_data(self, d):
        if self.buf is not None and not self.skipping():
            self.buf.append(d)
            if any(r == 'label' for _, r in self.stack):
                self.label.append(d)


def lines_of_view(b):
    p = TA()
    p.feed(b.decode('utf-8', 'replace'))
    p.close()
    return p.lines


VIEW = re.compile(r'/ta/44/text/vigencia/(\d+),(\d{4}-\d{2}-\d{2}),(\d{4}-\d{2}-\d{2}):[^/]+/')
MONTHS = {m: i + 1 for i, m in enumerate(['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto',
                                           'setembro', 'outubro', 'novembro', 'dezembro'])}


def given_by(b):
    """The act SAPL names under the view: "Dada por <a>Emenda à Lei Orgânica nº 25, de 30 de junho de 2025</a>"."""
    m = re.search(r'Dada por\s*<a href="([^"]+)">([^<]+)</a>', b.decode('utf-8', 'replace'))
    return (html.unescape(m.group(2)).strip(), m.group(1)) if m else (None, None)


COUNTRY = {
    'code': 'BR-CE-FORTALEZA', 'name': 'Fortaleza', 'slug': 'brazil-fortaleza-city', 'lang': 'pt',
    'tz': 'America/Fortaleza', 'future_branch': 'futuro',
    'publisher': {'name': 'Câmara Municipal de Fortaleza (SAPL)', 'email': 'sapl@cmfor.ce.gov.br.invalid'},
    'default_in_force_rule': {
        'text': 'The Lei Orgânica and its amendments are promulgated by the Mesa da Câmara and take effect as they '
                'state; this record dates each version by the first day of vigência SAPL gives it.',
        'source': 'https://sapl.fortaleza.ce.leg.br/norma/5257'},
    'licence_note': 'Text: Câmara Municipal de Fortaleza, SAPL (Sistema de Apoio ao Processo Legislativo), Lei Orgânica '
                    'do Município de Fortaleza, sapl.fortaleza.ce.leg.br. Lei 9.610/1998 art. 8 IV: the texts of laws '
                    'and other official acts are not protected by copyright. Non-official text: only the Diário '
                    'Oficial do Município is authoritative.',
}
DECISIONS = [
    'Each version is one SAPL "vigência" view of the Lei Orgânica\'s Texto Articulado: the text in force from the '
    'view\'s first day, dated by that day and credited to the act SAPL says gave it ("Dada por ..."); the first view '
    '(from 15 December 2006) is credited to the Lei Orgânica itself. Where two views start on the same day (two '
    'amendments of the same date), both are kept, in SAPL order, as two versions of that day. Each unit that '
    'differs from the view before is credited to the act that gave the view.',
    'The last version is the text SAPL shows as in force now (the norma page, "Vigência a partir de 30 de Junho de 2025", '
    '"Dada por" Emenda à Lei Orgânica nº 25). Where SAPL starts a period without naming an amending act (from 27 August '
    '2021), the units that changed are left uncredited and committed as publisher commits, not guessed.',
    'Each provision is one line: its label ("Art. 1º.", "§ 1º", "XV –") followed by its text; table rows are one line '
    'each, cells separated by " | ". Notes SAPL keeps under a provision or links into it ("Inclusão feita pelo ..."), '
    'provisions it marks as superseded and the amending acts own blocks it shows inside the text are left out.',
    'One file per Art.; headings stand above the first article under them; the "Ato das Disposições Orgânicas '
    'Transitórias", numbered from 1 again, is adt-*. "000-titulo" holds the preamble.',
]
AI = ["Claude Code (claude-opus-5-5) wrote Lexifina's code and chose the sources. No model output is used as legal "
      "text or dates: every word comes from the SAPL pages."]


def law_key(label):
    m = re.search(r'Emenda à Lei Orgânica nº\s*(\d+)(?:-([A-Za-z]))?, de (\d{1,2}) de (\w+) de (\d{4})', label)
    if not m:
        return None, None
    d = f'{m.group(5)}-{MONTHS[m.group(4).lower()]:02d}-{int(m.group(3)):02d}'
    suffix = f'-{m.group(2).lower()}' if m.group(2) else ''  # "nº 5-A"
    return f'elo-{m.group(5)}-{int(m.group(1)):03d}{suffix}', d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--today', required=True)
    a = ap.parse_args()
    page = (RAW / sha((BASE + '/norma/5257').encode())).read_bytes().decode('utf-8', 'replace')
    views = []
    for m in VIEW.finditer(page):
        p = RAW / sha((BASE + m.group(0)).encode())
        if not p.exists():
            raise SystemExit(f'not fetched yet: {m.group(0)}')
        if m.group(3) < m.group(2):
            continue  # an empty period (ends the day before it starts), naming no act: SAPL bookkeeping, no version
        views.append((m.group(2), int(m.group(1)), m.group(0), p))
    views = sorted(set(views))
    # The text in force now ("Texto Atual") is the norma page itself: "Vigência a partir de <b>30 de Junho de 2025</b>"
    m = re.search(r'Vigência a partir de <b>(\d{1,2}) de (\w+) de (\d{4})</b>', page)
    if m:
        d0 = f'{m.group(3)}-{MONTHS[m.group(2).lower()]:02d}-{int(m.group(1)):02d}'
        if d0 > views[-1][0]:
            views.append((d0, 10 ** 9, '/norma/5257', RAW / sha((BASE + '/norma/5257').encode())))
    laws = {'lom-2006': {'label': 'Lei Orgânica do Município de Fortaleza, de 15 de dezembro de 2006',
                         'title': 'Dispõe sobre a Lei Orgânica do Município de Fortaleza.', 'kind': 'law',
                         'enacted': '2006-12-15', 'published': '2006-12-15', 'url': BASE + '/norma/5257',
                         'temporary_until': None, 'restores': None, 'note': None}}
    versions, prev = [], None
    for i, (d0, n, path, p) in enumerate(views):
        b = p.read_bytes()
        units = units_of([('p', l) for l in lines_of_view(b)], title_label='Preâmbulo', adt=True)
        if prev is None:
            versions.append({'from': d0, 'source_url': BASE + path, 'sha256': sha(b), 'units': units})
            prev = units
            continue
        label, href = given_by(b)
        key, enacted = law_key(label or '')
        if not key and not (label or '').startswith('Lei Orgânica nº 1'):
            raise SystemExit(f'no amending act for {path}: {label!r}')
        if key:
            laws.setdefault(key, {'label': label, 'title': label, 'kind': 'law', 'enacted': enacted,
                                  'published': None, 'url': BASE + href, 'temporary_until': None, 'restores': None,
                                  'note': None})
        changes = {k: u for k, u in units.items() if prev.get(k) != u}
        changes.update({k: None for k in prev if k not in units})
        # SAPL names no amending act for this period ("Dada por" the Lei Orgânica itself): its changes are left
        # uncredited, so the builder commits them as the publisher's ("unexplained"), never guessed.
        v = {'from': d0, 'source_url': BASE + path, 'sha256': sha(b), 'changes': changes,
             'credits': {k: [key] for k in changes} if key else {}}
        if not key:
            v['note'] = ('SAPL starts a period of vigência on this day without naming an amending act ("Dada por" '
                         'the Lei Orgânica itself).')
        if not changes:
            v['credits'] = {}
            v['note'] = f'SAPL gives a new period of vigência from this day ({label}) with no change of wording.'
        if versions[-1]['from'] == d0:
            v['same_day'] = True
        versions.append(v)
        prev = units
    act = {'slug': 'lei-organica', 'short': 'LOM-Fortaleza', 'title': 'Lei Orgânica do Município de Fortaleza',
           'url': BASE + '/norma/5257', 'first_law': 'lom-2006', 'earlier_laws': [], 'versions': versions}
    c = {'country': COUNTRY,
         'sources': [{'name': 'Câmara Municipal de Fortaleza, SAPL: Texto Articulado of the Lei Orgânica, one view per '
                              'period of vigência', 'url': BASE + '/norma/5257', 'retrieved': a.today,
                      'licence': COUNTRY['licence_note'], 'notes': f'{len(versions)} versions.'}],
         'laws': laws, 'acts': [act], 'applies': [], 'decisions': DECISIONS, 'ai_use': AI}
    print(write_part(HERE / 'corpus.d', '10-lei-organica', c), len(versions), 'versions')


if __name__ == '__main__':
    main()
