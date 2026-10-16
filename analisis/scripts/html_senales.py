"""Genera la página HTML del libro de señales a partir de los resultados calculados (senales_final.pkl, confluencia_final.pkl)."""
import html
import numpy as np
import pandas as pd

S = '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad'
F = pd.read_pickle(S + '/senales_final.pkl')
C = pd.read_pickle(S + '/confluencia_final.pkl')
E = html.escape


def pct(x):
    return '—' if x is None or (isinstance(x, float) and np.isnan(x)) else f'{x * 100:.0f} %'


def num(x, d=2):
    return f'{x:.{d}f}'.replace('.', ',')


def miles(n):
    return f'{int(n):,}'.replace(',', '.')


EVENTOS = [
    dict(key='caida', match='CAÍDA', nombre='Caída', tono='malo', icono='↓',
         pregunta='¿Este código, que hoy va bien, se va a hundir?',
         y='Vende menos de la mitad de lo esperable en los 3 meses siguientes.',
         pob='Códigos sanos: últimos 3 meses ≥ 60 % de su ritmo y sin meses a cero.',
         mag='vende {m}× lo esperable',
         accion='Con 2 o más señales, bajar el forecast de los próximos 3 meses a 0,3–0,4× lo esperable. Con 1 señal, a 0,6×. No extrapolar un buen trimestre de un código errático o que va contra su línea.'),
    dict(key='muerte', match='MUERTE', nombre='Muerte', tono='malo', icono='✕',
         pregunta='¿Este código va a dejar de venderse?',
         y='Vende menos del 20 % de su ritmo en los 6 meses siguientes.',
         pob='Códigos sanos: últimos 3 meses ≥ 60 % de su ritmo y sin meses a cero.',
         mag='vende {m}× su ritmo',
         accion='No reponer: no fabricar contra el forecast, poner el código en la lista de phase-out y pasar el volumen al hermano sano de la línea. Un pedido grande en un código errático no anuncia una recuperación: suele ser el último.'),
    dict(key='pedido', match='PEDIDO GRANDE', nombre='Pedido grande', tono='bueno', icono='↑',
         pregunta='¿Viene un pedido grande el mes que viene?',
         y='El sell-in del mes siguiente es al menos 2× su mediana de 12 meses.',
         pob='Todos los regulares con ≥ 150 uds/año.',
         mag='pide {m}× su media mensual',
         accion='Asegurar supply y stock para el mes siguiente por unas 1,5× la media mensual. Los cortes no se pierden: vuelven como pedido.',
         nota_conf='Con 2 o más señales solo hay casos suficientes en el periodo reciente (37 casos).'),
    dict(key='subida', match='SUBIDA', nombre='Subida fuerte', tono='bueno', icono='↗',
         pregunta='¿Va a vender mucho más de lo esperable?',
         y='Vende más de 1,5× lo esperable en los 3 meses siguientes.',
         pob='Todos los regulares con ≥ 150 uds/año.',
         mag='vende {m}× lo esperable',
         accion='No recortar: subir el forecast un 20 % y vigilar el supply. En los códigos activos el momentum de pedidos continúa.'),
    dict(key='vacio', match='MES VACÍO', nombre='Mes vacío', tono='neutro', icono='○',
         pregunta='¿El mes que viene vendrá vacío?',
         y='El sell-in del mes siguiente es menos del 25 % de su media.',
         pob='Todos los regulares con ≥ 150 uds/año.',
         mag='vende {m}× su media',
         accion='Mes a cero sin cortes: forecast 0 el mes siguiente. Mes a cero por cortes: mantener el forecast y el supply, la demanda sigue ahí.'),
]

