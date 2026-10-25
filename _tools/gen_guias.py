"""Genera las guías de goyokatravel.com/guias (contenido para Google, en español).

Las guías responden a búsquedas de quien está a punto de organizar un viaje en grupo
y terminan llevando a YOKA. Reutiliza la cabecera, el menú y el pie de las páginas de itinerarios.

Uso (desde la raíz de mi-web): python3 _tools/gen_guias.py
Salida: guias/<slug>.html, guias/index.html y sus entradas en sitemap.xml
"""
import datetime, json, os, re, sys

sys.path.insert(0, os.path.dirname(__file__))
import gen_web as W  # noqa: E402

BASE = W.BASE
OUT = "guias"
e = W.e

# ── Contenido ────────────────────────────────────────────────────────────────
# Cada sección: (título h2, html). El html se escribe a mano: solo <p>, <ul>, <ol>, <strong>, <a>.

GUIDES = [
dict(
  slug="como-organizar-un-viaje-con-amigos",
  title="Cómo organizar un viaje con amigos sin morir en el intento",
  h1="Cómo organizar un viaje <mark>con amigos</mark>",
  seo_title="Cómo organizar un viaje con amigos: guía paso a paso | YOKA",
  desc="Guía paso a paso para organizar un viaje en grupo: fechas, presupuesto, destino, reservas, itinerario y gastos, sin perderlo todo en el chat.",
  lead="Organizar un viaje en grupo es fácil hasta que sois más de tres. Esta es la forma de hacerlo sin 300 mensajes sin leer, sin un Excel que nadie abre y sin que la misma persona acabe haciéndolo todo.",
  sections=[
    ("1. Primero fechas y presupuesto, después destino",
     "<p>El error más común es empezar por el destino. Si no sabéis cuándo podéis ir todos ni cuánto queréis gastar, cualquier destino que propongáis se caerá a la semana.</p>"
     "<ul><li><strong>Fechas:</strong> que cada uno diga qué fines de semana o semanas tiene libres y quedaos con los que coinciden.</li>"
     "<li><strong>Presupuesto:</strong> pactad un máximo por persona sin contar vuelos ni alojamiento, o contándolo todo. Lo importante es que todos digan la misma cifra en voz alta.</li></ul>"),
    ("2. Elegid el destino votando",
     "<p>Con fechas y presupuesto claros, cada uno propone uno o dos destinos y se vota. Si gana uno con mucha diferencia, perfecto. Si hay empate, desempatad con el precio del transporte para esas fechas.</p>"
     "<p>Si no se os ocurre nada, partir de un itinerario hecho ahorra mucho tiempo: mirad los <a href=\"/itinerarios/\">itinerarios para viajar con amigos</a> y elegid uno que encaje con vuestros días.</p>"),
    ("3. Un solo sitio para toda la información",
     "<p>El chat del grupo está bien para hablar, pero fatal para guardar cosas: la dirección del hotel, las entradas o el plan del día acaban enterrados entre memes. Decidid desde el principio dónde va a estar todo y que nadie tenga que preguntar «¿me pasas el itinerario?».</p>"),
    ("4. Repartid las reservas",
     "<p>No hace falta que una sola persona lo reserve todo. Repartid: una persona el alojamiento, otra el transporte, otra las entradas que haya que sacar con antelación. Lo que sí conviene es apuntar en el momento quién ha pagado qué, para no tener que reconstruirlo al volver.</p>"),
    ("5. Un itinerario con margen",
     "<p>Un buen plan de grupo tiene uno o dos planes fijos por día (lo que hay que reservar o lo que no os queréis perder) y huecos para improvisar. Para los huecos, que cada uno vaya apuntando ideas: restaurantes, miradores, bares. El día antes, votáis y la más votada entra en el plan.</p>"),
    ("6. Gastos al día desde el primer euro",
     "<p>Apuntad cada gasto cuando ocurre, con quién lo ha pagado y entre quién se reparte. Al final del viaje solo hay que mirar quién debe a quién y hacer los pagos. Lo explicamos con un ejemplo en <a href=\"/guias/como-dividir-gastos-viaje-amigos\">cómo dividir los gastos de un viaje entre amigos</a>.</p>"),
    ("7. Durante el viaje",
     "<p>Que todo el mundo pueda ver el plan de hoy y la dirección del alojamiento sin depender de quien lo organizó. Y repartid lo que hay que llevar: no hacen falta cuatro secadores ni que nadie lleve cargador. Tenéis una lista en <a href=\"/guias/que-llevar-en-la-maleta-fin-de-semana\">qué llevar en la maleta para un fin de semana</a>.</p>"),
    ("Errores típicos",
     "<ul><li>Decidir el destino antes que las fechas.</li>"
     "<li>Que una sola persona lo organice todo y luego nadie sepa nada.</li>"
     "<li>Llenar el itinerario de planes y no dejar tiempo libre.</li>"
     "<li>Dejar las cuentas para el final.</li></ul>"),
  ],
  yoka="En <strong>YOKA</strong> creáis el viaje, invitáis al grupo con un código y lo tenéis todo en un sitio: el itinerario día a día, las ideas que se votan, el hotel de cada etapa, la maleta del grupo y los gastos con quién debe a quién. Durante el viaje, el modo Hoy os enseña el plan del día y el hotel aunque os quedéis sin cobertura.",
  faq=[
    ("¿Con cuánta antelación hay que organizar un viaje con amigos?",
     "Para una escapada de fin de semana, con 4 a 6 semanas suele bastar. Para un viaje largo o en fechas muy demandadas, como puentes o verano, mejor con 2 o 3 meses, sobre todo por los vuelos y el alojamiento."),
    ("¿Cómo ponemos de acuerdo a todos con el presupuesto?",
     "Pactad una cifra máxima por persona antes de elegir destino y decid qué incluye: solo el día a día o también vuelos y alojamiento. Si alguien no llega, mejor saberlo al principio y ajustar el plan."),
    ("¿Qué app usar para organizar un viaje en grupo?",
     "Una que junte el plan, las reservas y los gastos en el mismo sitio y que todo el grupo pueda ver. YOKA está pensada justo para eso y es gratis en iPhone (en Android está en beta)."),
  ],
  related=["lisboa-3-dias", "granada-finde", "despedida-en-cadiz"],
),
dict(
  slug="como-dividir-gastos-viaje-amigos",
  title="Cómo dividir los gastos de un viaje entre amigos",
  h1="Cómo dividir los gastos <mark>de un viaje</mark> entre amigos",
  seo_title="Cómo dividir los gastos de un viaje entre amigos (con ejemplo) | YOKA",
  desc="Bote común o cada uno paga y se apunta: cómo repartir los gastos de un viaje en grupo, con un ejemplo de quién debe a quién y qué hacer con los gastos desiguales.",
  lead="Hablar de dinero entre amigos da pereza, pero no hablarlo es peor. Estas son las dos formas que funcionan para repartir los gastos de un viaje, con un ejemplo de cómo cuadrar las cuentas al final.",
  sections=[
    ("Opción 1: bote común",
     "<p>Cada uno pone la misma cantidad al principio y de ese bote se paga todo lo compartido: comidas, taxis, entradas. Si se acaba, se vuelve a poner. Si sobra, se devuelve a partes iguales.</p>"
     "<p><strong>Va bien</strong> en viajes cortos, con un grupo que gasta parecido. <strong>Va mal</strong> cuando hay gastos que no son de todos o cuando alguien adelanta algo grande, como el alojamiento.</p>"),
    ("Opción 2: cada uno paga y se apunta",
     "<p>Paga quien esté más a mano y se apunta en el momento: qué es, cuánto ha costado, quién lo ha pagado y entre quién se reparte. Al final se calcula cuánto ha pagado cada uno y cuánto le tocaba.</p>"
     "<p>Es lo más justo y lo que mejor funciona en viajes de varios días. La clave es apuntarlo en el momento, no intentar recordarlo al volver.</p>"),
    ("Ejemplo: quién debe a quién",
     "<p>Cuatro amigos se van un fin de semana:</p>"
     "<ul><li>Ana paga el alojamiento: 400 €.</li><li>Bea paga una cena: 120 €.</li><li>Carlos paga la gasolina: 80 €.</li><li>Dani no ha pagado nada todavía.</li></ul>"
     "<p>En total son <strong>600 €</strong>, así que a cada uno le tocan <strong>150 €</strong>. Ana ha puesto 250 € de más; Bea, 30 € de menos; Carlos, 70 € de menos, y Dani, 150 € de menos.</p>"
     "<p>Para cuadrarlo bastan tres pagos: <strong>Dani paga 150 € a Ana, Carlos le paga 70 € y Bea le paga 30 €</strong>. Nada de que todos se paguen entre todos.</p>"),
    ("Gastos que no son de todos",
     "<ul><li><strong>Alguien que no bebe o no come algo:</strong> ese gasto se reparte solo entre quienes lo han consumido.</li>"
     "<li><strong>Habitaciones distintas:</strong> si una habitación es más cara, se reparte entre quienes duermen en ella.</li>"
     "<li><strong>Planes opcionales:</strong> una excursión o una entrada que no hacen todos va solo a quienes van.</li></ul>"),
    ("Consejos para que nadie se agobie",
     "<ul><li>Decidid el método antes de salir.</li>"
     "<li>Apuntad cada gasto el mismo día.</li>"
     "<li>Haced los pagos finales en la primera semana después del viaje, por Bizum o transferencia.</li>"
     "<li>Si alguien adelanta mucho dinero antes del viaje, que se le vaya devolviendo antes de salir.</li></ul>"),
  ],
  yoka="En <strong>YOKA</strong> cada viaje tiene su pestaña de gastos: apuntáis lo que paga cada uno y entre quién se reparte, y la app os dice quién debe a quién con el mínimo de pagos. Cada uno lo ve desde su móvil, sin depender de quien lleva las cuentas.",
  faq=[
    ("¿Qué es mejor, bote común o que cada uno pague y se apunte?",
     "El bote común es más sencillo para viajes cortos con gastos parecidos. Si hay gastos grandes adelantados o cosas que no son de todos, es más justo que cada uno pague y se apunte."),
    ("¿Cómo se calcula quién debe a quién?",
     "Se suma todo lo gastado, se divide entre las personas (o entre quienes participan en cada gasto) y se compara con lo que ha pagado cada uno. Quien ha pagado de menos paga a quien ha pagado de más."),
    ("¿Hay alguna app para dividir gastos de viaje?",
     "Sí. YOKA lo hace dentro del propio viaje, junto al itinerario y la maleta, para que no tengáis que usar una app distinta para cada cosa."),
  ],
  related=["mallorca-3-dias", "ibiza-fin-de-carrera-4-dias", "budapest-3-dias"],
),
dict(
  slug="que-llevar-en-la-maleta-fin-de-semana",
  title="Qué llevar en la maleta para un fin de semana",
  h1="Qué llevar en la maleta <mark>para un fin de semana</mark>",
  seo_title="Qué llevar en la maleta para un fin de semana: lista completa | YOKA",
  desc="Lista para hacer la maleta de un fin de semana: documentos, ropa, neceser, tecnología y lo que conviene repartir con el grupo para no llevar cuatro secadores.",
  lead="Para dos o tres días cabe todo en una maleta de cabina si sabes qué llevar. Esta es la lista, más un truco para los viajes en grupo: repartir lo que se puede compartir.",
  sections=[
    ("Documentos y dinero",
     "<ul><li>DNI o pasaporte (comprueba que no esté caducado).</li><li>Tarjeta de embarque o billetes en el móvil.</li>"
     "<li>Tarjeta del banco y algo de efectivo.</li><li>Reservas del alojamiento y de las entradas a mano.</li>"
     "<li>Tarjeta sanitaria europea si sales de España dentro de la UE.</li></ul>"),
    ("Ropa para 2 o 3 días",
     "<ul><li>Una muda de ropa interior y calcetines por día, y una de repuesto.</li>"
     "<li>Dos pantalones o faldas que combinen con todo.</li><li>Tres camisetas o camisas.</li>"
     "<li>Algo de abrigo según el destino: una sudadera o una chaqueta ligera casi siempre hace falta por la noche.</li>"
     "<li>Un conjunto para salir.</li><li>Pijama.</li>"
     "<li>Calzado cómodo para andar (lo llevas puesto) y otro par si vais a salir.</li>"
     "<li>Bañador, si hay playa, piscina o spa.</li></ul>"),
    ("Neceser",
     "<ul><li>Cepillo y pasta de dientes.</li><li>Desodorante.</li><li>Champú y gel si el alojamiento no tiene.</li>"
     "<li>Crema solar, también en invierno si hay montaña o nieve.</li><li>Lentillas o gafas, y medicinas que tomes.</li></ul>"
     "<p>Si vas solo con equipaje de mano en avión, revisa las normas de líquidos de tu aeropuerto y de tu aerolínea antes de salir: en muchos todavía hay que llevarlos en envases pequeños dentro de una bolsa transparente.</p>"),
    ("Tecnología",
     "<ul><li>Móvil y cargador.</li><li>Batería externa.</li><li>Auriculares.</li><li>Adaptador de enchufe si vais a un país con otro tipo de enchufe.</li></ul>"),
    ("Lo que se puede repartir en grupo",
     "<p>En un viaje con amigos no hace falta que cada uno lleve de todo. Repartid antes de salir:</p>"
     "<ul><li>Secador y plancha de pelo.</li><li>Un cargador múltiple o una regleta.</li>"
     "<li>Altavoz.</li><li>Botiquín básico: ibuprofeno o paracetamol, tiritas, algo para el estómago.</li>"
     "<li>Juego de cartas o de mesa.</li><li>Toallas de playa, si el alojamiento no tiene.</li></ul>"
     "<p>Así viajáis más ligeros y no aparecen cuatro secadores y ningún cargador.</p>"),
  ],
  yoka="En <strong>YOKA</strong> cada viaje tiene una maleta con dos listas: la <strong>del grupo</strong>, donde se reparte quién lleva qué, y <strong>la tuya</strong>, privada y con cantidades. Con «Hazme la maleta» te propone una lista para empezar.",
  faq=[
    ("¿Cabe todo en una maleta de cabina para un fin de semana?",
     "Sí, para 2 o 3 días es lo normal si eliges ropa que combine y llevas puesto el calzado más voluminoso. Revisa las medidas de equipaje de tu aerolínea, porque cambian de una a otra."),
    ("¿Qué es lo que más se olvida?",
     "El cargador, el DNI y algo de abrigo para la noche. Revisa esas tres cosas antes de cerrar la maleta."),
    ("¿Cómo repartimos lo que lleva cada uno en un viaje en grupo?",
     "Haced una lista compartida con lo que se puede llevar entre todos (secador, cargador múltiple, altavoz, botiquín) y que cada persona se apunte a una o dos cosas. En YOKA es la maleta del grupo."),
  ],
  related=["san-sebastian-finde", "malaga-finde", "oporto-3-dias"],
),
]

