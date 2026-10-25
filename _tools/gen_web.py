"""Genera las páginas de itinerarios de goyokatravel.com a partir de los datos de la app.

Entrada: _tools/data/web_itineraries.json (lo que devuelve la función web_itineraries() de Supabase)
         _tools/itinerarios/extras.json (opcional: consejos y textos extra escritos a mano, por slug)
Salida:  itinerarios/<slug>.html, itinerarios/index.html y las entradas de itinerarios en sitemap.xml

Uso (desde la raíz de mi-web): python3 _tools/gen_web.py
"""
import datetime, glob, html, json, os, re

BASE = "https://www.goyokatravel.com"
DATA = "_tools/data/web_itineraries.json"
EXTRAS = "_tools/itinerarios/extras.json"
OUT = "itinerarios"

CAT = {"Activities": "Plan", "Sights": "Qué ver", "Restaurants": "Comer", "Museums": "Museo",
       "Nightlife": "Noche", "Shopping": "Compras", "Nature": "Naturaleza", "Bars": "Bar",
       "Cafés": "Café", "Parks": "Naturaleza", "Transport": "Transporte"}
TRANSPORT = ("🚆", "🚐", "✈", "🚄", "🚌", "⛴", "🚗", "🚂", "🛳", "🚇", "🚢", "🚕", "🛺", "🚠", "🚡")
DAY_COLORS = ["#0174D9", "#FF6B57", "#14213D", "#1D9E75", "#9B51E0", "#E6A100", "#D4537E"]
e = lambda s: html.escape(str(s) if s is not None else "", quote=True)
CAT_EN = {"Activities": "Plan", "Sights": "Sights", "Restaurants": "Food", "Museums": "Museum", "Nightlife": "Nightlife",
          "Shopping": "Shopping", "Nature": "Nature", "Bars": "Bar", "Cafés": "Café", "Parks": "Nature", "Transport": "Transport"}
COUNTRY_EN = {"Brasil y Argentina": "Brazil and Argentina", "Chequia": "Czechia", "España": "Spain", "Francia": "France",
              "Hungría": "Hungary", "Islandia": "Iceland", "Italia": "Italy", "Japón": "Japan", "Marruecos": "Morocco",
              "México": "Mexico", "Países Bajos": "Netherlands", "Perú": "Peru", "Reino Unido": "United Kingdom",
              "Tailandia": "Thailand", "Uzbekistán": "Uzbekistan"}


def _load(folder):
    out = {}
    for f in sorted(glob.glob(f"_tools/itinerarios/{folder}/*.json")):
        out.update(json.load(open(f, encoding="utf-8")))
    return out


TR_EN = _load("en")   # textos de la app en español → inglés
TR_ES = _load("es")   # textos de la app en inglés → español (p. ej. Nueva York)


def es_of(s):
    return TR_ES.get(s, s) if s else s


def en_of(s):
    return TR_EN.get(s, s) if s else s


def tx(s, tag="span", cls=""):
    """Texto que viene de la app, en los dos idiomas."""
    return t(es_of(s), en_of(s), tag, cls) if s else ""


def t(es, en, tag="span", cls=""):
    """Texto que cambia con el botón ES/EN."""
    c = f' class="{cls}"' if cls else ""
    return f'<{tag}{c} data-es="{e(es)}" data-en="{e(en)}">{e(es)}</{tag}>'