SEN = {
    'C1': ('Errático, pequeño y con el último mes flojo', 'CV mensual ≥ 0,9 · menos de 4.000 uds/año · último mes por debajo del 30 % de su media', ''),
    'C2': ('Sube mucho más que su brand', 'Crece ≥ 4× más que su brand (sell-in interanual de 3 meses) · CV ≥ 0,9', 'Más débil en el periodo reciente.'),
    'C3': ('Va contra su línea', 'Crece ≥ 6× más que su Product Line mientras la línea cae ≥ 40 %', ''),
    'C4': ('Campaña de One Shots y tamaño grande', 'Los One Shots de la brand venden ≥ 70 % de lo que venden sus regulares en 3 meses · tamaño ≥ 150 ml',
           'Canibalismo por tamaño: los de 50–100 ml no se ven afectados (24 %, igual que la base).'),
    'C5': ('Muy errático y pequeño', 'CV mensual ≥ 1,25 · menos de 4.000 uds/año', ''),
    'M1': ('Pequeño, errático y su línea cae', 'Menos de 4.000 uds/año · CV ≥ 1 · la Product Line cae ≥ 30 % (interanual de 3 meses)', ''),
    'M2': ('Rabbit con EPOS peor que su brand', 'Segmento Rabbits · su EPOS interanual va ≥ 25 % peor que el EPOS de su brand',
           'Solo se puede medir desde que hay EPOS: 6 meses de decisión.'),
    'M3': ('Pico aislado', 'CV mensual ≥ 1,25 · pedido grande en los últimos 3 meses', ''),
    'M4': ('Tamaño grande tras un pedido grande', 'Tamaño ≥ 150 ml · pedido grande en los últimos 2 meses', ''),
    'M5': ('Pequeño y su línea cae', 'Menos de 4.000 uds/año · la Product Line cae ≥ 30 %', ''),
    'G1': ('Re-pedido tras un corte', '≥ 2 meses a cero en 12 meses · pedido grande en los últimos 2 meses · cortes ≥ 0,5 meses de venta', ''),
    'G2': ('Estantería vacía', 'Cortes ≥ 2 meses de venta · EPOS de los últimos 3 meses ≤ 0,65× su media', ''),
    'G3': ('La brand cae pero empuja One Shots', 'Sell-in de la brand ≤ −25 % interanual · sus One Shots ≥ 2,5× · el código pide todos los meses',
           'Más fuerte en el periodo reciente (45 % frente a 22 %).'),
    'G4': ('Septiembre', 'El mes que viene es septiembre · el código pidió todos los meses de los últimos 12',
           'Patrón de calendario: en los datos solo hay 4 septiembres.'),
    'U1': ('Momentum de pedidos', '≥ 3 pedidos grandes en 12 meses · últimos 3 meses ≥ 1,5× su ritmo', ''),
    'U2': ('Código irregular que se reactiva', 'Algún mes a cero en 12 meses · últimos 3 meses ≥ 1,2× su ritmo · su brand sin campaña de One Shots (< 5 %)', ''),
    'U3': ('Llenado de canal', 'El retailer compra ≥ 45 % más de lo que vende (sell-through ≤ 0,69 de lo normal) · pedido grande en los últimos 3 meses',
           'Señal débil: casi duplica la base pero se queda en el 23 %.'),
    'U4': ('Recuperación tras cortes', 'Cortes ≥ 0,6 meses de venta · el EPOS de la brand cae ≥ 20 %', ''),
    'V1': ('Mes a cero sin cortes', 'Último mes por debajo del 10 % de la media · sin Supply Cuts en 3 meses', 'Es demanda, no supply.'),
    'V2': ('Mes a cero y tendencia negativa', 'Último mes por debajo del 10 % de la media · pendiente de 12 meses negativa', ''),
    'V3': ('Mes a cero con cortes', 'Último mes por debajo del 10 % de la media · cortes de más de 1 mes de venta',
           'Es supply: solo el 48 % sigue vacío y el 18 % trae un pedido grande. Acción contraria: mantener el forecast.'),
}
PARTES = [('antiguo', 'Periodo antiguo (2023.M06–2025.M02)'), ('reciente', 'Periodo reciente (2025.M03–2026.M08)'),
          ('mitad A', 'Mitad A de los códigos'), ('mitad B', 'Mitad B de los códigos')]


def barra(p, base, label, enfasis, tip):
    """Fila de barra horizontal: etiqueta | pista con barra y marca de base | valor."""
    return (f'<div class="bar-row"><span class="bar-label">{E(label)}</span>'
            f'<span class="track" tabindex="0" data-tip="{E(tip)}">'
            f'<span class="bar{" bar--em" if enfasis else ""}" style="width:{p * 100:.1f}%"></span>'
            f'<span class="base-mark" style="left:{base * 100:.1f}%"></span></span>'
            f'<span class="bar-value">{pct(p)}</span></div>')


