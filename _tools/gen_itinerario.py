"""Genera una página de itinerario de la web de YOKA a partir de un demo en Markdown.

Uso: python3 gen_itinerario.py demo.md meta.json salida.html
"""
import html, json, re, sys

BASE = "https://www.goyokatravel.com"
CAT = {"Sights": "Qué ver", "Restaurants": "Comer", "Museums": "Museo", "Nightlife": "Noche",
       "Shopping": "Compras", "Bars": "Bar", "Cafés": "Café", "Transport": "Transporte",
       "Nature": "Naturaleza", "Beaches": "Playa", "Activities": "Plan", "Hotels": "Hotel"}
DAY_COLORS = ["#0174D9", "#FF6B57", "#14213D", "#1D9E75", "#9B51E0", "#E6A100", "#D4537E"]
e = lambda s: html.escape(s or "", quote=True)


def rows(block):
    out = []
    for line in block.splitlines():
        line = line.strip()
        if not line.startswith("|") or set(line) <= set("|-: "):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        out.append(cells)
    return out[1:]  # quita cabecera


def parse(md):
    sites_block = re.search(r"## SITIOS.*?\n(.*?)\n## ", md, re.S).group(1)
    sites = {}
    city = ""
    for line in sites_block.splitlines():
        h = re.match(r"###\s+(.+)", line.strip())
        if h:
            city = h.group(1).strip(); continue
        for c in rows("|h|\n" + line):
            if not c[0].isdigit():
                continue
            if len(c) >= 8:   # con columna Zona
                n, name, cat, zone, lat, lng, st, note = c[:8]
            else:             # viajes por etapas: la zona es la ciudad del bloque
                n, name, cat, lat, lng, st, note = c[:7]; zone = city
            sites[int(n)] = dict(n=int(n), name=name, cat=cat, zone=zone, lat=float(lat), lng=float(lng),
                                 stars=int(st) if st.isdigit() else None, note=note)
    days = []
    for m in re.finditer(r"### (Día \d+) · (.*?)\n(.*?)(?=\n### |\Z)", md, re.S):
        plans = []
        for c in rows(m.group(3)):
            ref = re.search(r"\((\d+)\)\s*$", c[2])
            plans.append(dict(time=c[0], plan=c[1], site=sites.get(int(ref.group(1))) if ref else None,
                              label=c[2], note=c[3] if len(c) > 3 else ""))
        days.append(dict(label=m.group(1), title=m.group(2).strip(), plans=plans))
    return sites, days


