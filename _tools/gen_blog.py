"""Genera el blog de goyokatravel.com/blog (español e inglés, con el botón ES/EN de la web).

Cada artículo es un JSON en _tools/blog/<slug>.json con:
  slug, date (AAAA-MM-DD), related (slugs de itinerarios),
  es / en: title, h1 (puede llevar <mark>), seo_title, desc, lead,
           sections [[título, html]], yoka (html), faq [[pregunta, respuesta]]
El html de las secciones se escribe a mano: solo <p>, <ul>, <ol>, <li>, <strong>, <a>.

Para publicar un artículo nuevo: añade su JSON y ejecuta (desde la raíz de mi-web)
    python3 _tools/gen_blog.py
Salida: blog/<slug>.html, blog/index.html y sus entradas en sitemap.xml
"""
import datetime, glob, json, os, re, sys

sys.path.insert(0, os.path.dirname(__file__))
import gen_web as W  # noqa: E402

BASE = W.BASE
OUT = "blog"
SRC = "_tools/blog"
e, t = W.e, W.t
CSS = '<link rel="stylesheet" href="/blog/blog.css">\n'
MONTHS = {"es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
          "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]}


def nav():
    """El menú de la web con «Blog» como página actual."""
    s = W.NAV.replace('class="js-lang current"', 'class="js-lang"')
    return s.replace('class="js-lang" href="/blog/"', 'class="js-lang current" href="/blog/"')


def both(es_html, en_html, tag="div"):
    """Bloque con html en los dos idiomas; el CSS enseña el del idioma activo."""
    return f'<{tag} class="l-es">{es_html}</{tag}><{tag} class="l-en">{en_html}</{tag}>'


def date_t(d):
    y, m, day = map(int, d.split("-"))
    return t(f"{day} de {MONTHS['es'][m - 1]} de {y}", f"{MONTHS['en'][m - 1]} {day}, {y}")


def load_posts():
    posts = [json.load(open(f, encoding="utf-8")) for f in glob.glob(f"{SRC}/*.json")]
    return sorted(posts, key=lambda p: (p["date"], p["slug"]), reverse=True)


def sections_html(lang):
    return "".join(f"<section><h2>{e(h)}</h2>{body}</section>" for h, body in lang["sections"])


def faq_html(lang, title):
    items = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in lang["faq"])
    return f"<h2>{title}</h2>{items}"


def post_page(p, items_by_slug, posts):
    es, en = p["es"], p["en"]
    url = f"{BASE}/blog/{p['slug']}"
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BlogPosting", "headline": es["title"], "description": es["desc"], "url": url, "inLanguage": "es",
         "datePublished": p["date"], "dateModified": p.get("updated", p["date"]), "image": f"{BASE}/og-image.png",
         "author": {"@type": "Organization", "name": "YOKA", "url": BASE + "/"},
         "publisher": {"@type": "Organization", "name": "YOKA", "url": BASE + "/",
                       "logo": {"@type": "ImageObject", "url": f"{BASE}/logo-512.png"}}},
        {"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in es["faq"]]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "YOKA", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": BASE + "/blog/"},
            {"@type": "ListItem", "position": 3, "name": es["title"], "item": url}]}]}
    rel = "".join(W.card(items_by_slug[s]) for s in p.get("related", []) if s in items_by_slug)
    rel_html = (f'<section class="related">{t("Itinerarios para inspirarte", "Itineraries to inspire you", "h2")}'
                f'<div class="grid">{rel}</div></section>') if rel else ""
    more = [q for q in posts if q["slug"] != p["slug"]][:3]
    more_html = ""
    if more:
        cards = "".join(post_card(q) for q in more)
        more_html = f'<section class="more-posts">{t("Más del blog", "More from the blog", "h2")}<div class="post-list">{cards}</div></section>'
    return W.head(es["seo_title"], es["desc"], url, f"{BASE}/og-image.png", ld, "article", CSS) + f"""
<body class="blog">
{nav()}
<main class="wrap">
  <p class="crumbs"><a class="js-lang" href="/">YOKA</a> › <a class="js-lang" href="/blog/">Blog</a> › <span class="date">{date_t(p['date'])}</span></p>
  <h1>{both(es['h1'], en['h1'], 'span')}</h1>
  {both(f'<p class="lead">{e(es["lead"])}</p>', f'<p class="lead">{e(en["lead"])}</p>')}
  <article class="post-body">{both(sections_html(es), sections_html(en))}</article>
  <section class="why">
    {t("Todo el viaje en un solo sitio", "The whole trip in one place", "h2")}
    {both(f'<p>{es["yoka"]}</p>', f'<p>{en["yoka"]}</p>')}
    <a class="js-lang" href="/descarga" data-goatcounter-click="clic-descarga-blog">{t("Descargar YOKA gratis", "Download YOKA for free")}</a>
  </section>
  <section class="faq">{both(faq_html(es, "Preguntas frecuentes"), faq_html(en, "FAQ"))}</section>
  {rel_html}
  {more_html}
</main>
{W.footer(" · <a class='js-lang' href='/itinerarios/'>" + t("Itinerarios", "Itineraries") + "</a>")}
{W.LANG_JS}
</body>
</html>
"""