def tira(r, base):
    """Tira de consistencia: dónde cae el resultado en cada una de las 4 partes, con la base marcada."""
    dots, textos, ok, test = [], [], 0, 0
    umbral = 2 * base if base < 0.2 else base + 0.15
    for col, nombre in PARTES:
        v = r[col]
        if v is None or np.isnan(v):
            textos.append('—')
            continue
        test += 1
        ok += v >= umbral
        dots.append(f'<span class="dot" tabindex="0" style="left:{v * 100:.1f}%" data-tip="{E(nombre)}: {pct(v)}"></span>')
        textos.append(pct(v))
    estado = f'Se cumple en {ok} de {test} partes' if test else 'Sin partes medibles'
    return (f'<div class="strip-wrap"><div class="strip"><span class="strip-base" style="left:{base * 100:.1f}%"></span>'
            f'{"".join(dots)}</div><div class="strip-text"><span>{" · ".join(textos)}</span>'
            f'<span class="strip-state{" strip-state--ok" if ok == test and test else ""}">{estado}</span></div></div>')


def seccion_evento(ev):
    g = F[F.evento.str.startswith(ev['match'])]
    base = float(g.base.iloc[0])
    filas = []
    for _, r in g.iterrows():
        sid = r['señal'].split(' ')[0]
        titulo, cond, nota = SEN[sid]
        lift = r.p / base
        filas.append(f'''
      <article class="sig" id="{sid.lower()}">
        <div class="sig-main">
          <div class="sig-head"><span class="sig-id">{sid}</span><h4>{E(titulo)}</h4></div>
          <p class="sig-cond">{E(cond)}</p>
          {f'<p class="sig-note">{E(nota)}</p>' if nota else ''}
        </div>
        <div class="sig-prob">
          <span class="prob">{pct(r.p)}</span>
          <span class="prob-sub">IC 95 %: {pct(r.lo)}–{pct(r.hi)}</span>
          <span class="prob-sub">{num(lift, 1)}× la base</span>
        </div>
        <div class="sig-strip">{tira(r, base)}</div>
        <dl class="sig-facts">
          <div><dt>Casos</dt><dd>{miles(r.n)}</dd></div>
          <div><dt>Códigos</dt><dd>{int(r.cod)}</dd></div>
          <div><dt>Meses</dt><dd>{int(r.meses)}</dd></div>
          <div><dt>Mediana</dt><dd>{num(r.mag)}×</dd></div>
        </dl>
      </article>''')
    return f'''
  <section class="event" id="{ev['key']}">
    <header class="event-head">
      <p class="eyebrow"><span class="tone tone--{ev['tono']}" aria-hidden="true">{ev['icono']}</span>{E(ev['nombre'])} · base {pct(base)}</p>
      <h3>{E(ev['pregunta'])}</h3>
      <p class="event-def"><strong>Qué se predice:</strong> {E(ev['y'])} <span class="muted">{E(ev['pob'])}</span></p>
    </header>
    <div class="sig-list">{''.join(filas)}
    </div>
    <div class="action"><span class="action-label">Acción</span><p>{E(ev['accion'])}</p></div>
  </section>'''


def resumen_evento(ev):
    c = C[C.evento.str.startswith(ev['match'])].set_index('señales')
    base = float(F[F.evento.str.startswith(ev['match'])].base.iloc[0])
    rows = []
    for k, label in [('0', 'Sin señales'), ('1', '1 señal'), ('2+', '2 o más')]:
        r = c.loc[k]
        tip = (f'{label}: {pct(r.p)} (IC {pct(r.lo)}–{pct(r.hi)}), {miles(r.n)} casos de {int(r.cod)} códigos. '
               f'Antiguo {pct(r.antiguo) if r.n_ant >= 10 else "sin casos suficientes"} · reciente {pct(r.reciente) if r.n_rec >= 10 else "sin casos suficientes"}.')
        rows.append(barra(r.p, base, label, k == '2+', tip))
    r2 = c.loc['2+']
    mag = ev['mag'].format(m=num(r2.mag))
    nota = ev.get('nota_conf', '')
    return f'''
    <article class="sum">
      <div class="sum-head">
        <a class="sum-name" href="#{ev['key']}"><span class="tone tone--{ev['tono']}" aria-hidden="true">{ev['icono']}</span>{E(ev['nombre'])}</a>
        <p class="sum-q">{E(ev['y'])}</p>
      </div>
      <div class="bars" role="img" aria-label="{E(ev['nombre'])}: sin señales {pct(c.loc['0'].p)}, 1 señal {pct(c.loc['1'].p)}, 2 o más {pct(r2.p)}; base {pct(base)}">
        {''.join(rows)}
        <div class="axis"><span>0</span><span>50 %</span><span>100 %</span></div>
      </div>
      <div class="sum-act">
        <p class="sum-big">{pct(r2.p)} <span>con 2 o más señales</span></p>
        <p class="sum-mag">El código típico {E(mag)}.</p>
        {f'<p class="sum-note">{E(nota)}</p>' if nota else ''}
      </div>
    </article>'''