GUIDE_CSS = '<link rel="stylesheet" href="/guias/guia.css">\n'


def nav():
    # el menú de itinerarios, sin marcar «Itinerarios» como página actual
    return W.NAV.replace(' current"', '"').replace('class="js-lang current"', 'class="js-lang"')


def faq_html(faq):
    items = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in faq)
    return f'<section class="faq"><h2>Preguntas frecuentes</h2>{items}</section>'


def related_html(slugs, items_by_slug):
    cards = "".join(W.card(items_by_slug[s]) for s in slugs if s in items_by_slug)
    if not cards:
        return ""
    return f'<section class="related"><h2>Itinerarios para inspirarte</h2><div class="grid">{cards}</div></section>'


def guide_page(g, items_by_slug, today):
    url = f"{BASE}/guias/{g['slug']}"
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "Article", "headline": g["title"], "description": g["desc"], "url": url, "inLanguage": "es",
         "dateModified": today, "image": f"{BASE}/og-image.png",
         "author": {"@type": "Organization", "name": "YOKA", "url": BASE + "/"},
         "publisher": {"@type": "Organization", "name": "YOKA", "url": BASE + "/",
                       "logo": {"@type": "ImageObject", "url": f"{BASE}/logo-512.png"}}},
        {"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in g["faq"]]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "YOKA", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Guías", "item": BASE + "/guias/"},
            {"@type": "ListItem", "position": 3, "name": g["title"], "item": url}]}]}
    sections = "".join(f"<section><h2>{e(h)}</h2>{body}</section>" for h, body in g["sections"])
    return W.head(g["seo_title"], g["desc"], url, f"{BASE}/og-image.png", ld, "article", GUIDE_CSS) + f"""
<body class="guide">
{nav()}
<main class="wrap">
  <p class="crumbs"><a href="/">YOKA</a> › <a href="/guias/">Guías</a></p>
  <h1>{g['h1']}</h1>
  <p class="lead">{e(g['lead'])}</p>
  <article class="guide-body">{sections}</article>
  <section class="why">
    <h2>Todo el viaje en un solo sitio</h2>
    <p>{g['yoka']}</p>
    <a href="/descarga" data-goatcounter-click="clic-descarga-guia">Descargar YOKA gratis</a>
  </section>
  {faq_html(g['faq'])}
  {related_html(g['related'], items_by_slug)}
</main>
{W.footer(" · <a class='js-lang' href='/itinerarios/'>" + W.t("Itinerarios", "Itineraries") + "</a>")}
</body>
</html>
"""


