#!/usr/bin/env python3
"""Génère articles.html (page « Tous les articles ») à partir des pages existantes."""
import re, html, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
sys.path.insert(0, 'scripts')
import seo_apply as S
BASE = 'https://assistantjuridique.ai'
THEMES = [
 ('RGPD et données personnelles', ['rgpd-pme-obligations','checklist-rgpd-pme-10-points','registre-traitements-rgpd-pme','protection-donnees-rh-pme','cgv-mentions-legales-rgpd-ia']),
 ('Signature électronique', ['signature-electronique-valeur-juridique','signature-electronique-quel-niveau-par-contrat']),
 ('Contrats et documents juridiques', ['ia-juridique-rediger-contrats','contrat-freelance-ia','bail-commercial-ia','ia-rediger-statuts-societe','sous-traitance-responsabilite-clauses']),
 ('Facturation et paiement', ['facturation-electronique-pme-obligations-2026','delais-de-paiement-entre-entreprises-penalites','mise-en-demeure-de-payer-injonction-de-payer']),
 ('IA et ressources humaines', ['taches-juridiques-ia-assistant-rh','licenciement-ia-avocat']),
 ('IA juridique : outils, limites et coûts', ['limites-ia-juridique','outils-ia-juridiques-2025','pme-reduire-facture-juridique-ia','ia-avocats-facturer-moins-cher']),
]
TITLE = 'Tous les articles : RGPD, contrats, facturation, IA'
DESC = "Les 21 articles d'AssistantJuridique.ai classés par thème : RGPD, signature électronique, contrats, facturation et paiement, IA et RH."
assert sum(len(t[1]) for t in THEMES) == len(S.ARTICLES) and set(sum((t[1] for t in THEMES), [])) == set(S.ARTICLES)
src = open('index.html', encoding='utf8').read()
def css(): 
    m = re.search(r'<style>(.*?)</style>', src, re.S).group(1)
    return m
extra = re.search(r'<style id="seo-extra">(.*?)</style>', src, re.S).group(1)
tail = re.findall(r'\n<style>\n\.nl-inline.*?</style>', src, re.S)
items = []
ld_items = []
for ti, (name, slugs) in enumerate(THEMES):
    items.append('  <h2 class="theme">%s</h2>\n  <div class="article-list">' % html.escape(name, quote=False))
    for sl in slugs:
        s = S.rd(sl + '.html')
        h1 = re.search(r'<h1>(.*?)</h1>', s, re.S).group(1).strip()
        d = re.search(r'<meta name="description" content="(.*?)"', s).group(1)
        items.append('    <a href="/%s" class="article-item">\n      <span class="article-text"><span class="article-title">%s</span><span class="article-desc">%s</span></span>\n      <span class="article-arrow">→</span>\n    </a>' % (sl, h1, d))
        ld_items.append('{"@type": "ListItem", "position": %d, "url": "%s/%s"}' % (len(ld_items) + 1, BASE, sl))
    items.append('  </div>')
page = f'''<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(TITLE, quote=False)}</title>
  <meta name="description" content="{html.escape(DESC)}" />
  <link rel="canonical" href="{BASE}/articles" />
  <link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;800&family=Inter:wght@400;500&display=swap" rel="stylesheet" />
  <style>{css()}
    .theme {{ font-family: 'Syne', sans-serif; font-size: 1.15rem; font-weight: 700; color: var(--heading); margin: 2.5rem 0 1rem; }}
    .page-hero {{ max-width: 760px; margin: 4rem auto 2rem; padding: 0 2rem; }}
    .page-hero h1 {{ font-family: 'Syne', sans-serif; font-size: clamp(1.8rem, 4.5vw, 2.5rem); font-weight: 800; color: var(--heading); line-height: 1.15; letter-spacing: -0.03em; margin-bottom: 1rem; }}
  </style>
  <meta property="og:type" content="website" />
  <meta property="og:locale" content="fr_FR" />
  <meta property="og:site_name" content="AssistantJuridique.ai" />
  <meta property="og:title" content="{html.escape(TITLE)}" />
  <meta property="og:description" content="{html.escape(DESC)}" />
  <meta property="og:url" content="{BASE}/articles" />
  <meta name="twitter:card" content="summary" />
  <meta name="twitter:title" content="{html.escape(TITLE)}" />
  <meta name="twitter:description" content="{html.escape(DESC)}" />
  <script type="application/ld+json">[{{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Tous les articles", "description": "{DESC}", "url": "{BASE}/articles", "inLanguage": "fr-FR", "mainEntity": {{"@type": "ItemList", "itemListElement": [{", ".join(ld_items)}]}}}}, {{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{{"@type": "ListItem", "position": 1, "name": "Accueil", "item": "{BASE}/"}}, {{"@type": "ListItem", "position": 2, "name": "Tous les articles", "item": "{BASE}/articles"}}]}}]</script>
  <style id="seo-extra">{extra}</style>
  <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
  <link rel="icon" href="/favicon-32.png" type="image/png" sizes="32x32" />
  <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
  <meta name="theme-color" content="#f7f6f2" />
  <meta property="og:image" content="{BASE}/og-image.png" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <meta name="twitter:image" content="{BASE}/og-image.png" />
  <link rel="alternate" type="application/rss+xml" title="AssistantJuridique.ai" href="{BASE}/feed.xml" />
  <meta name="robots" content="index,follow,max-image-preview:large" />
</head>
<body>
<header>
  <a href="/" class="logo">assistant<span>juridique</span>.ai</a>
  <nav><a href="/">Accueil</a><a href="/articles">Tous les articles</a><a href="/#newsletter">Newsletter</a></nav>
</header>
<div class="page-hero">
  <h1>Tous les articles</h1>
  <p class="subtitle" style="color:var(--muted)">Les {len(S.ARTICLES)} articles d'AssistantJuridique.ai, classés par thème : RGPD, signature électronique, contrats, facturation et paiement, IA et RH.</p>
</div>
<div class="articles" id="articles">
{chr(10).join(items)}
</div>
<div class="disclaimer">Le contenu de ce site est fourni à titre informatif uniquement et ne constitue pas un conseil juridique.</div>
<footer><p>© 2026 AssistantJuridique.ai — Tous droits réservés &nbsp;·&nbsp; <a href="/articles" style="color:inherit">Tous les articles</a> &nbsp;·&nbsp; <a href="/mentions-legales" style="color:inherit">Mentions légales</a> &nbsp;·&nbsp; <a href="/politique-de-confidentialite" style="color:inherit">Confidentialité</a></p></footer>
</body>
</html>
'''
open('articles.html', 'w', encoding='utf8').write(page)
print('articles.html OK')
