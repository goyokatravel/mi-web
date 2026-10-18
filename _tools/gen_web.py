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


def is_transport(p):
    return (p.get("name") or "").lstrip().startswith(TRANSPORT) or p.get("category") == "Transport"


def country_of(it):
    dest = it.get("destination") or ""
    return dest.split(",")[-1].strip() or dest


def city_of(p):
    return (p.get("address") or "").split(",")[0].strip()


def money(n, cur):
    if n in (None, 0):
        return ""
    n = int(n) if float(n).is_integer() else n
    return f"~{n} {cur or '€'}/persona"


def h1_html(title):
    m = re.search(r"\b(en \d+ (?:días|dias|semanas|day|days))", title)
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
        credit = (f'<figcaption>Foto: <a href="{e(link)}" rel="noopener nofollow" target="_blank">{e(it["photo_credit"])}</a>'
                  f' en <a href="https://unsplash.com" rel="noopener nofollow" target="_blank">Unsplash</a></figcaption>')
    return f'<figure class="hero-photo"><img src="{e(it["photo"])}" alt="{e(it.get("destination") or it["title"])}" loading="eager">{credit}</figure>'


def page(it, extra):
    slug = it["slug"]
    url = f"{BASE}/itinerarios/{slug}"
    days = it.get("days") or []
    nplans = sum(len(d.get("plans") or []) for d in days)
    flag = it.get("country_flag") or ""
    desc = (extra.get("description") or it.get("description") or "").strip()
    meta_desc = desc if len(desc) > 60 else f"{it['title']}: plan día a día para viajar en grupo, con mapa, horarios y consejos."

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
                                name=p["name"], time=p.get("time") or ""))

    def plan_html(p):
        t = e(p.get("time") or "")
        price = f'<span class="price">{e(int(p["price"]) if float(p["price"]).is_integer() else p["price"])} {e(p.get("currency") or "€")}</span>' if p.get("price") else ""
        note = f'<p class="note">{e(p["note"])}</p>' if p.get("note") else ""
        if is_transport(p):
            return f'<li class="plan transport"><span class="time">{t}</span><div class="pbody"><h4>{e(p["name"])}</h4>{note}</div></li>'
        city = city_of(p)
        cat = CAT.get(p.get("category"), p.get("category") or "")
        return (f'<li class="plan"><span class="time">{t}</span><div class="pbody">'
                f'<h4>{e(p["name"])}</h4>'
                f'<p class="where">{e(city)}{" " if city else ""}<span class="cat">{e(cat)}</span>{price}</p>{note}</div></li>')

    days_html = "".join(
        f'<section class="day" id="dia-{d["day"]}"><div class="dayhead"><span class="dot" style="background:{DAY_COLORS[i % 7]}"></span>'
        f'<h3>Día {d["day"]}{" · " + e(d["title"]) if d.get("title") else ""}</h3></div>'
        f'{"<p class=daynote>" + e(d["notes"]) + "</p>" if d.get("notes") else ""}'
        f'<ol class="plans">{"".join(plan_html(p) for p in d.get("plans") or [])}</ol></section>'
        for i, d in enumerate(days))
    legend = "".join(f'<button type="button" class="chip" data-day="{i}"><span class="dot" style="background:{DAY_COLORS[i % 7]}"></span>Día {d["day"]}</button>'
                     for i, d in enumerate(days) if any(m["day"] == i for m in markers))
    tips = extra.get("tips") or []
    tips_html = f'<section class="tips"><h2>Consejos para el viaje</h2><ul>{"".join(f"<li>{e(t)}</li>" for t in tips)}</ul></section>' if tips else ""
    facts = [f"{len(days)} días", f"{nplans} planes"]
    if money(it.get("budget_per_person"), it.get("currency")):
        facts.append(money(it.get("budget_per_person"), it.get("currency")))
    if it.get("group_size"):
        facts.append(f"Pensado para {it['group_size']}")
    if extra.get("stay_fact"):
        facts.append(extra["stay_fact"])

    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "TouristTrip", "name": it["title"], "description": meta_desc, "url": url, "inLanguage": "es",
         "touristType": "Grupos de amigos", **({"image": it["photo"]} if it.get("photo") else {}),
         "provider": {"@type": "Organization", "name": "YOKA", "url": BASE + "/"},
         "itinerary": {"@type": "ItemList", "numberOfItems": len(markers), "itemListElement": [
             {"@type": "ListItem", "position": m["n"], "item": {"@type": "TouristAttraction", "name": m["name"],
              "geo": {"@type": "GeoCoordinates", "latitude": m["lat"], "longitude": m["lng"]}}} for m in markers]}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "YOKA", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Itinerarios", "item": BASE + "/itinerarios/"},
            {"@type": "ListItem", "position": 3, "name": it["title"], "item": url}]}]}
    og_img = it.get("photo") or f"{BASE}/og-image.png"

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(it['title'])} · Plan día a día con mapa | YOKA</title>
<meta name="description" content="{e(meta_desc)}">
<link rel="canonical" href="{url}">
<meta name="apple-itunes-app" content="app-id=6808558555">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="192x192" href="/favicon-192.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="theme-color" content="#0174D9">
<meta property="og:type" content="article">
<meta property="og:site_name" content="YOKA">
<meta property="og:locale" content="es_ES">
<meta property="og:title" content="{e(it['title'])} · Plan día a día">
<meta property="og:description" content="{e(meta_desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{e(og_img)}">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bagel+Fat+One&family=Bricolage+Grotesque:opsz,wght@12..96,800&family=Nunito:wght@400;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<link rel="stylesheet" href="/itinerarios/itinerario.css">
</head>
<body>
<nav><a class="brand" href="/">yoka</a><a class="navcta" href="/descarga">Descargar</a></nav>
<main class="wrap">
  <p class="crumbs"><a href="/">YOKA</a> › <a href="/itinerarios/">Itinerarios</a> › {e(country_of(it))}</p>
  {photo_html(it)}
  <h1>{flag + " " if flag else ""}{h1_html(it['title'])}</h1>
  <p class="lead">{e(desc)}</p>
  <div class="facts">{"".join(f"<span>{e(f)}</span>" for f in facts)}</div>

  <div class="open">
    <a class="btn" id="open-in-app" href="/descarga" data-app-path="/itinerarios/{e(slug)}">Ábrelo en YOKA</a>
    <p>Gratis en iPhone (beta en Android). En la app, búscalo en <strong>Explorar → Itinerarios</strong>: «{e(it['title'])}». Cópialo a tu viaje, votad los planes y repartid los gastos.</p>
  </div>

  <div id="map" role="img" aria-label="Mapa con los sitios del itinerario"></div>
  <div class="legend" id="legend">{legend}</div>
  {days_html}
  {tips_html}
  <section class="why">
    <h2>Organizad este viaje en grupo, sin el caos</h2>
    <p>Copiad el plan, cambiad lo que queráis, votad los sitios y llevad las cuentas de quién ha pagado qué.</p>
    <a href="/descarga">Descargar YOKA</a>
  </section>
