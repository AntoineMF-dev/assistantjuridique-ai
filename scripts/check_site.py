#!/usr/bin/env python3
"""Contrôles SEO en local. Émule Cloudflare Pages (URLs propres + _redirects, 1re règle gagnante).
Usage : python3 scripts/check_site.py   (code retour != 0 si une erreur)"""
import re, glob, os, json, html, collections, sys
from html.parser import HTMLParser
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
BASE = 'https://assistantjuridique.ai'
errors = []
def err(m): errors.append(m); print('ERREUR', m)

# --- émulation Pages ---
rules = []
for line in open('_redirects', encoding='utf8'):
    line = line.split('#')[0].strip()
    if not line: continue
    a = line.split()
    rules.append((a[0], a[1], int(a[2]) if len(a) > 2 else 302))
def match(pat, path):
    rx = '^' + re.escape(pat).replace(r'\*', '(?P<splat>.*)') + '$'
    m = re.match(rx, path)
    return m
def resolve(path):
    """-> ('redirect', target, code) | ('file', filename) | ('404',)"""
    for pat, dst, code in rules:
        m = match(pat, path)
        if m:
            return ('redirect', dst.replace(':splat', m.groupdict().get('splat', '')), code)
    # Pages : /x.html -> 308 /x ; /index -> /
    if path.endswith('.html') and os.path.exists(path[1:]):
        return ('redirect', path[:-5] if path != '/index.html' else '/', 308)
    if path == '/': return ('file', 'index.html')
    if os.path.isfile(path[1:]): return ('file', path[1:])
    if os.path.isfile(path[1:] + '.html'): return ('file', path[1:] + '.html')
    return ('404',)
def fetch(path, maxhops=5):
    chain = [path]
    for _ in range(maxhops):
        r = resolve(path)
        if r[0] == 'redirect':
            path = r[1]; chain.append(path)
            if len(chain) > maxhops: return ('loop', chain)
            continue
        return (r[0], chain, r[1] if r[0] == 'file' else None)
    return ('loop', chain)
def norm(h):
    h = h.split('#')[0]
    if h.startswith(BASE): h = h[len(BASE):] or '/'
    return h.split('?')[0]

class P(HTMLParser):
    def __init__(s): super().__init__(); s.links = []; s.h1 = 0; s.title = ''; s._t = False; s.meta = {}; s.canon = None; s.ld = []; s._ld = False; s.href_attrs = []
    def handle_starttag(s, tag, a):
        a = dict(a)
        if tag == 'a' and 'href' in a: s.links.append(a['href'])
        if tag == 'h1': s.h1 += 1
        if tag == 'title': s._t = True
        if tag == 'meta' and a.get('name') == 'description': s.meta['desc'] = a.get('content', '')
        if tag == 'link' and a.get('rel') == 'canonical': s.canon = a.get('href')
        if tag == 'link' and 'href' in a: s.href_attrs.append(a['href'])
        if tag == 'script' and a.get('type') == 'application/ld+json': s._ld = True; s.ld.append('')
    def handle_endtag(s, tag):
        if tag == 'title': s._t = False
        if tag == 'script': s._ld = False
    def handle_data(s, d):
        if s._t: s.title += d
        if s._ld: s.ld[-1] += d

pages = sorted(f for f in glob.glob('*.html') if not f.startswith('google') and f != '404.html')
info = {}
for f in pages:
    p = P(); p.feed(open(f, encoding='utf8').read()); info[f] = p
slug = lambda f: '/' if f == 'index.html' else '/' + f[:-5]

# 1. liens internes : 200 direct, sans redirection
graph = collections.defaultdict(set)
for f, p in info.items():
    for h in p.links:
        if h.startswith(('mailto:', 'tel:', '#', 'javascript:')): continue
        if h.startswith('http') and not h.startswith(BASE): continue
        path = norm(h)
        if not path: continue
        if path.endswith('.html'): err(f'{f}: lien en .html -> {h}')
        r = fetch(path)
        if r[0] != 'file': err(f'{f}: lien cassé/boucle {h} {r}')
        elif len(r[1]) > 1: err(f'{f}: lien interne qui redirige {h} -> {r[1]}')
        elif path != slug(r[2]) and not path.endswith(('.pdf', '.png', '.svg', '.xml', '.txt')): err(f'{f}: lien non canonique {h}')
        if path != slug(f): graph[slug(f)].add(path)

# 2. sitemap
sm = open('sitemap.xml', encoding='utf8').read()
locs = re.findall(r'<loc>(.*?)</loc>', sm)
if len(set(locs)) != len(locs): err('sitemap : doublons')
for u in locs:
    if '.html' in u: err(f'sitemap : .html {u}')
    r = fetch(norm(u))
    if r[0] != 'file' or len(r[1]) > 1: err(f'sitemap : URL non finale {u} {r}')