LANG_UI = '''<div class="lang-switch"><button type="button" data-lang="es" class="active">ES</button><button type="button" data-lang="en">EN</button></div>'''
LANG_JS = '''<script>
(function(){
  function setLang(l){
    document.documentElement.lang = l;
    document.querySelectorAll('[data-' + l + ']').forEach(function(el){ el.textContent = el.getAttribute('data-' + l); });
    document.querySelectorAll('.lang-switch button').forEach(function(b){ b.classList.toggle('active', b.dataset.lang === l); });
    document.querySelectorAll('a.js-lang').forEach(function(a){ a.href = a.getAttribute('href').split('?')[0] + (l === 'en' ? '?lang=en' : ''); });
    if (window.YOKA_ON_LANG) window.YOKA_ON_LANG(l);
  }
  document.querySelectorAll('.lang-switch button').forEach(function(b){ b.addEventListener('click', function(){ setLang(b.dataset.lang); try { sessionStorage.setItem('yoka_lang_visita', b.dataset.lang); } catch (err) {} }); });
  try { localStorage.removeItem('yoka_lang'); } catch (err) {}
  var l = new URLSearchParams(location.search).get('lang');
  try { l = l || sessionStorage.getItem('yoka_lang_visita'); } catch (err) {}
  if (l !== 'es' && l !== 'en') l = /^(es|ca|gl|eu)\\b/i.test(navigator.language || 'es') ? 'es' : 'en';
  if (l === 'en') setLang('en');
})();
</script>'''


def is_transport(p):
    return (p.get("name") or "").lstrip().startswith(TRANSPORT) or p.get("category") == "Transport"


def country_of(it):
    dest = it.get("destination") or ""
    return dest.split(",")[-1].strip() or dest


def city_of(p):
    return (p.get("address") or "").split(",")[0].strip()


def money(n, cur, en=False):
    if n in (None, 0):
        return ""
    n = int(n) if float(n).is_integer() else n
    return f"~{n} {cur or '€'}/" + ("person" if en else "persona")


def money_t(it):
    a = money(it.get("budget_per_person"), it.get("currency"))
    return t(a, money(it.get("budget_per_person"), it.get("currency"), True)) if a else ""


def h1_both(title):
    return (f'<span class="l-es">{h1_html(es_of(title))}</span>'
            f'<span class="l-en">{h1_html(en_of(title))}</span>')


def h1_html(title):
    m = re.search(r"\b((?:en|in) \d+ (?:días|dias|semanas|days|weeks)|en un finde|in a weekend)", title)
    if not m:
        return e(title)
    a, b = title[:m.start()], m.group(1)
    return f"{e(a)}<mark>{e(b)}</mark>{e(title[m.end():])}"


def photo_html(it):
    if not it.get("photo"):
        return ""
    credit = ""
    if it.get("photo_credit"):
        link = it.get("photo_credit_url") or "https://unsplash.com"
        credit = (f'<figcaption>{t("Foto", "Photo")}: <a href="{e(link)}" rel="noopener nofollow" target="_blank">{e(it["photo_credit"])}</a>'
                  f' {t("en", "on")} <a href="https://unsplash.com" rel="noopener nofollow" target="_blank">Unsplash</a></figcaption>')
    return f'<figure class="hero-photo"><img src="{e(it["photo"])}" alt="{e(it.get("destination") or it["title"])}" loading="eager">{credit}</figure>'


def country_t(it):
    c = country_of(it)
    return t(c, COUNTRY_EN.get(c, c))


def head(title, desc, url, og_img, ld, og_type="website", extra_css=""):
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta name="apple-itunes-app" content="app-id=6808558555">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="192x192" href="/favicon-192.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="theme-color" content="#0174D9">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="YOKA">
<meta property="og:locale" content="es_ES">
<meta property="og:locale:alternate" content="en_US">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{e(og_img)}">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bagel+Fat+One&family=Bricolage+Grotesque:opsz,wght@12..96,800&family=Baloo+2:wght@500;600;700;800&family=Nunito:wght@400;600;700;800&display=swap" rel="stylesheet">
{extra_css}<link rel="stylesheet" href="/site-nav.css">
<link rel="stylesheet" href="/itinerarios/itinerario.css">
<script data-goatcounter="https://goyokatravel.goatcounter.com/count"
        async src="//gc.zgo.at/count.js"></script>
