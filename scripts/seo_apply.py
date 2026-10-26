#!/usr/bin/env python3
"""Applique les corrections SEO (balises, maillage, redirections). Idempotent."""
import re, glob, html, sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
H = html.escape
def rd(f): return open(f, encoding='utf8').read()
def wr(f, s): open(f, 'w', encoding='utf8').write(s)

# ---------- 1. Titres / descriptions (<=60 / <=155) ----------
META = {
 'bail-commercial-ia': ("Analyser un bail commercial avec l'IA : test et limites", None),
 'cgv-mentions-legales-rgpd-ia': ("CGV et mentions légales : les générer avec l'IA (RGPD)", None),
 'checklist-rgpd-pme-10-points': (None, "Checklist RGPD pour PME : les 7 étapes de la CNIL en 10 points concrets (fichiers, durées de conservation, registre, droits, sécurité)."),
 'contrat-freelance-ia': ("Contrat de freelance rédigé par IA : clauses à vérifier", None),
 'delais-de-paiement-entre-entreprises-penalites': ("Délais de paiement entre entreprises : pénalités de retard", "Délais de paiement entre entreprises : 60 jours ou 45 jours fin de mois, pénalités de retard, indemnité de 40 € et sanctions. Les règles officielles."),
 'facturation-electronique-pme-obligations-2026': ("Facturation électronique PME : calendrier et obligations", "Facturation électronique des PME : réception obligatoire depuis le 1er septembre 2026, émission en 2027. Calendrier et plan d'action."),
 'mise-en-demeure-de-payer-injonction-de-payer': ("Facture impayée : mise en demeure et injonction de payer", "Facture impayée : mise en demeure, injonction de payer et nouveau délai de 3 mois depuis septembre 2026. La marche à suivre pas à pas."),
 'protection-donnees-rh-pme': ("Données RH et RGPD en PME : ce qu'il faut savoir", "RGPD et RH en PME : quelles données collecter sur les salariés, comment les protéger et comment l'IA peut aider à rester conforme."),
 'registre-traitements-rgpd-pme': ("Registre des traitements RGPD PME : qui, quand, comment", "Registre des traitements RGPD : l'exception des moins de 250 salariés, le contenu d'une fiche et le modèle simplifié de la CNIL pour les PME."),
 'signature-electronique-quel-niveau-par-contrat': ("Niveau de signature électronique par contrat : le guide", "Niveau de signature électronique par contrat : simple, avancée ou qualifiée (eIDAS), valeur juridique et niveau adapté selon le document."),
 'sous-traitance-responsabilite-clauses': ("Sous-traitance : clauses de responsabilité que l'IA oublie", None),
 'about': (None, "AssistantJuridique.ai : newsletter hebdomadaire sur l'IA juridique pour TPE et PME. Ce que l'IA peut faire, ce qu'elle ne peut pas faire, sans jargon."),
}
LEGAL_DESC = {
 'mentions-legales': "Mentions légales d'AssistantJuridique.ai : éditeur, hébergeur, propriété intellectuelle et contact.",
 'politique-de-confidentialite': "Politique de confidentialité d'AssistantJuridique.ai : données collectées, finalités, durées de conservation et droits RGPD.",
}
BASE = 'https://assistantjuridique.ai'

def set_meta(slug, s, new_t, new_d):
    old_t = html.unescape(re.search(r'<title>(.*?)</title>', s, re.S).group(1).strip())
    m = re.search(r'<meta name="description" content="(.*?)"', s)
    old_d = html.unescape(m.group(1)) if m else None
    if new_t:
        for pat in (old_t, H(old_t), H(old_t, quote=False)):
            s = s.replace(pat, H(new_t, quote=False)) if False else s
        s = re.sub(r'<title>.*?</title>', '<title>%s</title>' % H(new_t, quote=False), s, count=1, flags=re.S)
        s = re.sub(r'(<meta property="og:title" content=")[^"]*', lambda m: m.group(1) + H(new_t), s)
        s = re.sub(r'(<meta name="twitter:title" content=")[^"]*', lambda m: m.group(1) + H(new_t), s)
    if new_d:
        s = re.sub(r'(<meta name="description" content=")[^"]*', lambda m: m.group(1) + H(new_d), s, count=1)
        s = re.sub(r'(<meta property="og:description" content=")[^"]*', lambda m: m.group(1) + H(new_d), s)
        s = re.sub(r'(<meta name="twitter:description" content=")[^"]*', lambda m: m.group(1) + H(new_d), s)
        if old_d:
            s = s.replace('"description": "%s"' % old_d.replace('"', '\\"'), '"description": "%s"' % new_d.replace('"', '\\"'))
    return s

