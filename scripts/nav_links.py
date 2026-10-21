#!/usr/bin/env python3
"""Ajoute le lien « Tous les articles » (pied de page, menu, accueil). Idempotent."""
import glob, os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FOOT_OLD = '&nbsp;·&nbsp; <a href="/mentions-legales"'
for f in glob.glob('*.html'):
    if f.startswith('google') or f in ('articles.html', '404.html'): continue
    s = open(f, encoding='utf8').read(); o = s
    if '<a href="/articles" style="color:inherit">' not in s and FOOT_OLD in s:
        s = s.replace(FOOT_OLD, '&nbsp;·&nbsp; <a href="/articles" style="color:inherit">Tous les articles</a> ' + FOOT_OLD, 1)
    if f == 'index.html':
        s = s.replace('<nav><a href="#articles">Articles</a>', '<nav><a href="/articles">Tous les articles</a>')
        if 'Voir la liste complète par thème' not in s:
            s = s.replace('  <h2>Tous les articles</h2>\n', '  <h2>Tous les articles</h2>\n  <p style="margin-bottom:1.5rem"><a href="/articles" style="color:var(--accent);font-weight:600">Voir la liste complète par thème →</a></p>\n', 1)
    if s != o: open(f, 'w', encoding='utf8').write(s)