def index_page(today):
    url = f"{BASE}/guias/"
    ld = {"@context": "https://schema.org", "@type": "ItemList", "name": "Guías de YOKA para viajar en grupo",
          "itemListElement": [{"@type": "ListItem", "position": n + 1, "url": f"{BASE}/guias/{g['slug']}", "name": g["title"]}
                              for n, g in enumerate(GUIDES)]}
    cards = "".join(f'<a class="guide-card" href="/guias/{g["slug"]}"><h2>{e(g["title"])}</h2><p>{e(g["desc"])}</p>'
                    f'<span class="cta">Leer la guía →</span></a>' for g in GUIDES)
    return W.head("Guías para organizar un viaje con amigos | YOKA",
                  "Guías prácticas para viajar en grupo: cómo organizar el viaje, cómo dividir los gastos y qué llevar en la maleta.",
                  url, f"{BASE}/og-image.png", ld, "website", GUIDE_CSS) + f"""
<body class="guide">
{nav()}
<main class="wrap">
  <p class="crumbs"><a href="/">YOKA</a> › Guías</p>
  <h1>Guías para viajar <mark>con amigos</mark></h1>
  <p class="lead">Todo lo que hay que saber para organizar un viaje en grupo sin agobios.</p>
  <div class="guide-list">{cards}</div>
  <section class="why">
    <h2>¿Buscáis destino?</h2>
    <p>Tenemos itinerarios día a día con mapa, horarios y presupuesto.</p>
    <a href="/itinerarios/">Ver itinerarios</a>
  </section>
</main>
{W.footer(" · <a class='js-lang' href='/itinerarios/'>" + W.t("Itinerarios", "Itineraries") + "</a>")}
</body>
</html>
"""