# ---------- 2. Maillage ----------
ARTICLES = ['rgpd-pme-obligations','checklist-rgpd-pme-10-points','registre-traitements-rgpd-pme','protection-donnees-rh-pme','cgv-mentions-legales-rgpd-ia',
 'signature-electronique-valeur-juridique','signature-electronique-quel-niveau-par-contrat','ia-juridique-rediger-contrats','contrat-freelance-ia','bail-commercial-ia',
 'ia-rediger-statuts-societe','sous-traitance-responsabilite-clauses','delais-de-paiement-entre-entreprises-penalites','mise-en-demeure-de-payer-injonction-de-payer',
 'facturation-electronique-pme-obligations-2026','taches-juridiques-ia-assistant-rh','licenciement-ia-avocat','limites-ia-juridique','outils-ia-juridiques-2025',
 'pme-reduire-facture-juridique-ia','ia-avocats-facturer-moins-cher','rupture-conventionnelle-procedure-indemnite-cout']
RELATED = {
 'rgpd-pme-obligations': ['checklist-rgpd-pme-10-points','registre-traitements-rgpd-pme','protection-donnees-rh-pme'],
 'checklist-rgpd-pme-10-points': ['registre-traitements-rgpd-pme','rgpd-pme-obligations','cgv-mentions-legales-rgpd-ia'],
 'registre-traitements-rgpd-pme': ['checklist-rgpd-pme-10-points','rgpd-pme-obligations','protection-donnees-rh-pme'],
 'protection-donnees-rh-pme': ['rgpd-pme-obligations','registre-traitements-rgpd-pme','licenciement-ia-avocat'],
 'cgv-mentions-legales-rgpd-ia': ['rgpd-pme-obligations','delais-de-paiement-entre-entreprises-penalites','ia-juridique-rediger-contrats'],
 'signature-electronique-valeur-juridique': ['signature-electronique-quel-niveau-par-contrat','contrat-freelance-ia','ia-juridique-rediger-contrats'],
 'signature-electronique-quel-niveau-par-contrat': ['signature-electronique-valeur-juridique','contrat-freelance-ia','bail-commercial-ia'],
 'ia-juridique-rediger-contrats': ['signature-electronique-quel-niveau-par-contrat','contrat-freelance-ia','ia-rediger-statuts-societe'],
 'contrat-freelance-ia': ['sous-traitance-responsabilite-clauses','ia-juridique-rediger-contrats','signature-electronique-quel-niveau-par-contrat'],
 'bail-commercial-ia': ['ia-juridique-rediger-contrats','ia-rediger-statuts-societe','signature-electronique-quel-niveau-par-contrat'],
 'ia-rediger-statuts-societe': ['ia-juridique-rediger-contrats','bail-commercial-ia','sous-traitance-responsabilite-clauses'],
 'sous-traitance-responsabilite-clauses': ['contrat-freelance-ia','rgpd-pme-obligations','ia-juridique-rediger-contrats'],
 'delais-de-paiement-entre-entreprises-penalites': ['mise-en-demeure-de-payer-injonction-de-payer','facturation-electronique-pme-obligations-2026','cgv-mentions-legales-rgpd-ia'],
 'mise-en-demeure-de-payer-injonction-de-payer': ['delais-de-paiement-entre-entreprises-penalites','facturation-electronique-pme-obligations-2026','cgv-mentions-legales-rgpd-ia'],
 'facturation-electronique-pme-obligations-2026': ['delais-de-paiement-entre-entreprises-penalites','mise-en-demeure-de-payer-injonction-de-payer','pme-reduire-facture-juridique-ia'],
 'taches-juridiques-ia-assistant-rh': ['licenciement-ia-avocat','protection-donnees-rh-pme','rupture-conventionnelle-procedure-indemnite-cout'],
 'licenciement-ia-avocat': ['taches-juridiques-ia-assistant-rh','protection-donnees-rh-pme','rupture-conventionnelle-procedure-indemnite-cout'],
 'rupture-conventionnelle-procedure-indemnite-cout': ['licenciement-ia-avocat','protection-donnees-rh-pme','taches-juridiques-ia-assistant-rh'],
 'limites-ia-juridique': ['outils-ia-juridiques-2025','pme-reduire-facture-juridique-ia','ia-avocats-facturer-moins-cher'],
 'outils-ia-juridiques-2025': ['limites-ia-juridique','taches-juridiques-ia-assistant-rh','pme-reduire-facture-juridique-ia'],
 'pme-reduire-facture-juridique-ia': ['outils-ia-juridiques-2025','ia-avocats-facturer-moins-cher','taches-juridiques-ia-assistant-rh'],
 'ia-avocats-facturer-moins-cher': ['pme-reduire-facture-juridique-ia','limites-ia-juridique','outils-ia-juridiques-2025'],
}
# Liens contextuels souhaités (3 max par article, existants inclus)
INLINE = {
 'rupture-conventionnelle-procedure-indemnite-cout': ['protection-donnees-rh-pme','taches-juridiques-ia-assistant-rh'],
 'rgpd-pme-obligations': ['protection-donnees-rh-pme','registre-traitements-rgpd-pme','checklist-rgpd-pme-10-points'],
 'checklist-rgpd-pme-10-points': ['rgpd-pme-obligations','cgv-mentions-legales-rgpd-ia','registre-traitements-rgpd-pme'],
 'registre-traitements-rgpd-pme': ['checklist-rgpd-pme-10-points','rgpd-pme-obligations','protection-donnees-rh-pme'],
 'protection-donnees-rh-pme': ['rgpd-pme-obligations','registre-traitements-rgpd-pme','checklist-rgpd-pme-10-points'],
 'cgv-mentions-legales-rgpd-ia': ['rgpd-pme-obligations','checklist-rgpd-pme-10-points','delais-de-paiement-entre-entreprises-penalites'],
 'signature-electronique-valeur-juridique': ['signature-electronique-quel-niveau-par-contrat','contrat-freelance-ia','ia-juridique-rediger-contrats'],
 'signature-electronique-quel-niveau-par-contrat': ['ia-juridique-rediger-contrats','signature-electronique-valeur-juridique','bail-commercial-ia'],
 'ia-juridique-rediger-contrats': ['signature-electronique-valeur-juridique','contrat-freelance-ia','limites-ia-juridique'],
 'contrat-freelance-ia': ['signature-electronique-quel-niveau-par-contrat','sous-traitance-responsabilite-clauses','ia-avocats-facturer-moins-cher'],
 'bail-commercial-ia': ['ia-juridique-rediger-contrats','ia-rediger-statuts-societe','limites-ia-juridique'],
 'ia-rediger-statuts-societe': ['ia-juridique-rediger-contrats','bail-commercial-ia','limites-ia-juridique'],
 'sous-traitance-responsabilite-clauses': ['contrat-freelance-ia','ia-juridique-rediger-contrats','rgpd-pme-obligations'],
 'delais-de-paiement-entre-entreprises-penalites': ['cgv-mentions-legales-rgpd-ia','mise-en-demeure-de-payer-injonction-de-payer','facturation-electronique-pme-obligations-2026'],
 'mise-en-demeure-de-payer-injonction-de-payer': ['delais-de-paiement-entre-entreprises-penalites','facturation-electronique-pme-obligations-2026','cgv-mentions-legales-rgpd-ia'],
 'facturation-electronique-pme-obligations-2026': ['cgv-mentions-legales-rgpd-ia','delais-de-paiement-entre-entreprises-penalites','mise-en-demeure-de-payer-injonction-de-payer'],
 'taches-juridiques-ia-assistant-rh': ['licenciement-ia-avocat','protection-donnees-rh-pme','outils-ia-juridiques-2025'],
 'licenciement-ia-avocat': ['taches-juridiques-ia-assistant-rh','protection-donnees-rh-pme','limites-ia-juridique'],
 'limites-ia-juridique': ['ia-avocats-facturer-moins-cher','outils-ia-juridiques-2025','pme-reduire-facture-juridique-ia'],
 'outils-ia-juridiques-2025': ['limites-ia-juridique','taches-juridiques-ia-assistant-rh','pme-reduire-facture-juridique-ia'],
 'pme-reduire-facture-juridique-ia': ['outils-ia-juridiques-2025','ia-avocats-facturer-moins-cher','taches-juridiques-ia-assistant-rh'],
 'ia-avocats-facturer-moins-cher': ['pme-reduire-facture-juridique-ia','limites-ia-juridique','outils-ia-juridiques-2025'],
}
Q = r"(?:'|’|&#x27;|&#39;)"
PHRASES = {
 'registre-traitements-rgpd-pme': r"registre des (?:activités de )?traitements",
 'checklist-rgpd-pme-10-points': r"check-?list(?: RGPD)?",
 'rgpd-pme-obligations': r"obligations (?:du )?RGPD|conformité (?:au )?RGPD|mise en conformité",
 'protection-donnees-rh-pme': r"données RH|données (?:personnelles )?des salariés",
 'cgv-mentions-legales-rgpd-ia': r"conditions générales de vente|CGV",
 'delais-de-paiement-entre-entreprises-penalites': r"délais de paiement|pénalités de retard",
 'mise-en-demeure-de-payer-injonction-de-payer': r"mise en demeure|injonction de payer|factures? impayées?",
 'facturation-electronique-pme-obligations-2026': r"facturation électronique|facture électronique",
 'signature-electronique-valeur-juridique': r"signature électronique",
 'signature-electronique-quel-niveau-par-contrat': r"signature (?:électronique )?(?:simple|avancée|qualifiée)|niveaux? de signature",
 'contrat-freelance-ia': r"contrats? de freelance|freelances?",
 'ia-juridique-rediger-contrats': r"rédiger (?:vos |des |un )?contrats?|rédaction de contrats?|contrats? commerciaux?",
 'bail-commercial-ia': r"bail commercial|baux commerciaux",
 'ia-rediger-statuts-societe': r"statuts de société|statuts",
 'sous-traitance-responsabilite-clauses': r"contrats? de sous-traitance|sous-traitance|sous-traitants?",
 'limites-ia-juridique': r"limites de l"+Q+r"IA(?: juridique)?",
 'outils-ia-juridiques-2025': r"outils (?:d"+Q+r"IA|IA)(?: juridiques)?|outils juridiques",
 'pme-reduire-facture-juridique-ia': r"facture juridique|coûts? juridiques?|frais juridiques?",
 'ia-avocats-facturer-moins-cher': r"honoraires d(?:"+Q+r")avocats?|cabinets? d(?:"+Q+r")avocats?",
 'licenciement-ia-avocat': r"licenciements?",
 'taches-juridiques-ia-assistant-rh': r"tâches juridiques",
}
SHORT = {
 'registre-traitements-rgpd-pme': 'le registre des traitements RGPD en PME',
 'checklist-rgpd-pme-10-points': 'la checklist RGPD pour PME en 10 points',
 'rgpd-pme-obligations': 'les obligations RGPD des PME',
 'protection-donnees-rh-pme': 'la protection des données RH en PME',
 'cgv-mentions-legales-rgpd-ia': 'les CGV et mentions légales générées avec l'+"'"+'IA',
 'delais-de-paiement-entre-entreprises-penalites': 'les délais de paiement et pénalités de retard entre entreprises',
 'mise-en-demeure-de-payer-injonction-de-payer': 'la mise en demeure et l'+"'"+'injonction de payer',
 'facturation-electronique-pme-obligations-2026': 'les obligations de facturation électronique des PME',
 'signature-electronique-valeur-juridique': 'la valeur juridique de la signature électronique',
 'signature-electronique-quel-niveau-par-contrat': 'le niveau de signature électronique à choisir par contrat',
 'contrat-freelance-ia': 'le contrat de freelance rédigé par IA',
 'ia-juridique-rediger-contrats': 'la rédaction de contrats par l'+"'"+'IA juridique',
 'bail-commercial-ia': 'l'+"'"+'analyse d'+"'"+'un bail commercial par l'+"'"+'IA',
 'ia-rediger-statuts-societe': 'la rédaction de statuts de société par l'+"'"+'IA',
 'sous-traitance-responsabilite-clauses': 'les clauses de responsabilité en sous-traitance',
 'limites-ia-juridique': 'les limites de l'+"'"+'IA juridique',
 'outils-ia-juridiques-2025': 'le comparatif des outils IA juridiques',
 'pme-reduire-facture-juridique-ia': 'comment réduire sa facture juridique avec l'+"'"+'IA',
 'ia-avocats-facturer-moins-cher': 'l'+"'"+'IA et la facturation des avocats',
 'licenciement-ia-avocat': 'la procédure de licenciement et le rôle de l'+"'"+'IA',
 'taches-juridiques-ia-assistant-rh': 'les tâches juridiques que l'+"'"+'IA automatise',
}
def h1_of(slug):
    return re.search(r'<h1>(.*?)</h1>', rd(slug + '.html'), re.S).group(1).strip()