</main>
<footer>© {datetime.date.today().year} YOKA · <a href="/">goyokatravel.com</a> · <a href="/itinerarios/">Más itinerarios</a> · <a href="/privacidad">Privacidad</a></footer>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<script>window.YOKA_MAP = {json.dumps(dict(markers=markers, colors=DAY_COLORS), ensure_ascii=False)};</script>
<script src="/itinerarios/mapa.js"></script>
</body>
</html>
"""


def card(it):
    photo = (f'<span class="cover" style="background-image:url(\'{e(it["photo"])}\')"></span>' if it.get("photo")
             else f'<span class="cover nophoto"><span>{e(it.get("country_flag") or "🧳")}</span></span>')
    chips = [f"{len(it.get('days') or [])} días"]
    if money(it.get("budget_per_person"), it.get("currency")):
        chips.append(money(it.get("budget_per_person"), it.get("currency")))
    return (f'<a class="card" href="/itinerarios/{e(it["slug"])}" data-region="{e(region(it))}">{photo}<span class="cbody">'
            f'<span class="country">{e(it.get("country_flag") or "")} {e(country_of(it))}</span>'
            f'<h2>{e(it["title"])}</h2><p>{e(it.get("description") or "")}</p>'
            f'<span class="chips">{"".join(f"<span>{e(c)}</span>" for c in chips)}</span>'
            f'<span class="cta">Ver el plan →</span></span></a>')


def region(it):
    return "escapada" if len(it.get("days") or []) <= 5 else "ruta"


def index(items):
    escapadas = [i for i in items if region(i) == "escapada"]
    rutas = [i for i in items if region(i) == "ruta"]
    ld = {"@context": "https://schema.org", "@type": "ItemList", "name": "Itinerarios de YOKA",
          "itemListElement": [{"@type": "ListItem", "position": n + 1, "url": f"{BASE}/itinerarios/{i['slug']}", "name": i["title"]}
                              for n, i in enumerate(items)]}
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Itinerarios para viajar con amigos · Planes día a día | YOKA</title>
<meta name="description" content="{len(items)} itinerarios día a día para viajar en grupo: escapadas de fin de semana y grandes rutas, con mapa, horarios, presupuesto y consejos.">
<link rel="canonical" href="{BASE}/itinerarios/">
<meta name="apple-itunes-app" content="app-id=6808558555">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="192x192" href="/favicon-192.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="theme-color" content="#0174D9">
<meta property="og:type" content="website">
<meta property="og:site_name" content="YOKA">
<meta property="og:title" content="Itinerarios para viajar con amigos · YOKA">
<meta property="og:description" content="Planes día a día con mapa, horarios y presupuesto. Ábrelos en YOKA y organizadlos en grupo.">
<meta property="og:url" content="{BASE}/itinerarios/">
<meta property="og:image" content="{BASE}/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bagel+Fat+One&family=Bricolage+Grotesque:opsz,wght@12..96,800&family=Nunito:wght@400;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/itinerarios/itinerario.css">
</head>
<body class="index">
<nav><a class="brand" href="/">yoka</a><a class="navcta" href="/descarga">Descargar</a></nav>
<main class="wrap wide">
  <h1>Itinerarios para viajar <mark>con amigos</mark></h1>
  <p class="lead">Planes día a día con mapa, horarios, presupuesto y los trucos de quien ya ha ido. Ábrelos en YOKA, copiadlos a vuestro viaje y cambiad lo que queráis.</p>
  <div class="filters"><button type="button" class="chip on" data-f="todos">Todos ({len(items)})</button><button type="button" class="chip" data-f="escapada">Escapadas ({len(escapadas)})</button><button type="button" class="chip" data-f="ruta">Grandes rutas ({len(rutas)})</button></div>
  <div class="grid" id="grid">{"".join(card(i) for i in items)}</div>
  <section class="why">
    <h2>En la app hay muchos más</h2>
    <p>Busca en Explorar → Itinerarios y sigue a tus amigos para robarles las mejores ideas.</p>
    <a href="/descarga">Descargar YOKA</a>
  </section>
</main>
<footer>© {datetime.date.today().year} YOKA · <a href="/">goyokatravel.com</a> · <a href="/privacidad">Privacidad</a></footer>
<script>
document.querySelectorAll('.filters .chip').forEach(function(b){{
  b.addEventListener('click', function(){{
    document.querySelectorAll('.filters .chip').forEach(function(x){{ x.classList.toggle('on', x===b); }});
    document.querySelectorAll('#grid .card').forEach(function(c){{ c.hidden = b.dataset.f!=='todos' && c.dataset.region!==b.dataset.f; }});
  }});
}});
</script>
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
        open(f"{OUT}/{i['slug']}.html", "w", encoding="utf-8").write(page(i, extras.get(i["slug"], {})))
    open(f"{OUT}/index.html", "w", encoding="utf-8").write(index(items))
    update_sitemap(items)
    print(f"ok: {len(items)} itinerarios")


if __name__ == "__main__":
    main()