</head>"""


NAV = """<div class="nav-wrap">
<nav>
  <a href="/" class="brand js-lang">yoka</a>
  <div class="nav-links">
    <a class="js-lang" href="/como-funciona.html" data-es="Cómo funciona" data-en="How it works">Cómo funciona</a>
    <a class="js-lang" href="/sobre-nosotros.html" data-es="Sobre nosotros" data-en="About us">Sobre nosotros</a>
    <a class="js-lang current" href="/itinerarios/" data-es="Itinerarios" data-en="Itineraries">Itinerarios</a>
    <a class="js-lang" href="/faq.html" data-es="FAQ" data-en="FAQ">FAQ</a>
    <a class="js-lang" href="/contacto.html" data-es="Contacto" data-en="Contact">Contacto</a>
  </div>
  <div class="nav-right">
    <div class="lang-toggle">
      <div class="lang-switch"><button type="button" class="active" data-lang="es">ES</button><button type="button" data-lang="en">EN</button></div>
      <div class="store-badges nav-stores">
        <a href="https://apps.apple.com/es/app/yoka-viaja-con-amigos/id6808558555" target="_blank" rel="noopener" class="store-badge" aria-label="Descargar YOKA en la App Store" data-goatcounter-click="clic-app-store">
          <svg viewBox="0 0 24 24" class="store-icon" fill="currentColor"><path d="M16.7 12.4c0-2.5 2-3.7 2.1-3.8-1.1-1.7-2.9-1.9-3.5-1.9-1.5-.2-2.9.9-3.7.9-.8 0-1.9-.9-3.2-.8-1.6 0-3.1.9-4 2.4-1.7 3-.4 7.4 1.2 9.8.8 1.2 1.8 2.5 3 2.5 1.2 0 1.7-.8 3.1-.8 1.4 0 1.8.8 3.1.8 1.3 0 2.1-1.2 2.9-2.3.9-1.3 1.3-2.6 1.3-2.7-.1 0-2.3-.9-2.3-3.6M14.5 5c.7-.8 1.1-2 1-3.1-1 0-2.2.7-2.9 1.5-.6.7-1.2 1.9-1 3 1.1.1 2.2-.6 2.9-1.4"/></svg>
          <span class="store-text"><span class="store-name">iPhone</span></span>
        </a>
        <a href="/android.html" class="store-badge" aria-label="Probar YOKA en Android (beta cerrada en Google Play)" data-goatcounter-click="clic-android-beta">
          <svg viewBox="0 0 24 24" class="store-icon" fill="currentColor"><path d="M3.6 2.2c-.4.4-.6.9-.6 1.6v16.4c0 .7.2 1.2.6 1.6l.1.1L13 12.5v-.1L3.7 2.1l-.1.1M16.3 15.8l-3-3v-.1l3-3 3.6 2c1 .6 1 1.5 0 2.1l-3.6 2M4.3 21.4 14 12.5l2.3 2.3-11.4 6.5c-.2.1-.4.1-.6.1M14 11.5 4.3 2.6c.2 0 .4 0 .6.1L16.3 9.2 14 11.5"/></svg>
          <span class="store-text"><span class="store-name">Android</span></span>
        </a>
      </div>
    </div>
    <button class="nav-toggle" type="button" onclick="toggleNav()" aria-label="Abrir menú" aria-expanded="false" id="navToggleBtn">
      <span></span><span></span><span></span>
    </button>
  </div>
</nav>
<div class="nav-menu" id="navMenu">
  <div class="nav-links-mobile">
    <a class="js-lang" href="/como-funciona.html" data-es="Cómo funciona" data-en="How it works">Cómo funciona</a>
    <a class="js-lang" href="/sobre-nosotros.html" data-es="Sobre nosotros" data-en="About us">Sobre nosotros</a>
    <a class="js-lang current" href="/itinerarios/" data-es="Itinerarios" data-en="Itineraries">Itinerarios</a>
    <a class="js-lang" href="/faq.html" data-es="FAQ" data-en="FAQ">FAQ</a>
    <a class="js-lang" href="/contacto.html" data-es="Contacto" data-en="Contact">Contacto</a>
  </div>