def post_card(p):
    return (f'<a class="post-card js-lang" href="/blog/{p["slug"]}"><span class="date">{date_t(p["date"])}</span>'
            f'{t(p["es"]["title"], p["en"]["title"], "h2")}{t(p["es"]["desc"], p["en"]["desc"], "p")}'
            f'<span class="cta">{t("Leer →", "Read →")}</span></a>')


def index_page(posts):
    url = f"{BASE}/blog/"
    ld = {"@context": "https://schema.org", "@type": "Blog", "name": "Blog de YOKA", "url": url,
          "blogPost": [{"@type": "BlogPosting", "headline": p["es"]["title"], "url": f"{BASE}/blog/{p['slug']}",
                        "datePublished": p["date"]} for p in posts]}
    return W.head("Blog de YOKA · Consejos para viajar con amigos",
                  "Consejos prácticos para viajar en grupo: cómo organizar el viaje, cómo dividir los gastos, qué llevar en la maleta y más.",
                  url, f"{BASE}/og-image.png", ld, "website", CSS) + f"""
<body class="blog">
{nav()}
<main class="wrap">
  <p class="crumbs"><a class="js-lang" href="/">YOKA</a> › Blog</p>
  <h1>{both('El blog de <mark>YOKA</mark>', 'The <mark>YOKA</mark> blog', 'span')}</h1>
  {t("Consejos para organizar viajes con amigos sin agobios: el plan, las cuentas, la maleta y todo lo demás.",
     "Tips for planning trips with friends without the stress: the plan, the money, the packing and everything else.", "p", "lead")}
  <div class="post-list">{"".join(post_card(p) for p in posts)}</div>
  <section class="why">
    {t("¿Buscáis destino?", "Looking for a destination?", "h2")}
    {t("Tenemos itinerarios día a día con mapa, horarios y presupuesto.", "We have day-by-day itineraries with a map, times and budget.", "p")}
    <a class="js-lang" href="/itinerarios/">{t("Ver itinerarios", "See itineraries")}</a>
  </section>
</main>
{W.footer(" · <a class='js-lang' href='/itinerarios/'>" + t("Itinerarios", "Itineraries") + "</a>")}
{W.LANG_JS}
</body>
</html>
"""


def update_sitemap(posts):
    path = "sitemap.xml"
    s = open(path, encoding="utf-8").read()
    s = re.sub(r"  <url><loc>https://www\.goyokatravel\.com/blog/[^<]*</loc>.*?</url>\n", "", s)
    today = datetime.date.today().isoformat()
    block = f"  <url><loc>{BASE}/blog/</loc><lastmod>{today}</lastmod><priority>0.7</priority></url>\n" + "".join(
        f"  <url><loc>{BASE}/blog/{p['slug']}</loc><lastmod>{p.get('updated', p['date'])}</lastmod><priority>0.7</priority></url>\n"
        for p in posts)
    s = s.replace("</urlset>", block + "</urlset>")
    open(path, "w", encoding="utf-8").write(s)


def main():
    posts = load_posts()
    raw = json.load(open(W.DATA, encoding="utf-8"))
    items_by_slug = {i["slug"]: i for i in raw if i.get("slug")}
    os.makedirs(OUT, exist_ok=True)
    for p in posts:
        open(f"{OUT}/{p['slug']}.html", "w", encoding="utf-8").write(post_page(p, items_by_slug, posts))
    open(f"{OUT}/index.html", "w", encoding="utf-8").write(index_page(posts))
    update_sitemap(posts)
    print(f"ok: {len(posts)} artículos")


if __name__ == "__main__":
    main()
