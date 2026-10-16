"""Página de escenarios frente al Consensus: real más bajo / mucho más bajo / más alto / mucho más alto y orden no prevista."""
import html
import json
import numpy as np

S = '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad'
D = json.load(open(S + '/cons_cartas.json'))
E = html.escape
sig = lambda z: 1 / (1 + np.exp(-z))  # noqa: E731


def pct(x):
    return f'{x * 100:.0f} %'


def miles(x):
    return f'{x:,.0f}'.replace(',', '.')


def pts(p):
    return (f'+{p}' if p > 0 else f'−{abs(p)}') if p else '0'


def fuerza(p):
    a = abs(p)
    return 'Muy clara' if a >= 8 else ('Moderada' if a >= 4 else 'Ligera')


CATS = [
    ('Y_bajo', 'bajo', 'Real más bajo', 'Lo vendido en los próximos 3 meses queda por debajo de 0,8 veces el Consensus.'),
    ('Y_muy_bajo', 'muybajo', 'Real mucho más bajo', 'Lo vendido queda por debajo de la mitad del Consensus.'),
    ('Y_alto', 'alto', 'Real más alto', 'Lo vendido supera 1,2 veces el Consensus.'),
    ('Y_muy_alto', 'muyalto', 'Real mucho más alto', 'Lo vendido supera 1,5 veces el Consensus.'),
    ('Y_orden', 'orden', 'Orden no prevista', 'Algún mes de los 3 llega un pedido grande (al menos el doble de su mediana) que el Consensus no tenía: ese mes se vende más del doble de lo previsto.'),
]
NOTAS = {
    'EP_acel': 'Contraintuitiva: cuando el sell-out se dispara (por ejemplo, una promo en tienda), el retailer vende de su stock y compra menos de lo previsto.',
    'O_cortes_altos': 'Tras un corte fuerte, el Consensus se queda corto: la demanda que no se sirvió vuelve.',
    'O_cortes': 'Tras un corte, la demanda vuelve y el riesgo de quedar muy por debajo del Consensus baja.',
    'C_ceros': 'Los códigos que piden a saltos sorprenden con pedidos que el Consensus no tenía.',
    'G_contra_casa': 'Tu hipótesis: el código que sube a contracorriente de la casa mantiene el impulso.',
    'G_contra_brand': 'El código que sube a contracorriente de su brand mantiene el impulso.',
    'K_ep_hi': 'El Consensus promete más crecimiento del que se ve en tienda.',
    'K_da_alto': 'El DA solo llega en parte: de cada 100 unidades planificadas llegan unas 55.',
    'K_ritmo_lo': 'Cuando el Consensus recorta por debajo del ritmo del código, suele pasarse recortando.',
    'K_ritmo_LO': 'Recorte muy fuerte frente al ritmo: el real suele quedar por encima.',
    'K_frontal': 'Si el Consensus concentra el volumen en los primeros meses, ese volumen no suele llegar.',
    'G_casa_dn': 'Cuando la casa cae, llegan pedidos de reposición que no estaban en el plan.',
    'EP_dn3': 'Con el sell-out cayendo, las sorpresas al alza casi desaparecen.',
    'X_stock_bajo': 'Canal vacío: el retailer ya no compra para reponer, compra lo justo.',
    'O_os_campaña': 'Con campaña fuerte de One Shots, la brand no hace pedidos sorpresa de regulares.',
}


def tarjeta_senal(s, cls):
    signo = 'mas' if s['puntos'] > 0 else 'menos'
    nota = NOTAS.get(s['id'], '')
    epos = '<span class="tag">usa EPOS</span>' if s['epos'] else ''
    return f'''
        <li class="sc sc--{signo}">
          <div class="sc-pts"><b>{pts(s['puntos'])}</b><span>{fuerza(s['puntos'])}</span></div>
          <div class="sc-body">
            <p class="sc-txt">{E(s['texto'])}</p>
            <p class="sc-meta"><span class="tag">{E(s['familia'])}</span>{epos}<span>Cuando salta, pasó en el {pct(s['p_si'])} de {miles(s['n'])} casos</span></p>
            {f'<p class="sc-nota">{E(nota)}</p>' if nota else ''}
          </div>
        </li>'''