def build(md, meta):
    sites, days = parse(md)
    used = {p["site"]["n"] for d in days for p in d["plans"] if p["site"]}
    extra = [s for n, s in sites.items() if n not in used]
    nplans = sum(len(d["plans"]) for d in days)
    url = f"{BASE}/itinerarios/{meta['slug']}"
    title = f"{meta['title']} con amigos: plan día a día y mapa | YOKA"

    markers = []
    for di, d in enumerate(days):
        for p in d["plans"]:
            s = p["site"]
            if s:
                markers.append(dict(lat=s["lat"], lng=s["lng"], day=di, name=s["name"], plan=p["plan"], time=p["time"]))

    def plan_html(p):
        s = p["site"]
        if s:
            notes = " ".join((x if x.rstrip()[-1:] in ".!?" else x.rstrip() + ".") for x in [p["note"], s["note"]] if x)
            return f"""
        <li class="plan">
          <span class="time">{e(p['time'])}</span>
          <div class="pbody">
            <h4>{e(p['plan'])}</h4>
            <p class="where"><strong>{e(s['name'])}</strong> · {e(s['zone'])} <span class="cat">{e(CAT.get(s['cat'], s['cat']))}</span></p>
            {f'<p class="note">{e(notes)}</p>' if notes else ''}
          </div>
        </li>"""
        return f"""
        <li class="plan transport">
          <span class="time">{e(p['time'])}</span>
          <div class="pbody"><h4>{e(p['plan'])}</h4>{f'<p class="note">{e(p["note"])}</p>' if p['note'] else ''}</div>
        </li>"""

    days_html = "".join(f"""
    <section class="day" id="dia-{i+1}">
      <div class="dayhead"><span class="dot" style="background:{DAY_COLORS[i % 7]}"></span><h3>{e(d['label'])} · {e(d['title'])}</h3></div>
      <ol class="plans">{''.join(plan_html(p) for p in d['plans'])}
      </ol>
    </section>""" for i, d in enumerate(days))

    extra_html = ""
    if extra:
        extra_html = '<section class="extra"><h2>Si os sobra tiempo</h2><ul>' + "".join(
            f"<li><strong>{e(s['name'])}</strong>{'' if s['zone']==s['name'] else ' · ' + e(s['zone'])}. {e(s['note'])}</li>" for s in extra) + "</ul></section>"

    tips_html = "".join(f"<li>{e(t)}</li>" for t in meta["tips"])
    legend = "".join(f'<button type="button" class="chip" data-day="{i}"><span class="dot" style="background:{DAY_COLORS[i % 7]}"></span>{e(d["label"])}</button>'
                     for i, d in enumerate(days))

    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "TouristTrip", "name": meta["title"], "description": meta["description"], "url": url,
             "touristType": "Grupos de amigos", "inLanguage": "es",
             "provider": {"@type": "Organization", "name": "YOKA", "url": BASE + "/"},
             "itinerary": {"@type": "ItemList", "numberOfItems": len(used), "itemListElement": [
                 {"@type": "ListItem", "position": i + 1,
                  "item": {"@type": "TouristAttraction", "name": m["name"],
                           "geo": {"@type": "GeoCoordinates", "latitude": m["lat"], "longitude": m["lng"]}}}
                 for i, m in enumerate({m["name"]: m for m in markers}.values())]}},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "YOKA", "item": BASE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Itinerarios", "item": BASE + "/itinerarios/"},
                {"@type": "ListItem", "position": 3, "name": meta["title"], "item": url}]},
        ],
    }

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(meta['description'])}">
<link rel="canonical" href="{url}">
<meta name="apple-itunes-app" content="app-id=6808558555">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="192x192" href="/favicon-192.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="theme-color" content="#0174D9">
<meta property="og:type" content="article">
<meta property="og:site_name" content="YOKA">
<meta property="og:locale" content="es_ES">
<meta property="og:title" content="{e(meta['title'])} con amigos · Plan día a día">
<meta property="og:description" content="{e(meta['description'])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{json.dumps(ld, ensure_ascii=False, indent=1)}
</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bagel+Fat+One&family=Bricolage+Grotesque:opsz,wght@12..96,800&family=Nunito:wght@400;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<style>
  :root{{--yellow:#FFDC01;--blue:#0174D9;--coral:#FF6B57;--ink:#14213D;--soft:#3A4568;--muted:#5B6478;--bg:#FFFDF7;--card:#FFFFFF;--line:#E9E3CC;--chip:#F4F1E4}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:Nunito,system-ui,sans-serif;color:var(--ink);background:var(--bg);line-height:1.5}}
  a{{color:inherit}}
  h1,h2,h3,h4{{font-family:"Bricolage Grotesque",sans-serif;font-weight:800;letter-spacing:-.01em}}
  nav{{position:sticky;top:0;z-index:1000;display:flex;align-items:center;justify-content:space-between;padding:14px 16px;background:rgba(255,253,247,.92);backdrop-filter:blur(8px);border-bottom:2px solid var(--ink)}}
  .brand{{font-family:"Bagel Fat One",sans-serif;font-size:1.5rem;text-decoration:none;text-transform:uppercase}}
  .navcta{{background:var(--coral);color:#fff;text-decoration:none;font-weight:800;padding:9px 18px;border-radius:100px;font-size:.95rem}}
  .wrap{{max-width:820px;margin:0 auto;padding:0 16px}}
  .crumbs{{font-size:.9rem;color:var(--muted);margin:22px 0 10px}}
  .crumbs a{{text-decoration:none}}
  h1{{font-size:clamp(2rem,6vw,3rem);line-height:1.05;margin-bottom:12px}}
  h1 mark{{background:var(--yellow);padding:0 .15em;border-radius:8px}}
  .lead{{font-size:1.1rem;color:var(--soft);margin-bottom:18px}}
  .facts{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:22px}}
  .facts span{{background:var(--chip);border-radius:100px;padding:6px 12px;font-weight:700;font-size:.9rem}}
  .open{{display:grid;gap:8px;background:var(--blue);color:#fff;border:2px solid var(--ink);border-radius:20px;padding:18px;margin-bottom:28px}}
  .open .btn{{display:block;text-align:center;background:var(--yellow);color:var(--ink);text-decoration:none;font-family:"Bricolage Grotesque",sans-serif;font-weight:800;font-size:1.15rem;border-radius:14px;padding:14px}}
  .open p{{font-size:.95rem;opacity:.95}}
  #map{{height:360px;border:2px solid var(--ink);border-radius:20px;margin-bottom:10px;z-index:1}}
  .legend{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:30px}}
  .chip{{display:inline-flex;align-items:center;gap:6px;font:inherit;font-weight:700;font-size:.9rem;background:var(--card);border:2px solid var(--line);border-radius:100px;padding:6px 12px;cursor:pointer}}
  .chip.on{{border-color:var(--ink)}}
  .dot{{width:12px;height:12px;border-radius:50%;display:inline-block;flex:none}}
  .day{{margin-bottom:30px}}
  .dayhead{{display:flex;align-items:flex-start;gap:10px;margin-bottom:12px}}
  .dayhead .dot{{margin-top:.55em}}
  .dayhead h3{{font-size:1.35rem}}
  .plans{{list-style:none;border-left:3px solid var(--line);margin-left:5px;padding-left:16px;display:grid;gap:10px}}
  .plan{{display:grid;grid-template-columns:52px 1fr;gap:10px;background:var(--card);border:2px solid var(--line);border-radius:16px;padding:12px 14px}}
  .plan.transport{{background:var(--chip);border-style:dashed}}
  .time{{font-weight:800;color:var(--blue)}}
  .plan h4{{font-size:1.02rem;margin-bottom:2px}}
  .where{{font-size:.95rem;color:var(--soft)}}
  .cat{{display:inline-block;font-size:.75rem;font-weight:800;background:var(--chip);border-radius:100px;padding:1px 8px;margin-left:4px;color:var(--muted)}}
  .note{{font-size:.93rem;color:var(--muted);margin-top:4px}}
  .tips,.extra{{background:var(--card);border:2px solid var(--line);border-radius:20px;padding:18px 20px;margin-bottom:24px}}
  .tips h2,.extra h2{{font-size:1.3rem;margin-bottom:8px}}
  .tips ul,.extra ul{{padding-left:18px;display:grid;gap:6px}}
  .why{{background:var(--yellow);border:2px solid var(--ink);border-radius:24px;padding:24px 20px;margin:10px 0 30px;text-align:center}}
  .why h2{{font-size:clamp(1.4rem,4vw,1.9rem);margin-bottom:8px}}
  .why p{{color:var(--soft);margin-bottom:16px}}
  .why a{{display:inline-block;background:var(--ink);color:var(--yellow);text-decoration:none;font-weight:800;border-radius:100px;padding:12px 24px}}
  footer{{text-align:center;font-size:.85rem;color:var(--muted);padding:10px 16px 40px}}
  .num{{width:24px;height:24px;border-radius:50%;color:#fff;font:800 11px/20px Nunito,sans-serif;text-align:center;border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,.35)}}
</style>
</head>
<body>
<nav><a class="brand" href="/">yoka</a><a class="navcta" href="/descarga">Descargar</a></nav>
<main class="wrap">
  <p class="crumbs"><a href="/">YOKA</a> › <a href="/itinerarios/">Itinerarios</a> › {e(meta['country'])}</p>
  <h1>{e(meta['h1_a'])} <mark>{e(meta['h1_b'])}</mark></h1>
  <p class="lead">{e(meta['intro'])}</p>
  <div class="facts">
    <span>{len(days)} días</span><span>{nplans} planes</span><span>{e(meta['budget'])}</span><span>{e(meta['stay_fact'])}</span>
  </div>

  <div class="open">
    <a class="btn" id="open-in-app" href="/descarga" data-app-path="/itinerarios/{e(meta['slug'])}">Ábrelo en YOKA</a>
    <p>Gratis en iPhone (beta en Android). En la app, búscalo en <strong>Explorar → Itinerarios</strong>: «{e(meta['app_name'])}». Cópialo a tu viaje, votad los planes y repartid los gastos.</p>
  </div>

  <div id="map" role="img" aria-label="Mapa con los sitios del itinerario"></div>
  <div class="legend" id="legend">{legend}</div>
{days_html}

  <section class="tips"><h2>Consejos para el viaje</h2><ul>{tips_html}</ul></section>
  {extra_html}

  <section class="why">
    <h2>Organizad este viaje en grupo, sin el caos</h2>
    <p>Copiad el plan, cambiad lo que queráis, votad los sitios y llevad las cuentas de quién ha pagado qué.</p>
    <a href="/descarga">Descargar YOKA</a>
  </section>
</main>
<footer>© 2026 YOKA · <a href="/">goyokatravel.com</a> · <a href="/privacidad">Privacidad</a></footer>

<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<script>
(function(){{
  var M = {json.dumps(markers, ensure_ascii=False)};
  var C = {json.dumps(DAY_COLORS)};
  if (!window.L) return;
  var map = L.map('map', {{scrollWheelZoom:false}});
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{maxZoom:18, attribution:'&copy; OpenStreetMap'}}).addTo(map);
  var groups = {{}}, all = [], seen = {{}};
  M.forEach(function(m){{
    var k = m.name; if (seen[k]) return; seen[k] = 1;
    var n = Object.keys(seen).length;
    var icon = L.divIcon({{className:'', html:'<div class="num" style="background:'+C[m.day % C.length]+'">'+n+'</div>', iconSize:[24,24], iconAnchor:[12,12]}});
    var mk = L.marker([m.lat, m.lng], {{icon:icon}}).bindPopup('<strong>'+m.name+'</strong><br>Día '+(m.day+1)+' · '+m.time+' · '+m.plan);
    (groups[m.day] = groups[m.day] || []).push(mk); all.push(mk); mk.addTo(map);
  }});
  var fitAll = function(){{ map.fitBounds(L.featureGroup(all).getBounds(), {{padding:[24,24]}}); }};
  fitAll();
  var chips = document.querySelectorAll('#legend .chip'), active = null;
  chips.forEach(function(c){{
    c.addEventListener('click', function(){{
      var d = +c.dataset.day;
      chips.forEach(function(x){{ x.classList.remove('on'); }});
      if (active === d) {{ active = null; fitAll(); return; }}
      active = d; c.classList.add('on');
      map.fitBounds(L.featureGroup(groups[d]).getBounds(), {{padding:[30,30], maxZoom:15}});
    }});
  }});
}})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    md = open(sys.argv[1], encoding="utf-8").read()
    meta = json.load(open(sys.argv[2], encoding="utf-8"))
    open(sys.argv[3], "w", encoding="utf-8").write(build(md, meta))
    print("ok", sys.argv[3])