for f in pages:
    if f in ('mentions-legales.html', 'politique-de-confidentialite.html'): continue
    if BASE + (slug(f) if f != 'index.html' else '/') not in locs: err(f'sitemap : {f} absent')
for d in re.findall(r'<lastmod>(.*?)</lastmod>', sm):
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', d): err(f'sitemap lastmod invalide {d}')
for f in ('feed.xml', 'sitemap.xml'):
    if re.search(r'https://assistantjuridique\.ai/[^"<\s]*\.html', open(f, encoding='utf8').read()): err(f'{f} contient une URL .html')

# 3. balises
titles, descs = collections.defaultdict(list), collections.defaultdict(list)
for f, p in info.items():
    t = html.unescape(p.title.strip()); d = html.unescape(p.meta.get('desc', ''))
    if p.h1 != 1: err(f'{f}: {p.h1} <h1>')
    if not t or len(t) > 60: err(f'{f}: title {len(t)} car. > 60 : {t}')
    if not d or len(d) > 155: err(f'{f}: description {len(d)} car. : {d[:50]}')
    titles[t].append(f); descs[d].append(f)
    exp = BASE + slug(f)
    if p.canon != exp: err(f'{f}: canonical {p.canon} != {exp}')
    for blk in p.ld:
        try: json.loads(blk)
        except Exception as e: err(f'{f}: JSON-LD invalide {e}')
    is_art = f[:-5] in {l.strip('/') for l in []}
for k, v in titles.items():
    if len(v) > 1: err(f'titles dupliqués {v}')
for k, v in descs.items():
    if len(v) > 1: err(f'descriptions dupliquées {v}')
ARTS = [f for f in pages if f not in ('index.html', 'about.html', 'articles.html', 'mentions-legales.html', 'politique-de-confidentialite.html')]
for f in ARTS:
    s = open(f, encoding='utf8').read()
    for need in ('"@type": "Article"', '"headline"', '"datePublished"', '"dateModified"', '"author"', 'BreadcrumbList'):
        if need not in s: err(f'{f}: données structurées manquantes {need}')
    body = s.split('<article>')[1]
    rel = re.search(r'<section class="related".*?</section>', body, re.S)
    n_rel = len(re.findall(r'<li>', rel.group(0))) if rel else 0
    if n_rel != 3: err(f'{f}: bloc À lire aussi = {n_rel} liens')
    main = body.split('<section class="related"')[0]
    n_ctx = len({norm(h) for h in re.findall(r'href="(/[^"#]*)"', main) if norm(h)[1:] + '.html' in ARTS and norm(h) != slug(f)})
    if not 2 <= n_ctx <= 3: err(f'{f}: {n_ctx} liens contextuels (attendu 2-3)')

# 4. liens entrants (depuis d'autres articles) + profondeur
inc = collections.Counter()
for f in ARTS:
    for t in graph[slug(f)]:
        if t[1:] + '.html' in ARTS: inc[t] += 1
for f in ARTS:
    if inc[slug(f)] < 2: err(f'{f}: {inc[slug(f)]} lien(s) entrant(s) depuis les articles')
depth = {'/': 0}; q = collections.deque(['/'])
while q:
    u = q.popleft()
    for v in graph[u]:
        if v not in depth: depth[v] = depth[u] + 1; q.append(v)
for f in ARTS:
    d = depth.get(slug(f))
    if d is None or d > 2: err(f'{f}: profondeur {d}')
home = {norm(h) for h in info['index.html'].links}; hub = {norm(h) for h in info['articles.html'].links}
for f in ARTS:
    if slug(f) not in home: err(f'{f}: absent de l\'accueil')
    if slug(f) not in hub: err(f'{f}: absent de /articles')

# 5. redirections
chains = []
for pat, dst, code in rules:
    if '*' in pat: continue
    r = fetch(pat)
    if r[0] != 'file' or len(r[1]) != 2: err(f'redirection {pat}: {r}')
    chains.append((pat, r[1][-1]))
for f in ARTS + ['about.html']:   # /x.html -> /x en 1 saut
    r = fetch('/' + f)
    if r[0] != 'file' or len(r[1]) != 2 or r[1][1] != slug(f): err(f'/{f}: {r}')
r = fetch('/index.html')
if r[1] != ['/index.html', '/']: err(f'/index.html: {r}')
print('Pages:', len(pages), '| liens internes testés OK | redirections:', len(chains), '| erreurs:', len(errors))
sys.exit(1 if errors else 0)
