"""Página de tarjetas de señales ponderadas: 4 movimientos + pedido grande en los próximos 3 meses."""
import html
import json
import numpy as np

S = '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad'
D = json.load(open(S + '/cartas.json'))
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
    ('Y_caida', 'caida', 'Caída', 'Vende menos de 0,8 veces lo esperable en los próximos 3 meses.'),
    ('Y_caida_fuerte', 'caidaf', 'Caída fuerte', 'Vende menos de la mitad de lo esperable en los próximos 3 meses.'),
    ('Y_subida', 'subida', 'Subida', 'Vende más de 1,2 veces lo esperable en los próximos 3 meses.'),
    ('Y_subida_fuerte', 'subidaf', 'Subida fuerte', 'Vende más de 1,5 veces lo esperable en los próximos 3 meses.'),
    ('Y_pedido3', 'pedido', 'Pedido grande', 'Algún mes de los próximos 3 llega al menos al doble de su mediana de 12 meses.'),
]
NOTAS = {
    'EP_acel': 'Contraintuitiva: cuando el sell-out se dispara (por ejemplo, una promo en tienda), el retailer vende de su stock y el sell-in de después baja.',
    'X_stock_alto': 'Contraintuitiva: un canal que se carga durante meses suele estar ganando puertas o distribución, y sigue comprando.',
    'X_st_bajo': 'El retailer está comprando por encima de lo que vende: suele seguir comprando, no frena de golpe.',
    'G_brand_destock': 'La brand lleva meses vendiendo en tienda más de lo que compra: toca reponer.',
    'O_os_campaña': 'Canibalismo: durante una campaña fuerte de One Shots, los regulares de la brand pierden.',
    'O_lanz_brand': 'Halo: tras varios lanzamientos de la brand, el resto de regulares tiende a tirar algo más.',
    'C_ly_valle': 'El valle del año pasado no se repite: el código vuelve a su nivel.',
    'C_ly_pico': 'El pico del año pasado no se repite.',
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
        <summary><span class="row-name"><b>{E(h['desc'])}</b><small>{E(h['brand'].split(' (')[0])} · {E(h['seg'] or 'sin segmento')} · {miles(h['vol12'])} uds/año</small></span>{celdas}</summary>
        <div class="row-det">{''.join(det)}</div>
      </details>'''


TEXTO = {}
for y in D['categorias']:
    for s in D['categorias'][y]['senales']:
        TEXTO[s['id']] = s['texto']

ej = next(h for h in D['hoy'] if 'MAG RG EDP 100' in h['desc'])
ej_act = sorted(ej['Y_caida_act'], key=lambda t: -t[1])
ej_list = ''.join(f'<li><span>{E(TEXTO[s])}</span><b>{pts(p)}</b></li>' for s, p in ej_act)
cC = D['categorias']['Y_caida']

page = f'''<title>Señales de demanda Gucci</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
/* Tarjetas por categoría: arriba cómo funciona, después una sección por movimiento y al final los códigos de hoy. */
:root {{
  --bg: #f4f6f9; --surface: #ffffff; --ink: #11151c; --ink-2: #4a5263; --muted: #6f7787; --line: #e2e6ed; --line-2: #c9cfda;
  --accent: #1f6fd6; --accent-wash: #e8f1fc;
  --caida: #e0645c; --caidaf: #b42d2d; --subida: #3aa55a; --subidaf: #1d7a3a; --pedido: #2f7be0;
  --mas: #11151c; --menos: #6f7787;
  --font: system-ui, -apple-system, "SF Pro Text", "Segoe UI", Roboto, sans-serif;
  --mono: ui-monospace, "SF Mono", "Cascadia Mono", Menlo, monospace;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg: #0e1116; --surface: #161a21; --ink: #eef1f5; --ink-2: #b8c0cc; --muted: #8b93a1; --line: #262c36; --line-2: #3a4250;
    --accent: #4b93ea; --accent-wash: #16253a; --caida: #e8746c; --caidaf: #c94848; --subida: #4cb86a; --subidaf: #2f9a52; --pedido: #4b93ea;
    --mas: #eef1f5; --menos: #8b93a1; color-scheme: dark;
  }}
}}
:root[data-theme="dark"] {{
  --bg: #0e1116; --surface: #161a21; --ink: #eef1f5; --ink-2: #b8c0cc; --muted: #8b93a1; --line: #262c36; --line-2: #3a4250;
  --accent: #4b93ea; --accent-wash: #16253a; --caida: #e8746c; --caidaf: #c94848; --subida: #4cb86a; --subidaf: #2f9a52; --pedido: #4b93ea;
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
.dot--caida {{ background: var(--caida); }} .dot--caidaf {{ background: var(--caidaf); }} .dot--subida {{ background: var(--subida); }}
.dot--subidaf {{ background: var(--subidaf); }} .dot--pedido {{ background: var(--pedido); }}
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
.cat--caida .sc--mas .sc-pts b {{ color: var(--caida); }} .cat--caidaf .sc--mas .sc-pts b {{ color: var(--caidaf); }}
.cat--subida .sc--mas .sc-pts b {{ color: var(--subida); }} .cat--subidaf .sc--mas .sc-pts b {{ color: var(--subidaf); }}
.cat--pedido .sc--mas .sc-pts b {{ color: var(--pedido); }}
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
.m--caida i {{ background: var(--caida); }} .m--caidaf i {{ background: var(--caidaf); }} .m--subida i {{ background: var(--subida); }}
.m--subidaf i {{ background: var(--subidaf); }} .m--pedido i {{ background: var(--pedido); }}
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
    <p class="eyebrow">Gucci · regulares · próximos 3 meses</p>
    <h1>Señales de demanda Gucci</h1>
    <p class="lede">Para cada código, cinco probabilidades separadas para los próximos 3 meses: caída, caída fuerte, subida, subida fuerte y pedido grande. Cada señal que se cumple suma o resta puntos según lo clara que es, y los puntos se convierten en probabilidad.</p>
    <nav class="nav" aria-label="Secciones">
      <a href="#como">Cómo funciona</a>
      {''.join(f'<a href="#{cls}"><i class="dot dot--{cls}"></i>{E(n)}</a>' for _, cls, n, _ in CATS)}
      <a href="#hoy">Códigos hoy</a>
      <a href="#hipotesis">Tus hipótesis</a>
    </nav>
  </header>

  <section class="block" id="como">
    <header>
      <h2>Cómo funciona</h2>
      <p>«Lo esperable» es el ritmo del código en los últimos 12 meses, ajustado por la estacionalidad de su brand el año anterior. Las cinco probabilidades son independientes: un código puede tener a la vez un 60 % de subida y un 40 % de caída.</p>
    </header>
    <div class="cats">{''.join(f'<div><b><i class="dot dot--{cls}"></i>{E(n)}</b><span>{E(d)}</span></div>' for _, cls, n, d in CATS)}</div>
    <div class="steps">
      <div class="step"><b>1. Se revisan las señales</b><p>En cada foto se mira qué señales cumple el código: trends de sell-in y de sell-out, cómo va frente a su casa, brand y línea, su calendario de pedidos y su contexto (cortes, lanzamientos, One Shots).</p></div>
      <div class="step"><b>2. Se suman los puntos</b><p>Cada categoría tiene sus propias señales y pesos. Una señal puede sumar en una categoría y restar en otra. Los puntos se suman al punto de partida de la categoría.</p></div>
      <div class="step"><b>3. Puntos → probabilidad</b><p>La suma se convierte en probabilidad con la tabla de cada categoría. Esas tablas se comprobaron con lo que pasó de verdad, en códigos que el modelo no había visto.</p></div>
    </div>
    <p class="weights"><span><b>Ligera</b> 1–3 puntos</span><span><b>Moderada</b> 4–7 puntos</span><span><b>Muy clara</b> 8 puntos o más</span><span>Los puntos negativos frenan la categoría.</span></p>
    <article class="example">
      <div>
        <p class="eyebrow">Ejemplo real · foto 2026.M10</p>
        <h3>{E(ej['desc'])}</h3>
        <p>{miles(ej['vol12'])} uds en los últimos 12 meses. Para la <b>caída</b> parte del {pct(cC['inicio'])} y estas señales están activas hoy:</p>
        <ul class="ex-list">{ej_list}</ul>
      </div>
      <div class="ex-sum">
        <p class="mini">Total de caída</p>
        <p class="ex-big">{pts(ej['Y_caida_pts'])} puntos</p>
        <p>Con {pts(ej['Y_caida_pts'])} puntos la probabilidad de caída es del <b>{pct(ej['Y_caida'])}</b>.</p>
        <p>El mismo código, en las otras categorías: caída fuerte {pct(ej['Y_caida_fuerte'])}, subida {pct(ej['Y_subida'])}, subida fuerte {pct(ej['Y_subida_fuerte'])}, pedido grande {pct(ej['Y_pedido3'])}.</p>
      </div>
    </article>
  </section>

  {''.join(seccion(*c) for c in CATS)}

  <section class="block" id="hoy">
    <header>
      <h2>Códigos hoy (foto 2026.M10)</h2>
      <p>Las cinco probabilidades de los {len(D['hoy'])} regulares con más de un año de vida, ordenados por volumen. Pulsa un código para ver qué señales tiene activas en cada categoría.</p>
    </header>
    <div class="hoy"><div class="hoy-in">
      <div class="hoy-head"><span>Código</span>{''.join(f'<span><i class="dot dot--{cls}"></i>{E(n)}</span>' for _, cls, n, _ in CATS)}</div>
      {''.join(fila_hoy(h) for h in D['hoy'])}
    </div></div>
  </section>

  <section class="block" id="hipotesis">
    <header>
      <h2>Tus hipótesis y qué dicen los datos</h2>
      <p>Una señal solo entra con peso si empuja en la misma dirección en los dos periodos de datos (2023-24 y 2025-26) o, si usa EPOS, en las dos mitades de los códigos.</p>
    </header>
    <div class="hyp">
      <div><span class="verdict">No se puede confirmar</span><b>Sell-in baja y sell-out sube → el código va a subir</b><p>Solo pasó 26 veces en los datos y el efecto cambia de signo entre las dos mitades. Hacen falta más fotos con EPOS. A nivel de brand sí funciona: si la brand vende en tienda más de lo que compra, sus códigos suben (+5 puntos en subida).</p></div>
      <div><span class="verdict">Solo en 2025-26</span><b>La casa baja y el código sube → riesgo de caída</b><p>En 2025-26, el código que sube a contracorriente de la casa tiene <b>menos</b> caída (53 % frente al 61 %). En 2023-24 no tenía efecto. Por eso no lleva peso todavía.</p></div>
      <div><span class="verdict">Solo en 2025-26</span><b>Momentum: si el sell-in sube, seguirá subiendo</b><p>Con sell-in de 3 meses por encima de +10 %, la caída baja al 53 % y la subida sube al 25 %. Pero el efecto solo aparece en 2025-26. Lo que sí es estable: estar en mínimos del año o con el último mes muy flojo anuncia caída.</p></div>
      <div><span class="verdict">Sí, con matiz</span><b>Sell-in y sell-out cayendo a la vez</b><p>Si los dos se hunden (−30 % o peor), la caída suma 6 puntos y la caída fuerte 4. Si solo bajan un poco (−10 %), no anuncia caída, pero sí menos pedidos grandes (−5 puntos).</p></div>
      <div><span class="verdict">Al revés de lo esperado</span><b>Canal cargado → caída</b><p>Cuando el retailer compra más de lo que vende durante meses, lo normal es que <b>siga comprando</b>: suma 7 puntos de subida fuerte y 7 de pedido grande, y resta caída fuerte.</p></div>
    </div>
  </section>

  <details class="method">
    <summary>Método y límites</summary>
    <ul>
      <li><b>Datos:</b> 14 fotos de Gucci (2025.M09–2026.M10). 3.085 casos código × mes de 142 regulares con más de 12 meses de vida y al menos 150 uds/año, con decisiones de 2023.M06 a 2026.M06. El cambio de perímetro de la foto 2026.M02 está corregido.</li>
      <li><b>Señales:</b> 89 señales en 6 familias (trend de sell-in, trend de sell-out, sell-in frente a sell-out, código frente a su grupo, pedidos y calendario, supply y cartera), todas con información hasta el mes anterior a la foto.</li>
      <li><b>Selección:</b> solo entran las señales que empujan en la misma dirección en las dos partes de los datos, con efecto mínimo y p &lt; 0,01. Las redundantes (correlación &gt; 0,6) se descartan.</li>
      <li><b>Pesos:</b> regresión logística conjunta por categoría, para no contar dos veces dos señales que dicen lo mismo. Puntos = peso × 10, redondeado. Probabilidad = punto de partida + puntos, en escala logística.</li>
      <li><b>Validación:</b> probabilidades medidas en códigos que el modelo no vio (5 grupos de códigos) y entrenando en 2023-24 para predecir 2025-26. Capacidad de ordenar (AUC) entre 0,69 (pedido grande) y 0,78 (caída fuerte); 0,5 sería azar y 1 sería perfecto.</li>
      <li><b>Límites:</b> solo Gucci y regulares maduros; las señales de EPOS solo tienen datos desde 2024.M10; las probabilidades altas de subida (más del 50 %) tienen pocos casos. Hay que volver a calibrar cada trimestre y en cada casa.</li>
    </ul>
  </details>
  <footer>Análisis del 16/10/2026 sobre <code>data/Gucci/Consensus/</code>. Scripts en <code>analisis/scripts/</code>.</footer>
</div>
'''
open(S + '/senales-gucci.html', 'w', encoding='utf-8').write(page)
print('ok', len(page) // 1024, 'KB')