def seccion(y, cls, nombre, defi):
    c = D['categorias'][y]
    pos = [s for s in c['senales'] if s['puntos'] > 0]
    neg = [s for s in c['senales'] if s['puntos'] < 0]
    cal = ''.join(f'<tr><td>{pts(b["lo"]) if b["lo"] > -99 else "−15 o menos"}{"" if b["lo"] <= -99 else (" a " + pts(b["hi"]) if b["hi"] < 99 else " o más")}</td>'
                  f'<td>{pct(b["pred"])}</td><td>{pct(b["obs"])}</td><td>{miles(b["n"])}</td></tr>' for b in c['cal'])
    escala = ''.join(f'<span><b>{pts(p)}</b>{pct(sig(c["b0"] + p / 10))}</span>' for p in [-20, -10, -5, 0, 5, 10, 20, 30])
    return f'''
  <section class="cat cat--{cls}" id="{cls}">
    <header class="cat-head">
      <p class="eyebrow"><i class="dot dot--{cls}"></i>{E(nombre)}</p>
      <h3>{E(defi)}</h3>
      <div class="cat-stats">
        <span>Pasa en el <b>{pct(c['base'])}</b> de los casos</span>
        <span>Punto de partida sin señales: <b>{pct(c['inicio'])}</b></span>
        <span>Capacidad de ordenar (AUC): <b>{str(round(c['auc_cv'], 2)).replace('.', ',')}</b></span>
      </div>
    </header>
    <div class="cols">
      <div class="col">
        <h4>Señales que empujan hacia {E(nombre.lower())}</h4>
        <ul class="sc-list">{''.join(tarjeta_senal(s, cls) for s in pos)}</ul>
      </div>
      <div class="col">
        <h4>Señales que la frenan</h4>
        <ul class="sc-list">{''.join(tarjeta_senal(s, cls) for s in neg)}</ul>
      </div>
    </div>
    <div class="conv">
      <div class="conv-scale"><p class="mini">Puntos → probabilidad</p><div class="scale">{escala}</div></div>
      <div class="table-wrap"><table>
        <thead><tr><th>Puntos sumados</th><th>El modelo dice</th><th>Pasó de verdad</th><th>Casos</th></tr></thead>
        <tbody>{cal}</tbody></table></div>
    </div>
  </section>'''


def fila_hoy(h):
    celdas = ''.join(f'<span class="m m--{cls}" title="{E(nombre)}: {pct(h[y])}"><i style="width:{h[y] * 100:.0f}%"></i><b>{pct(h[y])}</b></span>' for y, cls, nombre, _ in CATS)
    det = []
    for y, cls, nombre, _ in CATS:
        act = sorted(h[y + '_act'], key=lambda t: -abs(t[1]))
        lista = ', '.join(f'{E(TEXTO[s])} ({pts(p)})' for s, p in act) or 'ninguna señal activa'
        det.append(f'<p><b>{E(nombre)} · {pct(h[y])}</b> · {pts(h[y + "_pts"])} puntos sobre el punto de partida. <span>{lista}</span></p>')
    return f'''
      <details class="row">
        <summary><span class="row-name"><b>{E(h['desc'])}</b><small>{E(h['brand'].split(' (')[0])} · {E(h['seg'] or 'sin segmento')} · Consensus 3M {miles(h['c3'])} uds</small></span>{celdas}</summary>
        <div class="row-det"><p class="lim">Consensus de noviembre a enero: <b>{miles(h['c3'])} uds</b>. Más bajo si vende menos de {miles(.8 * h['c3'])} · mucho más bajo, menos de {miles(.5 * h['c3'])} · más alto, más de {miles(1.2 * h['c3'])} · mucho más alto, más de {miles(1.5 * h['c3'])}.</p>{''.join(det)}</div>
      </details>'''