OTRAS = [
    ('DA positivo planificado', 'Llega ≈ 0,55 por unidad en regulares y ≈ 0,40 en One Shots', 'Planificar la mitad del DA como volumen incremental'),
    ('Supply Cut', 'Vuelve ≈ 0,40 por unidad cortada como pedido en los 3 meses siguientes (IC 0,22–0,59)', 'Sumar un 40 % del corte al forecast de los 3 meses siguientes'),
    ('EAN que sustituye a otro (misma línea y tamaño)', 'El viejo cae a 0 en unos 3 meses; el nuevo hereda ≈ 100 % (1,2–2× durante el llenado si es relanzamiento)', 'Pasar la historia y el forecast del viejo al nuevo'),
    ('Lanzamiento de un regular', 'El 50 % del primer año entra en los meses 1–3; a los 12 meses el canal tiene 2,4× lo vendido', 'No proyectar el mes 1; esperar una recompra débil en los meses 7–12'),
    ('EPOS de julio y agosto', 'Con EPOS por debajo del −30 % interanual, la carga de septiembre a noviembre baja (78 % de los códigos, −22 %)', 'Dimensionar la carga de Q4 con el EPOS de verano'),
]
NO = [
    ('Rebote de un código flojo', 'Solo el 14 % vuelve a su nivel y ninguna señal lo anticipa en las 4 partes. No planificar recuperaciones sin un motivo concreto.'),
    ('Muchos lanzamientos matan a los códigos pequeños', 'Pasó en el periodo reciente (46 %) pero no en el antiguo (10 %). No es una regla fija.'),
    ('El retailer vendió lo que compró, así que viene un pedido', 'Al revés: con sell-through > 1,8 la probabilidad de pedido grande baja al 7 %. Los pedidos siguen el calendario: septiembre, octubre, diciembre y marzo.'),
    ('Señales para One Shots', 'Ninguna combinación se confirma. Lo único sólido es que su DA llega en torno al 40 %.'),
]

nav = ''.join(f'<a href="#{e["key"]}"><span class="tone tone--{e["tono"]}" aria-hidden="true">{e["icono"]}</span>{E(e["nombre"])}</a>' for e in EVENTOS)