</div>
</div>
<div class="nav-backdrop" id="navBackdrop" onclick="toggleNav()"></div>
<script>
function toggleNav(){
  var menu = document.getElementById('navMenu'), btn = document.getElementById('navToggleBtn'), bd = document.getElementById('navBackdrop');
  var isOpen = menu.classList.toggle('open');
  btn.classList.toggle('open', isOpen); bd.classList.toggle('open', isOpen);
  btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  document.body.style.overflow = isOpen ? 'hidden' : '';
}
</script>"""


def footer(extra_links=""):
    return (f'<footer>© {datetime.date.today().year} YOKA · <a class="js-lang" href="/">goyokatravel.com</a>{extra_links}'
            f' · <a class="js-lang" href="/guias/">{t("Guías", "Guides")}</a>'
            f' · <a class="js-lang" href="/privacidad">{t("Privacidad", "Privacy")}</a></footer>')


def seo_title(title_es):
    """Título para Google: lo que la gente busca («qué ver», «itinerario») sin pasarse de largo."""
    if ":" in title_es:
        return f"{title_es} · Itinerario | YOKA"
    return f"{title_es}: qué ver, itinerario y mapa | YOKA"


def seo_desc(it, desc, title_es, ndays):
    """Descripción para Google (unos 155 caracteres): resumen + qué trae la página."""
    extra = f"Itinerario de {ndays} {'día' if ndays == 1 else 'días'} con mapa, horarios"
    extra += ", presupuesto y consejos." if it.get("budget_per_person") else " y consejos."
    base = es_of(desc).split(". Presupuesto")[0].rstrip(".") + "." if desc else f"{title_es}."
    full = f"{base} {extra}"
    if len(full) <= 160:
        return full
    cut = full[:157]
    return cut[:cut.rfind(" ")].rstrip(",.;:") + "…"


def related(it, items, n=3):
    """Itinerarios parecidos para enlazar: primero del mismo país, luego del mismo tipo (escapada o ruta)."""
    others = [i for i in items if i["slug"] != it["slug"]]
    same_country = [i for i in others if country_of(i) == country_of(it)]
    same_kind = [i for i in others if region(i) == region(it) and i not in same_country]
    # para que no salgan siempre los mismos, empezamos en un punto distinto según la página
    k = sum(map(ord, it["slug"]))
    if same_kind:
        k %= len(same_kind)
        same_kind = same_kind[k:] + same_kind[:k]
    return (same_country + same_kind + others)[:n]


def related_html(it, items):
    rel = related(it, items)
    if not rel:
        return ""
    return (f'<section class="related">{t("Itinerarios parecidos", "Similar itineraries", "h2")}'
            f'<div class="grid">{"".join(card(i) for i in rel)}</div></section>')


def page(it, extra, all_items=()):
    slug = it["slug"]
    url = f"{BASE}/itinerarios/{slug}"
    days = it.get("days") or []
    nplans = sum(len(d.get("plans") or []) for d in days)
    flag = it.get("country_flag") or ""
    desc = (extra.get("description") or it.get("description") or "").strip()
    title_es = es_of(it["title"])
    meta_desc = seo_desc(it, desc, title_es, len(days))

    markers, seen = [], {}
    for di, d in enumerate(days):
        for p in d.get("plans") or []:
            if is_transport(p) or p.get("lat") is None:
                continue
            key = (p["name"], round(float(p["lat"]), 4), round(float(p["lng"]), 4))
            if key in seen:
                continue
            seen[key] = len(seen) + 1
            markers.append(dict(n=seen[key], lat=float(p["lat"]), lng=float(p["lng"]), day=di,
                                name=es_of(p["name"]), name_en=en_of(p["name"]), time=p.get("time") or ""))

    def plan_html(p):
        tm = e(p.get("time") or "")
        price = (f'<span class="price">{e(int(p["price"]) if float(p["price"]).is_integer() else p["price"])} {e(p.get("currency") or "€")}</span>'
                 if p.get("price") else "")
        note = tx(p.get("note"), "p", "note")
        if is_transport(p):
            return f'<li class="plan transport"><span class="time">{tm}</span><div class="pbody">{tx(p["name"], "h4")}{note}</div></li>'
        city = city_of(p)
        cat = p.get("category") or ""
        cat_html = t(CAT.get(cat, cat), CAT_EN.get(cat, cat))
        return (f'<li class="plan"><span class="time">{tm}</span><div class="pbody">'
                f'{tx(p["name"], "h4")}'
                f'<p class="where">{tx(city)}{" " if city else ""}<span class="cat">{cat_html}</span>{price}</p>{note}</div></li>')

    def day_title(d):
        r_es = f' · {es_of(d["title"])}' if d.get("title") else ""
        r_en = f' · {en_of(d["title"])}' if d.get("title") else ""
        return t(f'Día {d["day"]}{r_es}', f'Day {d["day"]}{r_en}', "h3")

    days_html = "".join(
        f'<section class="day" id="dia-{d["day"]}"><div class="dayhead"><span class="dot" style="background:{DAY_COLORS[i % 7]}"></span>'
        f'{day_title(d)}</div>'
        f'{tx(d.get("notes"), "p", "daynote")}'
        f'<ol class="plans">{"".join(plan_html(p) for p in d.get("plans") or [])}</ol></section>'
        for i, d in enumerate(days))
    legend = "".join(f'<button type="button" class="chip" data-day="{i}"><span class="dot" style="background:{DAY_COLORS[i % 7]}"></span>'
                     f'{t("Día " + str(d["day"]), "Day " + str(d["day"]))}</button>'
                     for i, d in enumerate(days) if any(m["day"] == i for m in markers))

    tips_es = extra.get("tips") or []
    tips_en = extra.get("tips_en") or tips_es
    tips_html = ""
    if tips_es:
        items = "".join(t(a, b, "li") for a, b in zip(tips_es, tips_en))
        tips_html = f'<section class="tips">{t("Consejos para el viaje", "Travel tips", "h2")}<ul>{items}</ul></section>'

    facts = [t(f"{len(days)} días", f"{len(days)} days"), t(f"{nplans} planes", f"{nplans} plans")]
    if money_t(it):
        facts.append(money_t(it))
    if it.get("group_size"):
        facts.append(t(f"Pensado para {it['group_size']}", f"Made for {it['group_size']}"))
    if extra.get("stay_fact"):
        facts.append(t(extra["stay_fact"], extra.get("stay_fact_en") or extra["stay_fact"]))

    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "TouristTrip", "name": title_es, "description": meta_desc, "url": url, "inLanguage": "es",
         "touristType": "Grupos de amigos", **({"image": it["photo"]} if it.get("photo") else {}),
         "provider": {"@type": "Organization", "name": "YOKA", "url": BASE + "/"},
         "itinerary": {"@type": "ItemList", "numberOfItems": len(markers), "itemListElement": [
             {"@type": "ListItem", "position": m["n"], "item": {"@type": "TouristAttraction", "name": m["name"],
              "geo": {"@type": "GeoCoordinates", "latitude": m["lat"], "longitude": m["lng"]}}} for m in markers]}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "YOKA", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Itinerarios", "item": BASE + "/itinerarios/"},
            {"@type": "ListItem", "position": 3, "name": title_es, "item": url}]}]}

    open_es = (f"Gratis en iPhone (beta en Android). En la app, búscalo en Explorar → Itinerarios: «{it['title']}». "
               "Cópialo a tu viaje, votad los planes y repartid los gastos.")
    open_en = (f"Free on iPhone (beta on Android). In the app, find it in Explore → Itineraries: “{it['title']}” ({en_of(it['title'])}). "
               if en_of(it['title']) != it['title'] else
               f"Free on iPhone (beta on Android). In the app, find it in Explore → Itineraries: “{it['title']}”. "
               "Copy it to your trip, vote on the plans and split the costs.")

    return head(seo_title(title_es), meta_desc, url, it.get("photo") or f"{BASE}/og-image.png", ld, "article",
                '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">\n') + f"""