def article_body_span(s):
    a = s.index('<article>'); b = s.index('<section class="related"')
    return a, b

def own_links(seg):
    return set(l.strip('/') for l in re.findall(r'href="(/[^"#?]*)"', seg))

def add_inline(slug, s, report):
    a, b = article_body_span(s)
    body = s[a:b]
    have = [t for t in own_links(body) if t in ARTICLES and t != slug]
    want = [t for t in INLINE[slug] if t != slug]
    need = [t for t in want if t not in have]
    n_have = len(have)
    for t in need:
        if n_have >= 3: break
        rx = re.compile(PHRASES[t], re.I)
        done = False
        # paragraphes <p>, hors .disclaimer/.cta-box/.nl-inline/.sig-type
        for pm in re.finditer(r'<(p|li)(?: [^>]*)?>(.*?)</\1>', body, re.S):
            pre = body[:pm.start()]
            if (pre.count('<div') != pre.count('</div>')): continue
            inner = pm.group(2)
            parts = re.split(r'(<a\b.*?</a>|<[^>]+>)', inner, flags=re.S)
            inlink = False
            for i, p in enumerate(parts):
                if p.startswith('<a'): continue
                if p.startswith('<'): continue
                m = rx.search(p)
                if m:
                    parts[i] = p[:m.start()] + '<a href="/%s">%s</a>' % (t, m.group(0)) + p[m.end():]
                    new_inner = ''.join(parts)
                    body = body[:pm.start(2)] + new_inner + body[pm.end(2):]
                    done = True; report.append((slug, t, 'ancre: ' + m.group(0))); break
            if done: break
        if not done:
            # repli : phrase courte en fin de 2e paragraphe d'article
            ps = [pm for pm in re.finditer(r'<(p)(?: [^>]*)?>(.*?)</\1>', body, re.S)
                  if body[:pm.start()].count('<div') == body[:pm.start()].count('</div>')]
            pm = ps[min(1 + n_have, len(ps) - 1)]
            tpl = ('Pour approfondir, lisez notre article sur', 'Sur ce point, voir aussi notre article sur', 'À ce sujet, consultez notre article sur')[sum(map(ord, slug + t)) % 3]
            ins = ' %s <a href="/%s">%s</a>.' % (tpl, t, H(SHORT[t], quote=False))
            body = body[:pm.end(2)] + ins + body[pm.end(2):]
            report.append((slug, t, 'REPLI phrase'))
        n_have += 1
    return s[:a] + body + s[b:]