page = f'''<title>Señales de demanda Gucci</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
/* Libro de señales: una columna de lectura; resumen comparable arriba, detalle por evento debajo. */
:root {{
  --bg: #f4f6f9; --surface: #ffffff; --ink: #11151c; --ink-2: #4a5263; --muted: #6f7787; --line: #e2e6ed; --line-2: #c9cfda;
  --accent: #1f6fd6; --accent-soft: #86b6ef; --accent-wash: #e8f1fc;
  --bad: #d03b3b; --good: #0f8a0f; --neutral: #7a8291;
  --font: system-ui, -apple-system, "SF Pro Text", "Segoe UI", Roboto, sans-serif;
  --mono: ui-monospace, "SF Mono", "Cascadia Mono", Menlo, monospace;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg: #0e1116; --surface: #161a21; --ink: #eef1f5; --ink-2: #b8c0cc; --muted: #8b93a1; --line: #262c36; --line-2: #3a4250;
    --accent: #4b93ea; --accent-soft: #1f5aa8; --accent-wash: #16253a;
    --bad: #e66767; --good: #2fb62f; --neutral: #8b93a1; color-scheme: dark;
  }}
}}
:root[data-theme="dark"] {{
  --bg: #0e1116; --surface: #161a21; --ink: #eef1f5; --ink-2: #b8c0cc; --muted: #8b93a1; --line: #262c36; --line-2: #3a4250;
  --accent: #4b93ea; --accent-soft: #1f5aa8; --accent-wash: #16253a;
  --bad: #e66767; --good: #2fb62f; --neutral: #8b93a1; color-scheme: dark;
}}
* {{ box-sizing: border-box; }}
body {{ background: var(--bg); color: var(--ink); font: 15px/1.55 var(--font); }}
.wrap {{ max-width: 1080px; margin: 0 auto; padding-block: 40px 64px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  display: grid; gap: 48px; }}
h1, h2, h3, h4 {{ text-wrap: balance; margin: 0; }}
p {{ margin: 0; }}
a {{ color: var(--accent); }}
a:focus-visible, [tabindex]:focus-visible, summary:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 4px; }}
.muted {{ color: var(--muted); }}
.eyebrow {{ font-size: 12px; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: var(--ink-2); display: flex; align-items: center; gap: 8px; }}
.tone {{ display: inline-grid; place-items: center; width: 20px; height: 20px; border-radius: 6px; font-size: 13px; font-weight: 700; color: #fff; letter-spacing: 0; text-transform: none; }}
.tone--malo {{ background: var(--bad); }} .tone--bueno {{ background: var(--good); }} .tone--neutro {{ background: var(--neutral); }}

/* Cabecera */
.intro {{ display: grid; gap: 18px; }}
.intro h1 {{ font-size: clamp(30px, 5vw, 44px); line-height: 1.08; letter-spacing: -.02em; font-weight: 750; }}
.lede {{ font-size: 17px; color: var(--ink-2); max-width: 68ch; }}
.facts {{ display: flex; flex-wrap: wrap; gap: 8px 28px; font-size: 14px; color: var(--ink-2); }}
.facts b {{ color: var(--ink); font-weight: 650; font-variant-numeric: tabular-nums; }}
.nav {{ display: flex; flex-wrap: wrap; gap: 8px; }}
.nav a {{ display: inline-flex; align-items: center; gap: 8px; padding: 7px 12px 7px 8px; border: 1px solid var(--line-2); border-radius: 999px;
  color: var(--ink); text-decoration: none; font-weight: 550; background: var(--surface); }}
.nav a:hover {{ border-color: var(--accent); }}

/* Bloques */
.block {{ display: grid; gap: 20px; }}
.block > header {{ display: grid; gap: 6px; max-width: 72ch; }}
.block h2 {{ font-size: 24px; letter-spacing: -.01em; }}
.block > header p {{ color: var(--ink-2); }}
.howto {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }}
.howto div {{ background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 14px 16px; display: grid; gap: 4px; }}
.howto b {{ font-size: 14px; }}
.howto span {{ font-size: 14px; color: var(--ink-2); }}

/* Resumen: confluencia */
.sums {{ background: var(--surface); border: 1px solid var(--line); border-radius: 16px; }}
.sum {{ display: grid; grid-template-columns: minmax(180px, 1fr) minmax(240px, 1.6fr) minmax(200px, 1fr); gap: 20px 28px; padding: 22px 24px; align-items: center; }}
.sum + .sum {{ border-top: 1px solid var(--line); }}
.sum-head {{ display: grid; gap: 6px; min-width: 0; }}
.sum-name {{ display: inline-flex; align-items: center; gap: 8px; font-size: 18px; font-weight: 700; color: var(--ink); text-decoration: none; }}
.sum-name:hover {{ color: var(--accent); }}
.sum-q {{ font-size: 13.5px; color: var(--ink-2); }}
.sum-act {{ display: grid; gap: 4px; min-width: 0; }}
.sum-big {{ font-size: 30px; font-weight: 750; letter-spacing: -.02em; line-height: 1.1; }}
.sum-big span {{ display: block; font-size: 13px; font-weight: 500; color: var(--ink-2); letter-spacing: 0; }}
.sum-mag {{ font-size: 14px; color: var(--ink-2); }}
.sum-note {{ font-size: 12.5px; color: var(--muted); }}
.bars {{ display: grid; gap: 8px; min-width: 0; }}
.bar-row {{ display: grid; grid-template-columns: 78px 1fr 44px; gap: 10px; align-items: center; font-size: 13px; }}
.bar-label {{ color: var(--ink-2); }}
.bar-value {{ font-variant-numeric: tabular-nums; font-weight: 600; text-align: right; }}
.track {{ position: relative; height: 22px; display: flex; align-items: center; cursor: default; }}
.track::before {{ content: ""; position: absolute; inset: 10px 0 auto; height: 1px; background: var(--line); }}
.bar {{ position: relative; height: 14px; background: var(--accent-soft); border-radius: 0 4px 4px 0; min-width: 2px; }}
.bar--em {{ background: var(--accent); }}
.track:hover .bar, .track:focus-visible .bar {{ filter: brightness(1.08); }}
.base-mark {{ position: absolute; top: 2px; bottom: 2px; width: 2px; margin-left: -1px; background: var(--ink-2); border-radius: 1px; }}
.axis {{ position: relative; height: 14px; margin-left: 88px; margin-right: 54px; font-size: 11px; color: var(--muted); font-variant-numeric: tabular-nums; }}
.axis span {{ position: absolute; top: 0; }}
.axis span:nth-child(1) {{ left: 0; }} .axis span:nth-child(2) {{ left: 50%; transform: translateX(-50%); }} .axis span:nth-child(3) {{ right: 0; }}
.legend {{ display: flex; flex-wrap: wrap; gap: 6px 18px; font-size: 12.5px; color: var(--ink-2); padding: 0 24px 18px; }}
.legend span {{ display: inline-flex; align-items: center; gap: 6px; }}
.key {{ display: inline-block; width: 14px; height: 10px; border-radius: 0 3px 3px 0; }}
.key--em {{ background: var(--accent); }} .key--soft {{ background: var(--accent-soft); }}
.key--base {{ width: 2px; height: 14px; background: var(--ink-2); border-radius: 1px; }}
.key--dot {{ width: 10px; height: 10px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 0 2px var(--surface); }}

/* Secciones por evento */
.event {{ display: grid; gap: 16px; scroll-margin-top: 16px; }}
.event-head {{ display: grid; gap: 8px; max-width: 76ch; }}
.event-head h3 {{ font-size: 22px; letter-spacing: -.01em; }}
.event-def {{ color: var(--ink-2); font-size: 14.5px; }}
.event-def strong {{ color: var(--ink); font-weight: 600; }}
.sig-list {{ background: var(--surface); border: 1px solid var(--line); border-radius: 16px; }}
.sig {{ display: grid; grid-template-columns: minmax(0, 1.7fr) 112px minmax(180px, 1fr) 150px; gap: 16px 24px; padding: 18px 22px; align-items: start; }}
.sig + .sig {{ border-top: 1px solid var(--line); }}
.sig-main {{ display: grid; gap: 6px; min-width: 0; }}
.sig-head {{ display: flex; align-items: baseline; gap: 10px; }}
.sig-id {{ font: 600 12px/1 var(--mono); color: var(--ink-2); border: 1px solid var(--line-2); border-radius: 6px; padding: 4px 6px; flex: none; }}
.sig h4 {{ font-size: 16px; font-weight: 650; }}
.sig-cond {{ font-size: 14px; color: var(--ink-2); }}
.sig-note {{ font-size: 13px; color: var(--muted); }}
.sig-prob {{ display: grid; gap: 2px; }}
.prob {{ font-size: 28px; font-weight: 750; letter-spacing: -.02em; line-height: 1.1; }}
.prob-sub {{ font-size: 12px; color: var(--muted); font-variant-numeric: tabular-nums; }}
.strip-wrap {{ display: grid; gap: 6px; padding-top: 8px; }}
.strip {{ position: relative; height: 18px; }}
.strip::before {{ content: ""; position: absolute; left: 0; right: 0; top: 8px; height: 2px; border-radius: 1px; background: var(--line); }}
.strip-base {{ position: absolute; top: 1px; bottom: 1px; width: 2px; margin-left: -1px; background: var(--ink-2); border-radius: 1px; }}
.dot {{ position: absolute; top: 4px; width: 10px; height: 10px; margin-left: -5px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 0 2px var(--surface); }}
.dot::after {{ content: ""; position: absolute; inset: -7px; }}
.strip-text {{ display: grid; gap: 2px; font-size: 12px; color: var(--ink-2); font-variant-numeric: tabular-nums; }}
.strip-state {{ color: var(--muted); }}
.strip-state--ok {{ color: var(--ink); font-weight: 600; }}
.sig-facts {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px 14px; margin: 0; }}
.sig-facts div {{ display: grid; }}
.sig-facts dt {{ font-size: 11px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); }}
.sig-facts dd {{ margin: 0; font-weight: 600; font-variant-numeric: tabular-nums; }}
.action {{ display: grid; grid-template-columns: auto 1fr; gap: 14px; align-items: start; background: var(--accent-wash); border-radius: 12px; padding: 14px 18px; }}
.action-label {{ font-size: 12px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: var(--accent); padding-top: 2px; }}
.action p {{ max-width: 80ch; }}

/* Tablas y listas */
.table-wrap {{ overflow-x: auto; background: var(--surface); border: 1px solid var(--line); border-radius: 16px; }}
table {{ border-collapse: collapse; width: 100%; min-width: 640px; font-size: 14px; }}
th, td {{ text-align: left; vertical-align: top; padding: 12px 16px; border-bottom: 1px solid var(--line); }}
th {{ font-size: 12px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); font-weight: 600; }}
tr:last-child td {{ border-bottom: 0; }}
td:first-child {{ font-weight: 600; }}
.no {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; }}
.no div {{ background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 14px 16px; display: grid; gap: 6px; align-content: start; }}
.no b {{ font-size: 15px; }}
.no span {{ font-size: 14px; color: var(--ink-2); }}
details {{ background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 4px 20px; }}
summary {{ cursor: pointer; font-weight: 650; padding: 12px 0; }}
details ul {{ margin: 0 0 16px; padding-left: 20px; display: grid; gap: 8px; color: var(--ink-2); max-width: 82ch; }}
footer {{ font-size: 13px; color: var(--muted); }}

/* Tooltip */
.tip {{ position: fixed; z-index: 20; max-width: 280px; padding: 8px 10px; border-radius: 8px; background: var(--ink); color: var(--bg);
  font-size: 12.5px; line-height: 1.4; pointer-events: none; box-shadow: 0 6px 20px rgba(0,0,0,.18); }}

@media (max-width: 860px) {{
  .sum {{ grid-template-columns: 1fr; gap: 14px; }}
  .sig {{ grid-template-columns: 1fr 1fr; }}
  .sig-main {{ grid-column: 1 / -1; }}
  .sig-strip {{ grid-column: 1 / -1; }}
}}
@media (max-width: 480px) {{
  .sig {{ grid-template-columns: 1fr; }}
  .action {{ grid-template-columns: 1fr; gap: 6px; }}
  .legend {{ padding: 0 16px 16px; }}
  .sum, .sig {{ padding-left: 16px; padding-right: 16px; }}
}}
@media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; }} }}
</style>

<div class="wrap">
  <header class="intro">
    <p class="eyebrow">Gucci · regulares · sell-in real</p>
    <h1>Señales de demanda Gucci</h1>
    <p class="lede">Combinaciones de indicadores que se ven el día de la foto y anticipan lo que de verdad va a pasar con el sell-in de un código. Cada señal trae la probabilidad con la que se cumplió y la acción que pide. No se usa el Consensus en ningún paso.</p>
    <p class="facts"><span><b>3.370</b> casos código × mes</span><span><b>128</b> códigos regulares</span><span><b>75</b> indicadores probados</span><span><b>4</b> partes de validación</span><span>Decisiones de 2023.M06 a 2026.M08</span></p>
    <nav class="nav" aria-label="Eventos">{nav}</nav>
  </header>

  <section class="block">
    <header>
      <h2>Cómo leer cada señal</h2>
      <p>Una señal solo entra en el libro si se cumple en las cuatro partes de los datos y en al menos cuatro meses distintos.</p>
    </header>
    <div class="howto">
      <div><b>Probabilidad</b><span>Porcentaje de veces que pasó el evento cuando la señal estaba activa, con su intervalo del 95 %.</span></div>
      <div><b>Base</b><span>Lo que pasa sin mirar ninguna señal. La señal vale lo que supera a la base.</span></div>
      <div><b>Cuatro partes</b><span>Periodo antiguo, periodo reciente y cada mitad de los códigos. Cada punto azul es el resultado en una parte.</span></div>
      <div><b>Mediana</b><span>Lo que vendió el código típico cuando la señal estaba activa, frente a lo esperable, su ritmo o su media.</span></div>
    </div>
  </section>

  <section class="block" id="resumen">
    <header>
      <h2>Las señales se suman</h2>
      <p>Probabilidad de cada evento según cuántas de sus señales están activas a la vez. Cuantas más coinciden, más probable es el evento.</p>
    </header>
    <div class="sums">{''.join(resumen_evento(e) for e in EVENTOS)}
      <div class="legend"><span><i class="key key--soft"></i>0 o 1 señal</span><span><i class="key key--em"></i>2 o más señales</span><span><i class="key key--base"></i>Base del evento</span></div>
    </div>
  </section>

  {''.join(seccion_evento(e) for e in EVENTOS)}

  <section class="block">
    <header>
      <h2>Lo que no se confirma</h2>
      <p>Ideas razonables que los datos no sostienen. También deciden: evitan acciones que no funcionan.</p>
    </header>
    <div class="no">{''.join(f'<div><b>{E(a)}</b><span>{E(b)}</span></div>' for a, b in NO)}</div>
  </section>

  <section class="block">
    <header>
      <h2>Otras relaciones medidas</h2>
      <p>Medidas sobre lo que pasó de verdad, no sobre lo planificado.</p>
    </header>
    <div class="table-wrap"><table>
      <thead><tr><th>Cuando hay…</th><th>Lo que pasó</th><th>Acción</th></tr></thead>
      <tbody>{''.join(f'<tr><td>{E(a)}</td><td>{E(b)}</td><td>{E(c)}</td></tr>' for a, b, c in OTRAS)}</tbody>
    </table></div>
  </section>

  <details>
    <summary>Método y límites</summary>
    <ul>
      <li><b>Datos:</b> 14 fotos de Gucci (2025.M09–2026.M10); actuals cerrados hasta 2026.M09. El cambio de perímetro de la foto 2026.M02 (+29 % en la historia) se corrigió con un factor por código.</li>
      <li><b>Indicadores:</b> 75, todos con información hasta el mes anterior. Momentum interanual de 1, 3, 6 y 12 meses, aceleración, volatilidad, caída desde máximos, pedidos grandes, EPOS, sell-through, stock en el canal, Product Line, brand y casa sin el propio código, cuota, lanzamientos, One Shots, cortes, edad, tamaño, segmento y calendario.</li>
      <li><b>Búsqueda:</b> cada indicador se corta en los percentiles 10, 20, 30, 70, 80 y 90. Se prueban todas las condiciones sueltas, todas las parejas (unas 200.000 reglas por evento) y los mejores tríos.</li>
      <li><b>Validación:</b> se descubre en una parte y se confirma en otra (test binomial con corrección de Benjamini-Hochberg). Después, la regla tiene que superar a la base en las cuatro partes (2× la base si la base es menor del 20 %; base + 15 puntos si es mayor) y repetirse en al menos cuatro meses. Los umbrales se redondearon y se volvieron a medir.</li>
      <li><b>«Esperable»:</b> el nivel del código en los últimos 12 meses por la estacionalidad de su brand el año anterior.</li>
      <li><b>Límites:</b> solo Gucci y solo regulares; las señales con EPOS solo tienen datos de 2024.M10 a 2026.M08; los meses consecutivos se solapan, por eso se muestran códigos y meses distintos; correlación no es causalidad. Hay que volver a medir cada trimestre y en cada casa.</li>
    </ul>
  </details>

  <footer>Análisis del 16/10/2026 sobre las fotos de <code>data/Gucci/Consensus/</code>. Detalle completo en <code>analisis/SENALES-2026-10.md</code>.</footer>
</div>
<div class="tip" id="tip" hidden></div>
<script>
(() => {{
  const tip = document.getElementById('tip');
  const show = (el) => {{
    tip.textContent = el.getAttribute('data-tip');
    tip.hidden = false;
    const r = el.getBoundingClientRect(), w = tip.offsetWidth, h = tip.offsetHeight;
    let x = r.left + r.width / 2 - w / 2, y = r.top - h - 8;
    x = Math.max(8, Math.min(x, window.innerWidth - w - 8));
    if (y < 8) y = r.bottom + 8;
    tip.style.left = x + 'px'; tip.style.top = y + 'px';
  }};
  const hide = () => {{ tip.hidden = true; }};
  document.querySelectorAll('[data-tip]').forEach((el) => {{
    el.addEventListener('pointerenter', () => show(el));
    el.addEventListener('pointerleave', hide);
    el.addEventListener('focus', () => show(el));
    el.addEventListener('blur', hide);
  }});
  window.addEventListener('scroll', hide, {{ passive: true }});
}})();
</script>
'''
open(S + '/senales-gucci.html', 'w', encoding='utf-8').write(page)
print('ok', len(page))
