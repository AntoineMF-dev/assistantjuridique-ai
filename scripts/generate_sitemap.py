#!/usr/bin/env python3
"""Génère sitemap.xml : URL finales (sans .html), lastmod exact.
 - articles : dateModified du JSON-LD de la page ;
 - autres pages : date du dernier commit git du fichier (ou date du jour si modifié et non commité).
Usage : python3 scripts/generate_sitemap.py"""
import re, glob, os, subprocess, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
BASE = 'https://assistantjuridique.ai'
EXCLUDE = {'mentions-legales', 'politique-de-confidentialite'}  # pages légales: non listées (comme avant)
def git_date(f):
    dirty = subprocess.run(['git', 'status', '--porcelain', '--', f], capture_output=True, text=True).stdout.strip()
    if dirty: return datetime.date.today().isoformat()
    out = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', f], capture_output=True, text=True).stdout.strip()
    return out or datetime.date.today().isoformat()
rows = []
for f in sorted(glob.glob('*.html')):
    slug = f[:-5]
    if f.startswith('google') or slug in EXCLUDE or slug == '404': continue
    s = open(f, encoding='utf8').read()
    m = re.search(r'"@type": ?"Article".*?"dateModified": ?"(\d{4}-\d{2}-\d{2})"', s, re.S)
    last = m.group(1) if m else git_date(f)
    if slug == 'index': url, pr, cf = BASE + '/', '1.0', 'weekly'
    elif slug == 'articles': url, pr, cf = BASE + '/articles', '0.9', 'weekly'
    elif slug == 'about': url, pr, cf = BASE + '/about', '0.5', 'monthly'
    else: url, pr, cf = f'{BASE}/{slug}', '0.8', 'monthly'
    rows.append((url, last, cf, pr))
order = lambda r: (0 if r[0] == BASE + '/' else 1 if r[0].endswith('/articles') else 3 if r[0].endswith('/about') else 2, r[0])
rows.sort(key=order)
xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for u, l, c, p in rows:
    xml.append(f'  <url>\n    <loc>{u}</loc>\n    <lastmod>{l}</lastmod>\n    <changefreq>{c}</changefreq>\n    <priority>{p}</priority>\n  </url>')
xml.append('</urlset>')
open('sitemap.xml', 'w', encoding='utf8').write('\n'.join(xml) + '\n')
print(len(rows), 'URL écrites dans sitemap.xml')