<body>
{NAV}
<main class="wrap">
  <p class="crumbs"><a class="js-lang" href="/">YOKA</a> › <a class="js-lang" href="/itinerarios/">{t("Itinerarios", "Itineraries")}</a> › {country_t(it)}</p>
  {photo_html(it)}
  <h1>{flag + " " if flag else ""}{h1_both(it['title'])}</h1>
  {tx(desc, "p", "lead")}
  <div class="facts">{"".join(facts)}</div>

  <div class="openapp">
    <a class="btn js-lang" id="open-in-app" href="/descarga" data-app-path="/itinerarios/{e(slug)}">{t("Ábrelo en YOKA", "Open it in YOKA")}</a>
    {t(open_es, open_en, "p")}
  </div>

  <div id="map" role="img" aria-label="Mapa / Map"></div>
  <div class="legend" id="legend">{legend}</div>
  {days_html}
  {tips_html}
  <section class="why">
    {t("Organizad este viaje en grupo, sin el caos", "Plan this trip as a group, without the chaos", "h2")}
    {t("Copiad el plan, cambiad lo que queráis, votad los sitios y llevad las cuentas de quién ha pagado qué.", "Copy the plan, change whatever you like, vote on places and keep track of who paid for what.", "p")}
    <a class="js-lang" href="/descarga">{t("Descargar YOKA", "Download YOKA")}</a>
  </section>
  {related_html(it, all_items)}