TEXTO = {}
for y in D['categorias']:
    for s in D['categorias'][y]['senales']:
        TEXTO[s['id']] = s['texto']


ej = next(h for h in D['hoy'] if 'EDPI PRFM 100 ML INTENSE' in h['desc'])
ej_act = sorted(ej['Y_bajo_act'], key=lambda t: -t[1])
EJLIST = ''.join(f'<li><span>{E(TEXTO[s_])}</span><b>{pts(p)}</b></li>' for s_, p in ej_act)
cB = D['categorias']['Y_bajo']
EJDESC = E(ej['desc']); EJC3 = miles(ej['c3']); EJLIM = miles(0.8 * ej['c3']); EJINI = pct(cB['inicio'])
EJPTS = pts(ej['Y_bajo_pts']); EJP = pct(ej['Y_bajo']); EJMB = pct(ej['Y_muy_bajo']); EJA = pct(ej['Y_alto']); EJMA = pct(ej['Y_muy_alto']); EJO = pct(ej['Y_orden'])
NAVCATS = ''.join(f'<a href="#{cls}"><i class="dot dot--{cls}"></i>{E(n)}</a>' for _, cls, n, _ in CATS)
CATSDEF = ''.join(f'<div><b><i class="dot dot--{cls}"></i>{E(n)}</b><span>{E(d)}</span></div>' for _, cls, n, d in CATS)
SECCIONES = ''.join(seccion(*c) for c in CATS)
NOMBRE = {y: n for y, _, n, _ in CATS}
EJEMPLOS = ''.join(f'<tr><td>{E(NOMBRE[x["cat"]])}</td><td>{E(x["desc"])}</td><td>{x["foto"]}</td><td>{pct(x["p"])}</td><td>{miles(x["c3"])}</td><td>{miles(x["a3"])}</td><td>{str(round(x["ratio"], 2)).replace(".", ",")}×</td><td class="{"si" if x["paso"] else "no"}">{"Sí" if x["paso"] else "No"}</td></tr>' for x in D['ejemplos'])
NHOY = len(D['hoy']); HEADCATS = ''.join(f'<span><i class="dot dot--{cls}"></i>{E(n)}</span>' for _, cls, n, _ in CATS)
FILAS = ''.join(fila_hoy(h) for h in D['hoy']); NCASOS = miles(D['n']); NCOD = D['codigos']