def related_block(slug):
    lis = ''.join('<li><a href="/%s">%s</a></li>' % (t, h1_of(t)) for t in RELATED[slug])
    return '<section class="related" aria-label="À lire aussi"><h2>À lire aussi</h2><ul>%s</ul></section>' % lis

NAV_OLD_ARTICLE = '<nav><a href="/">Accueil</a><a href="/#newsletter">Newsletter</a></nav>'
NAV_NEW_ARTICLE = '<nav><a href="/">Accueil</a><a href="/articles">Tous les articles</a><a href="/#newsletter">Newsletter</a></nav>'

def main():
    report = []
    for slug in ARTICLES:
        f = slug + '.html'; s = rd(f)
        t, d = META.get(slug, (None, None))
        if t or d: s = set_meta(slug, s, t, d)
        if slug in RELATED:
            s = add_inline(slug, s, report)
            s = re.sub(r'<section class="related".*?</section>', lambda m: related_block(slug), s, flags=re.S)
        s = s.replace(NAV_OLD_ARTICLE, NAV_NEW_ARTICLE)
        wr(f, s)
    # about
    s = rd('about.html'); s = set_meta('about', s, *META['about']); wr('about.html', s)
    # pages légales : description + canonical
    for slug, d in LEGAL_DESC.items():
        s = rd(slug + '.html')
        if 'name="description"' not in s:
            s = s.replace('<meta name="robots"', '<meta name="description" content="%s"><link rel="canonical" href="%s/%s"><meta name="robots"' % (H(d), BASE, slug), 1)
        wr(slug + '.html', s)
    for r in report: print(*r)

if __name__ == '__main__':
    main()