</main>
{footer(" · <a class='js-lang' href='/itinerarios/'>" + t("Más itinerarios", "More itineraries") + "</a>")}
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<script>window.YOKA_MAP = {json.dumps(dict(markers=markers, colors=DAY_COLORS), ensure_ascii=False)};</script>
<script src="/itinerarios/mapa.js"></script>
{LANG_JS}
</body>
</html>
"""


def card(it):
    photo = (f'<span class="cover" style="background-image:url(\'{e(it["photo"])}\')"></span>' if it.get("photo")
             else f'<span class="cover nophoto"><span>{e(it.get("country_flag") or "🧳")}</span></span>')
    n = len(it.get("days") or [])
    chips = [t(f"{n} días", f"{n} days")]
    if money_t(it):
        chips.append(money_t(it))
    return (f'<a class="card js-lang" href="/itinerarios/{e(it["slug"])}" data-region="{e(region(it))}">{photo}<span class="cbody">'
            f'<span class="country">{e(it.get("country_flag") or "")} {country_t(it)}</span>'
            f'{tx(it["title"], "h2")}{tx(it.get("description") or "", "p")}'
            f'<span class="chips">{"".join(chips)}</span>'
            f'<span class="cta">{t("Ver el plan →", "See the plan →")}</span></span></a>')


def region(it):
    return "escapada" if len(it.get("days") or []) <= 5 else "ruta"


def index(items):
    escapadas = [i for i in items if region(i) == "escapada"]
    rutas = [i for i in items if region(i) == "ruta"]
    ld = {"@context": "https://schema.org", "@type": "ItemList", "name": "Itinerarios de YOKA",
          "itemListElement": [{"@type": "ListItem", "position": n + 1, "url": f"{BASE}/itinerarios/{i['slug']}", "name": i["title"]}
                              for n, i in enumerate(items)]}
    desc = (f"{len(items)} itinerarios día a día para viajar en grupo: escapadas de fin de semana y grandes rutas, "
            "con mapa, horarios, presupuesto y consejos.")
    h1 = ('<h1><span data-es="Itinerarios para viajar" data-en="Itineraries to travel">Itinerarios para viajar</span> '
          '<mark data-es="con amigos" data-en="with friends">con amigos</mark></h1>')
    return head("Itinerarios para viajar con amigos · Planes día a día | YOKA", desc, f"{BASE}/itinerarios/", f"{BASE}/og-image.png", ld) + f"""