def update_sitemap(today):
    path = "sitemap.xml"
    s = open(path, encoding="utf-8").read()
    s = re.sub(r"  <url><loc>https://www\.goyokatravel\.com/guias/[^<]*</loc>.*?</url>\n", "", s)
    block = f"  <url><loc>{BASE}/guias/</loc><lastmod>{today}</lastmod><priority>0.7</priority></url>\n" + "".join(
        f"  <url><loc>{BASE}/guias/{g['slug']}</loc><lastmod>{today}</lastmod><priority>0.7</priority></url>\n" for g in GUIDES)
    s = s.replace("</urlset>", block + "</urlset>")
    open(path, "w", encoding="utf-8").write(s)


def main():
    today = datetime.date.today().isoformat()
    raw = json.load(open(W.DATA, encoding="utf-8"))
    items_by_slug = {i["slug"]: i for i in raw if i.get("slug")}
    os.makedirs(OUT, exist_ok=True)
    for g in GUIDES:
        open(f"{OUT}/{g['slug']}.html", "w", encoding="utf-8").write(guide_page(g, items_by_slug, today))
    open(f"{OUT}/index.html", "w", encoding="utf-8").write(index_page(today))
    update_sitemap(today)
    print(f"ok: {len(GUIDES)} guías")


if __name__ == "__main__":
    main()