page = f'''<title>Señales de demanda Gucci</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
/* Escenarios frente al Consensus: cómo funciona, una sección por escenario, ejemplos con resultado y los códigos de hoy. */
:root {{
  --bg: #f4f6f9; --surface: #ffffff; --ink: #11151c; --ink-2: #4a5263; --muted: #6f7787; --line: #e2e6ed; --line-2: #c9cfda;
  --accent: #1f6fd6; --accent-wash: #e8f1fc;
  --bajo: #e0645c; --muybajo: #b42d2d; --alto: #3aa55a; --muyalto: #1d7a3a; --orden: #2f7be0;
  --mas: #11151c; --menos: #6f7787;
  --font: system-ui, -apple-system, "SF Pro Text", "Segoe UI", Roboto, sans-serif;
  --mono: ui-monospace, "SF Mono", "Cascadia Mono", Menlo, monospace;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg: #0e1116; --surface: #161a21; --ink: #eef1f5; --ink-2: #b8c0cc; --muted: #8b93a1; --line: #262c36; --line-2: #3a4250;
    --accent: #4b93ea; --accent-wash: #16253a; --bajo: #e8746c; --muybajo: #c94848; --alto: #4cb86a; --muyalto: #2f9a52; --orden: #4b93ea;
    --mas: #eef1f5; --menos: #8b93a1; color-scheme: dark;
  }}
}}
:root[data-theme="dark"] {{
  --bg: #0e1116; --surface: #161a21; --ink: #eef1f5; --ink-2: #b8c0cc; --muted: #8b93a1; --line: #262c36; --line-2: #3a4250;
  --accent: #4b93ea; --accent-wash: #16253a; --bajo: #e8746c; --muybajo: #c94848; --alto: #4cb86a; --muyalto: #2f9a52; --orden: #4b93ea;
  --mas: #eef1f5; --menos: #8b93a1; color-scheme: dark;
}}
* {{ box-sizing: border-box; }}
body {{ background: var(--bg); color: var(--ink); font: 15px/1.55 var(--font); }}
.wrap {{ max-width: 1100px; margin: 0 auto; padding-block: 40px 64px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); display: grid; gap: 52px; }}
h1, h2, h3, h4 {{ margin: 0; text-wrap: balance; }}
p {{ margin: 0; }}
a {{ color: var(--accent); }}
summary:focus-visible, a:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 6px; }}
.eyebrow {{ font-size: 12px; font-weight: 650; letter-spacing: .07em; text-transform: uppercase; color: var(--ink-2); display: flex; align-items: center; gap: 8px; }}
.dot {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%; }}
.dot--bajo {{ background: var(--bajo); }} .dot--muybajo {{ background: var(--muybajo); }} .dot--alto {{ background: var(--alto); }}
.dot--muyalto {{ background: var(--muyalto); }} .dot--orden {{ background: var(--orden); }}
.intro {{ display: grid; gap: 16px; }}
.intro h1 {{ font-size: clamp(30px, 5vw, 44px); line-height: 1.08; letter-spacing: -.02em; font-weight: 750; }}
.lede {{ font-size: 17px; color: var(--ink-2); max-width: 72ch; }}
.nav {{ display: flex; flex-wrap: wrap; gap: 8px; }}
.nav a {{ display: inline-flex; align-items: center; gap: 8px; padding: 7px 12px; border: 1px solid var(--line-2); border-radius: 999px; color: var(--ink); text-decoration: none; font-weight: 550; background: var(--surface); }}
.nav a:hover {{ border-color: var(--accent); }}
.block {{ display: grid; gap: 18px; scroll-margin-top: 16px; }}
.block > header {{ display: grid; gap: 8px; max-width: 76ch; }}
.block h2 {{ font-size: 25px; letter-spacing: -.01em; }}
.block > header p {{ color: var(--ink-2); }}

/* Cómo funciona */
.steps {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }}
.step {{ background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: 16px 18px; display: grid; gap: 6px; align-content: start; }}
.step b {{ font-size: 15px; }}
.step p {{ font-size: 14px; color: var(--ink-2); }}
.cats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 10px; }}
.cats div {{ background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 12px 14px; display: grid; gap: 4px; }}
.cats b {{ display: flex; align-items: center; gap: 8px; }}
.cats span {{ font-size: 13px; color: var(--ink-2); }}
.weights {{ display: flex; flex-wrap: wrap; gap: 8px 22px; font-size: 14px; color: var(--ink-2); }}
.weights b {{ color: var(--ink); }}
.example {{ background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 20px 22px; display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(0, 1fr); gap: 20px 28px; }}
.example h3 {{ font-size: 18px; }}
.example p {{ color: var(--ink-2); font-size: 14px; }}
.ex-list {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 6px; }}
.ex-list li {{ display: grid; grid-template-columns: 1fr auto; gap: 12px; font-size: 14px; padding-bottom: 6px; border-bottom: 1px solid var(--line); }}
.ex-list b {{ font-variant-numeric: tabular-nums; }}
.ex-sum {{ display: grid; gap: 4px; align-content: start; }}
.ex-big {{ font-size: 40px; font-weight: 750; letter-spacing: -.02em; line-height: 1; }}

/* Secciones por categoría */
.cat {{ display: grid; gap: 16px; scroll-margin-top: 16px; padding-top: 4px; }}
.cat-head {{ display: grid; gap: 8px; }}
.cat-head h3 {{ font-size: 22px; letter-spacing: -.01em; }}
.cat-stats {{ display: flex; flex-wrap: wrap; gap: 6px 22px; font-size: 14px; color: var(--ink-2); }}
.cat-stats b {{ color: var(--ink); }}
.cols {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }}
.col {{ background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 16px 18px; display: grid; gap: 12px; align-content: start; }}
.col h4 {{ font-size: 14px; color: var(--ink-2); font-weight: 650; }}
.sc-list {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 10px; }}
.sc {{ display: grid; grid-template-columns: 74px 1fr; gap: 12px; align-items: start; padding-top: 10px; border-top: 1px solid var(--line); }}
.sc:first-child {{ border-top: 0; padding-top: 0; }}
.sc-pts {{ display: grid; justify-items: start; gap: 2px; }}
.sc-pts b {{ font-size: 20px; font-variant-numeric: tabular-nums; letter-spacing: -.01em; }}
.sc-pts span {{ font-size: 11px; font-weight: 650; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); }}
.cat--bajo .sc--mas .sc-pts b {{ color: var(--bajo); }} .cat--muybajo .sc--mas .sc-pts b {{ color: var(--muybajo); }}
.cat--alto .sc--mas .sc-pts b {{ color: var(--alto); }} .cat--muyalto .sc--mas .sc-pts b {{ color: var(--muyalto); }}
.cat--orden .sc--mas .sc-pts b {{ color: var(--orden); }}
.sc--menos .sc-pts b {{ color: var(--menos); }}
.sc-body {{ display: grid; gap: 4px; min-width: 0; }}
.sc-txt {{ font-size: 14.5px; }}
.sc-meta {{ display: flex; flex-wrap: wrap; gap: 4px 10px; font-size: 12.5px; color: var(--ink-2); align-items: center; }}
.tag {{ font-size: 11.5px; border: 1px solid var(--line-2); border-radius: 6px; padding: 1px 6px; color: var(--ink-2); }}
.sc-nota {{ font-size: 12.5px; color: var(--muted); }}
.conv {{ background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 16px 18px; display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 16px 24px; align-items: start; }}
.mini {{ font-size: 12px; font-weight: 650; letter-spacing: .06em; text-transform: uppercase; color: var(--ink-2); margin-bottom: 8px; }}
.scale {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }}
.scale span {{ background: var(--bg); border-radius: 8px; padding: 6px 8px; display: grid; font-size: 14px; font-variant-numeric: tabular-nums; }}
.scale b {{ font-size: 12px; color: var(--ink-2); font-weight: 600; }}
.table-wrap {{ overflow-x: auto; }}
table {{ border-collapse: collapse; width: 100%; font-size: 13.5px; }}
th, td {{ text-align: left; padding: 7px 10px; border-bottom: 1px solid var(--line); font-variant-numeric: tabular-nums; }}
th {{ font-size: 11.5px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); font-weight: 650; }}
tr:last-child td {{ border-bottom: 0; }}

/* Hoy */
.hoy {{ background: var(--surface); border: 1px solid var(--line); border-radius: 16px; overflow-x: auto; }}
.hoy-in {{ min-width: 860px; }}
.hoy-head, .row summary {{ display: grid; grid-template-columns: minmax(240px, 1.6fr) repeat(5, minmax(96px, 1fr)); gap: 10px; align-items: center; padding: 10px 16px; }}
.hoy-head {{ font-size: 11.5px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); font-weight: 650; border-bottom: 1px solid var(--line); }}
.hoy-head span {{ display: flex; align-items: center; gap: 6px; }}
.row {{ border-bottom: 1px solid var(--line); }}
.row:last-child {{ border-bottom: 0; }}
.row summary {{ cursor: pointer; list-style: none; }}
.row summary::-webkit-details-marker {{ display: none; }}
.row summary:hover {{ background: var(--bg); }}
.row-name {{ display: grid; min-width: 0; }}
.row-name b {{ font-size: 13.5px; font-weight: 600; overflow-wrap: anywhere; }}
.row-name small {{ font-size: 12px; color: var(--muted); }}
.m {{ position: relative; height: 24px; border-radius: 6px; background: var(--bg); overflow: hidden; display: flex; align-items: center; }}
.m i {{ position: absolute; inset: 0 auto 0 0; opacity: .32; }}
.m b {{ position: relative; padding-left: 8px; font-size: 13px; font-variant-numeric: tabular-nums; }}
.m--bajo i {{ background: var(--bajo); }} .m--muybajo i {{ background: var(--muybajo); }} .m--alto i {{ background: var(--alto); }}
.m--muyalto i {{ background: var(--muyalto); }} .m--orden i {{ background: var(--orden); }}
.row-det {{ padding: 4px 16px 14px; display: grid; gap: 6px; font-size: 13.5px; }}
.row-det span {{ color: var(--ink-2); }}

/* Hipótesis */
.hyp {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 12px; }}
.hyp div {{ background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: 16px 18px; display: grid; gap: 6px; align-content: start; }}
.hyp b {{ font-size: 15px; }}
.hyp p {{ font-size: 14px; color: var(--ink-2); }}
.verdict {{ justify-self: start; font-size: 11.5px; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; padding: 3px 8px; border-radius: 6px; background: var(--accent-wash); color: var(--accent); }}
details.method {{ background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 4px 20px; }}
details.method summary {{ cursor: pointer; font-weight: 650; padding: 12px 0; }}
details.method ul {{ margin: 0 0 16px; padding-left: 20px; display: grid; gap: 8px; color: var(--ink-2); max-width: 86ch; }}
footer {{ font-size: 13px; color: var(--muted); }}
.card-t {{ background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 8px 12px; }}
.t-ej {{ min-width: 760px; }}
td.si {{ color: var(--alto); font-weight: 700; }} td.no {{ color: var(--bajo); font-weight: 700; }}
.lim {{ color: var(--ink-2); }} .lim b {{ color: var(--ink); }}
@media (max-width: 820px) {{
  .steps, .cols, .conv, .example {{ grid-template-columns: 1fr; }}
}}
@media (max-width: 480px) {{
  .sc {{ grid-template-columns: 60px 1fr; }}
  .scale {{ grid-template-columns: repeat(2, 1fr); }}
}}
</style>

<div class="wrap">
  <header class="intro">
    <p class="eyebrow">Gucci · regulares · Consensus de la foto frente a lo que se vende</p>
    <h1>Señales de demanda Gucci</h1>
    <p class="lede">Para cada código, cinco probabilidades sobre el Consensus de la última foto para los próximos 3 meses: que lo vendido quede más bajo, mucho más bajo, más alto o mucho más alto que el Consensus, y que llegue una orden que el Consensus no tiene. Cada señal que se cumple suma o resta puntos según lo clara que es, y los puntos se convierten en probabilidad.</p>
    <nav class="nav" aria-label="Secciones">
      <a href="#como">Cómo funciona</a>
      {NAVCATS}
      <a href="#ejemplos">¿Acertó?</a>
      <a href="#hoy">Códigos hoy</a>
      <a href="#hipotesis">Tus hipótesis</a>
    </nav>
  </header>

  <section class="block" id="como">
    <header>
      <h2>Cómo funciona</h2>
      <p>La referencia es el Consensus - Final de cada foto para los 3 meses siguientes (el mes en curso no cuenta). Las cinco probabilidades son independientes y no suman 100 %: un código puede tener a la vez un 40 % de quedar por debajo y un 30 % de recibir una orden no prevista.</p>
    </header>
    <div class="cats">{CATSDEF}</div>
    <div class="steps">
      <div class="step"><b>1. Se revisan las señales</b><p>Trends de sell-in y de sell-out, cómo va el código frente a su casa, brand y línea, su calendario de pedidos, su contexto (cortes, lanzamientos, One Shots) y el propio Consensus frente a la realidad: frente a su ritmo, al año pasado, al trend de sell-in y EPOS, el peso del DA y las revisiones.</p></div>
      <div class="step"><b>2. Se suman los puntos</b><p>Cada escenario tiene sus señales y sus pesos. Una misma señal puede sumar en un escenario y restar en otro. Los puntos se suman al punto de partida del escenario.</p></div>
      <div class="step"><b>3. Puntos → probabilidad</b><p>La suma se convierte en probabilidad con la tabla de cada escenario. Las tablas se comprobaron con lo que pasó de verdad, en códigos y fotos que el modelo no había visto.</p></div>
    </div>
    <p class="weights"><span><b>Ligera</b> 1–3 puntos</span><span><b>Moderada</b> 4–7 puntos</span><span><b>Muy clara</b> 8 puntos o más</span><span>Los puntos negativos frenan el escenario.</span></p>
    <article class="example">
      <div>
        <p class="eyebrow">Ejemplo real · foto 2026.M10</p>
        <h3>{EJDESC}</h3>
        <p>Consensus para noviembre-enero: <b>{EJC3} uds</b>. Para «real más bajo» (vender menos de {EJLIM} uds) parte del {EJINI} y estas señales están activas hoy:</p>
        <ul class="ex-list">{EJLIST}</ul>
      </div>
      <div class="ex-sum">
        <p class="mini">Total</p>
        <p class="ex-big">{EJPTS} puntos</p>
        <p>Con {EJPTS} puntos, la probabilidad de vender menos de {EJLIM} uds es del <b>{EJP}</b>.</p>
        <p>El mismo código en los otros escenarios: mucho más bajo {EJMB}, más alto {EJA}, mucho más alto {EJMA}, orden no prevista {EJO}.</p>
      </div>
    </article>
  </section>

  {SECCIONES}

  <section class="block" id="ejemplos">
    <header>
      <h2>¿Acertó? Ejemplos de 2026</h2>
      <p>Para cada escenario, los dos casos con más probabilidad en las fotos de 2026 (códigos con un Consensus de al menos 3.000 uds) y lo que pasó. Una probabilidad alta no es una certeza: también hay fallos.</p>
    </header>
    <div class="card-t"><div class="table-wrap"><table class="t-ej">
      <thead><tr><th>Escenario</th><th>Código</th><th>Foto</th><th>Probabilidad</th><th>Consensus 3M</th><th>Vendido</th><th>Real / Consensus</th><th>¿Pasó?</th></tr></thead>
      <tbody>{EJEMPLOS}</tbody></table></div></div>
  </section>

  <section class="block" id="hoy">
    <header>
      <h2>Códigos hoy (foto 2026.M10, noviembre a enero)</h2>
      <p>Los {NHOY} regulares con más de un año de vida y Consensus, ordenados por su Consensus de los próximos 3 meses. Pulsa un código para ver los umbrales en unidades y qué señales tiene activas en cada escenario.</p>
    </header>
    <div class="hoy"><div class="hoy-in">
      <div class="hoy-head"><span>Código</span>{HEADCATS}</div>
      {FILAS}
    </div></div>
  </section>

  <section class="block" id="hipotesis">
    <header>
      <h2>Tus hipótesis y qué dicen los datos</h2>
      <p>Medidas frente al Consensus. Una señal solo lleva peso si empuja en la misma dirección en las fotos de 2025 y en las de 2026 (o, si usa EPOS, en las dos mitades de los códigos).</p>
    </header>
    <div class="hyp">
      <div><span class="verdict">Confirmada</span><b>La casa baja y el código sube</b><p>El real queda muy por debajo del Consensus solo en el 8 % de los casos (lo normal es el 26 %), y llega una orden no prevista en el 26 % (lo normal es el 16 %). El código que va contra la casa mantiene el impulso. Lleva −5 puntos en «mucho más bajo». Con su brand pasa lo mismo.</p></div>
      <div><span class="verdict">Confirmada</span><b>Momentum del sell-in</b><p>Con el sell-in de 3 meses por encima de +10 %, «mucho más bajo» baja al 16 %, «más alto» sube al 34 % y la orden no prevista al 23 %. Con el sell-in por debajo de −10 %, «mucho más bajo» sube al 33 %. No lleva peso propio porque su efecto ya lo recogen otras señales del modelo (contracorriente, máximos, canal).</p></div>
      <div><span class="verdict">Confirmada</span><b>Sell-in y sell-out hundiéndose a la vez</b><p>Si los dos caen un 30 % o más, el real queda por debajo de la mitad del Consensus en el 45 % de los casos (lo normal es el 26 %). Suma 3 puntos en «mucho más bajo».</p></div>
      <div><span class="verdict">Confirmada</span><b>El retailer se está cargando (sell-in sube, sell-out baja)</b><p>Al revés de lo que se suele pensar, no es riesgo: «mucho más bajo» baja al 17 %. El retailer que compra por encima de lo que vende suele seguir comprando unos meses.</p></div>
      <div><span class="verdict">No se puede confirmar</span><b>Sell-in baja y sell-out sube → el código sube</b><p>Solo pasó 21 veces en estas fotos. Hacen falta más fotos con EPOS para medirlo.</p></div>
    </div>
  </section>

  <details class="method">
    <summary>Método y límites</summary>
    <ul>
      <li><b>Datos:</b> las 10 fotos de Gucci con los 3 meses siguientes ya cerrados (2025.M09–2026.M06): {NCASOS} casos código × foto de {NCOD} regulares con más de 12 meses de vida, al menos 150 uds/año y un Consensus de al menos 60 uds en esos 3 meses. Las fotos de 2025 son de un perímetro más pequeño y su Consensus se armonizó con un factor por código.</li>
      <li><b>Señales:</b> 113 señales en 7 familias, todas con información hasta el mes anterior a la foto: las 89 de trends y contexto y 24 de «el Consensus frente a la realidad».</li>
      <li><b>Selección:</b> solo entran las señales que empujan en la misma dirección en las fotos de 2025 y en las de 2026 (o en las dos mitades de los códigos si usan EPOS), con efecto mínimo y p &lt; 0,05. Las redundantes se descartan.</li>
      <li><b>Pesos:</b> regresión logística conjunta por escenario, con regularización para no exagerar con pocos casos. Puntos = peso × 10, redondeado. Probabilidad = punto de partida + puntos, en escala logística.</li>
      <li><b>Validación:</b> probabilidades medidas en códigos que el modelo no vio (5 grupos de códigos) y entrenando con las fotos de 2025 para predecir las de 2026. Capacidad de ordenar (AUC) entre 0,76 (real más bajo) y 0,84 (real mucho más alto); 0,5 sería azar y 1 perfecto.</li>
      <li><b>Límites:</b> solo un año de fotos, solo Gucci y solo regulares maduros. Las probabilidades por encima del 70 % tienen pocos casos. Hay que volver a calibrar con cada foto nueva.</li>
    </ul>
  </details>
  <footer>Análisis del 16/10/2026 sobre <code>data/Gucci/Consensus/</code>. Scripts en <code>analisis/scripts/</code>.</footer>
</div>
'''
open(S + '/senales-gucci.html', 'w', encoding='utf-8').write(page)
print('ok', len(page) // 1024, 'KB')