<body class="index">
{NAV}
<main class="wrap wide">
  {h1}
  {t("Planes día a día con mapa, horarios, presupuesto y los trucos de quien ya ha ido. Ábrelos en YOKA, copiadlos a vuestro viaje y cambiad lo que queráis.",
     "Day-by-day plans with a map, times, budget and tips from people who've been there. Open them in YOKA, copy them to your trip and change whatever you like.", "p", "lead")}
  <div class="filters"><button type="button" class="chip on" data-f="todos">{t(f"Todos ({len(items)})", f"All ({len(items)})")}</button><button type="button" class="chip" data-f="escapada">{t(f"Escapadas ({len(escapadas)})", f"Short breaks ({len(escapadas)})")}</button><button type="button" class="chip" data-f="ruta">{t(f"Grandes rutas ({len(rutas)})", f"Big trips ({len(rutas)})")}</button></div>
  <div class="grid" id="grid">{"".join(card(i) for i in items)}</div>
  <section class="why">
    {t("En la app hay muchos más", "There are many more in the app", "h2")}
    {t("Busca en Explorar → Itinerarios y sigue a tus amigos para robarles las mejores ideas.", "Search in Explore → Itineraries and follow your friends to steal their best ideas.", "p")}
    <a class="js-lang" href="/descarga">{t("Descargar YOKA", "Download YOKA")}</a>
  </section>
</main>
{footer()}
<script>
document.querySelectorAll('.filters .chip').forEach(function(b){{
  b.addEventListener('click', function(){{
    document.querySelectorAll('.filters .chip').forEach(function(x){{ x.classList.toggle('on', x===b); }});
    document.querySelectorAll('#grid .card').forEach(function(c){{ c.hidden = b.dataset.f!=='todos' && c.dataset.region!==b.dataset.f; }});
  }});
}});
</script>
{LANG_JS}
</body>
</html>
"""


def update_sitemap(items):
    path = "sitemap.xml"
    s = open(path, encoding="utf-8").read()
    s = re.sub(r"  <url><loc>https://www\.goyokatravel\.com/itinerarios/[^<]*</loc>.*?</url>\n", "", s)
    today = datetime.date.today().isoformat()
    block = f"  <url><loc>{BASE}/itinerarios/</loc><lastmod>{today}</lastmod><priority>0.8</priority></url>\n" + "".join(
        f"  <url><loc>{BASE}/itinerarios/{i['slug']}</loc><lastmod>{today}</lastmod><priority>0.7</priority></url>\n" for i in items)
    s = s.replace("</urlset>", block + "</urlset>")
    open(path, "w", encoding="utf-8").write(s)


def main():
    raw = json.load(open(DATA, encoding="utf-8"))
    if isinstance(raw, list) and raw and isinstance(raw[0], dict) and "web_itineraries" in raw[0]:
        raw = raw[0]["web_itineraries"]
        if isinstance(raw, str):
            raw = json.loads(raw)
    items = [i for i in raw if i.get("slug") and i.get("days")]
    # orden: primero las escapadas cortas, luego las rutas largas; dentro, alfabético
    items.sort(key=lambda i: (len(i["days"]) > 5, i["title"].lower()))
    extras = json.load(open(EXTRAS, encoding="utf-8")) if os.path.exists(EXTRAS) else {}

    keep = {f"{OUT}/{i['slug']}.html" for i in items} | {f"{OUT}/index.html"}
    for old in glob.glob(f"{OUT}/*.html"):  # quita las páginas de itinerarios que ya no están marcados
        if old not in keep:
            os.remove(old)
    for i in items:
        open(f"{OUT}/{i['slug']}.html", "w", encoding="utf-8").write(page(i, extras.get(i["slug"], {}), items))
    open(f"{OUT}/index.html", "w", encoding="utf-8").write(index(items))
    update_sitemap(items)
    print(f"ok: {len(items)} itinerarios")


if __name__ == "__main__":
    main()
