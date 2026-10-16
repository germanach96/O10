"""Página del libro de señales orientada al KPI (WAPE y SPP). Lee los resultados calculados y escribe el HTML."""
import html
import json
import numpy as np
import pandas as pd

S = '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad'
K = json.load(open(S + '/kpi_html.json'))
F = pd.read_pickle(S + '/senales_final.pkl')
C = pd.read_pickle(S + '/confluencia_final.pkl')
E = html.escape


def pct(x, d=0, signo=False):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return '—'
    s = f'{x * 100:+.{d}f}' if signo else f'{x * 100:.{d}f}'
    return s.replace('.', ',').replace('-', '−') + ' %'


def num(x, d=0):
    return f'{x:,.{d}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def decimos(p):
    return f'{p * 10:.0f} de cada 10'.replace('.', ',')


B = K['base']
DA = {round(r['rho'], 2): r for r in K['da']}
D7 = DA[0.7]
# Reglas: lanzamiento x0,7 y combinación (de kpi_lanz.py)
LZ = dict(w25=0.977, s25=-0.275, w26=0.543, s26=-0.040)
JU = dict(w25=0.888, s25=-0.167, w26=0.519, s26=0.024)
dec = K['dec']
ej = K['ej'][0]


def tile(label, w, s, nota, clase=''):
    return (f'<div class="tile {clase}"><p class="tile-label">{E(label)}</p>'
            f'<p class="tile-kpi"><span>WAPE90</span><b>{pct(w, 1)}</b></p>'
            f'<p class="tile-kpi"><span>SPP3</span><b>{pct(s, 1, True)}</b></p>'
            f'<p class="tile-note">{E(nota)}</p></div>')


def barras_tam():
    filas = []
    for t in K['tam']:
        tip_v = f"{t['t']}: {pct(t['vol'])} del volumen, {t['cod']} códigos"
        tip_e = f"{t['t']}: {pct(t['err'])} del error"
        filas.append(f'''
        <div class="pair">
          <p class="pair-label">{E(t['t'])}<span>{t['cod']} códigos</span></p>
          <div class="pair-bars">
            <div class="hbar"><span class="track" tabindex="0" data-tip="{E(tip_v)}"><span class="bar bar--vol" style="width:{t['vol'] * 100:.1f}%"></span></span><span class="hval">{pct(t['vol'])}</span></div>
            <div class="hbar"><span class="track" tabindex="0" data-tip="{E(tip_e)}"><span class="bar bar--err" style="width:{t['err'] * 100:.1f}%"></span></span><span class="hval">{pct(t['err'])}</span></div>
          </div>
        </div>''')
    return ''.join(filas)


def tabla_da():
    filas = []
    for rho in [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4]:
        r = DA[rho]
        cls = ' class="hl"' if rho == 0.7 else ''
        lab = 'Todo el DA (hoy)' if rho == 1.0 else f'El {rho * 100:.0f} % del DA'
        filas.append(f'<tr{cls}><td>{lab}</td><td>{pct(r["w26"], 1)}</td><td>{pct(r["s26"], 1, True)}</td><td>{pct(r["w25"], 1)}</td><td>{pct(r["s25"], 1, True)}</td></tr>')
    return ''.join(filas)


# Alertas por código: acierto (de la confluencia o de la señal) y efecto en el KPI 2026
CONF = {r['k']: r for r in K['reglas']}
def p_conf(match, k):
    return float(C[C.evento.str.startswith(match) & (C['señales'] == k)].p.iloc[0])
def base_ev(match):
    return float(F[F.evento.str.startswith(match)].base.iloc[0])
ALERTAS = [
    ('C', 'Caída', 'CAÍDA', p_conf('CAÍDA', '2+'), base_ev('CAÍDA'), 'Un código que hoy va bien se va a hundir en 3 meses (vende menos de la mitad de lo esperable).',
     'No fabricar ni empujar stock de ese código para los próximos 3 meses.'),
    ('M', 'Muerte', 'MUERTE', p_conf('MUERTE', '2+'), base_ev('MUERTE'), 'Un código que hoy va bien va a dejar de venderse en 6 meses (menos del 20 % de su ritmo).',
     'No reponer. Ponerlo en la lista de phase-out y pasar el volumen al hermano sano de su línea.'),
    ('V', 'Mes vacío', 'MES VACÍO', float(F[F['señal'].str.startswith('V1')].p.iloc[0]), base_ev('MES VACÍO'),
     'El último mes vino a cero y no hubo cortes: el mes siguiente también vendrá vacío.',
     'Revisarlo código a código. No poner a cero de forma automática: en códigos grandes que piden un mes sí y otro no, empeora el WAPE.'),
    ('U', 'Subida fuerte', 'SUBIDA', p_conf('SUBIDA', '2+'), base_ev('SUBIDA'), 'Un código va a vender más de 1,5 veces lo esperable en 3 meses.',
     'Asegurar supply. No recortar el forecast de ese código.'),
    ('G', 'Pedido grande', 'PEDIDO GRANDE', p_conf('PEDIDO GRANDE', '2+'), base_ev('PEDIDO GRANDE'), 'Viene un pedido grande el mes que viene (al menos 2 veces la mediana del código).',
     'Asegurar stock y supply para ese mes.'),
]

SEN = {
    'C1': 'Errático, pequeño (menos de 4.000 uds/año) y su último mes fue menos del 30 % de su media',
    'C2': 'Sube 4 veces más que su brand y es errático',
    'C3': 'Sube 6 veces más que su línea mientras la línea cae un 40 % o más',
    'C4': 'Su brand está en campaña fuerte de One Shots y el código es de 150 ml o más',
    'C5': 'Muy errático y pequeño',
    'M1': 'Pequeño, errático y su línea cae un 30 % o más',
    'M2': 'Es un Rabbit y su EPOS va al menos un 25 % peor que el de su brand',
    'M3': 'Muy errático y acaba de recibir un pedido grande (pico aislado)',
    'M4': 'Es de 150 ml o más y acaba de recibir un pedido grande',
    'M5': 'Pequeño y su línea cae un 30 % o más',
    'G1': 'Pide a saltos, hizo un pedido grande hace 1-2 meses y tuvo cortes de supply',
    'G2': 'Tuvo cortes de más de 2 meses de venta y su EPOS se está vaciando',
    'G3': 'Su brand cae pero empuja One Shots, y el código pide todos los meses',
    'G4': 'El mes que viene es septiembre y el código pide todos los meses',
    'U1': 'Encadena pedidos grandes (3 o más en un año) y va a 1,5 veces su ritmo',
    'U2': 'Pedía a saltos y se está reactivando, sin campaña de One Shots en su brand',
    'U3': 'El retailer compra bastante más de lo que vende y hubo un pedido grande reciente',
    'U4': 'Tuvo cortes de supply y el EPOS de su brand cae',
    'V1': 'Su último mes vino a cero y no hubo cortes de supply',
    'V2': 'Su último mes vino a cero y lleva un año cayendo',
    'V3': 'Su último mes vino a cero pero por cortes de supply (aquí suele volver)',
}


def alertas_tabla():
    filas = []
    for k, nombre, match, p, base, que, accion in ALERTAS:
        r = CONF[k]
        filas.append(f'''<tr>
          <td><b>{E(nombre)}</b><span class="cell-sub">{E(que)}</span></td>
          <td><b>{decimos(p)}</b><span class="cell-sub">sin señal: {decimos(base)}</span></td>
          <td>{r['codigos']}<span class="cell-sub">{pct(r['vol'], 1)} del volumen</span></td>
          <td>{pct(r['w1'] - r['w0'], 1, True).replace('%', 'pp').replace(' pp', ' pp')}</td>
          <td>{E(accion)}</td></tr>''')
    return ''.join(filas)


def alertas_detalle():
    bloques = []
    for k, nombre, match, p, base, que, accion in ALERTAS:
        g = F[F.evento.str.startswith(match)]
        c = C[C.evento.str.startswith(match)].set_index('señales')
        items = []
        for _, r in g.iterrows():
            sid = r['señal'].split(' ')[0]
            items.append(f'<li><span class="sig-id">{sid}</span><span class="sig-txt">{E(SEN[sid])}</span><span class="sig-p">{decimos(r.p)}</span></li>')
        bloques.append(f'''
      <div class="alerta">
        <div class="alerta-head"><h4>{E(nombre)}</h4><p>{E(que)}</p></div>
        <div class="conf">
          <div><span>Sin señales</span><b>{decimos(c.loc['0'].p)}</b></div>
          <div><span>1 señal</span><b>{decimos(c.loc['1'].p)}</b></div>
          <div class="conf-em"><span>2 o más</span><b>{decimos(c.loc['2+'].p)}</b></div>
        </div>
        <p class="alerta-sub">Señales que cuentan (y cuántas veces acierta cada una sola):</p>
        <ul class="sig-ul">{''.join(items)}</ul>
        <p class="alerta-acc"><b>Qué hacer:</b> {E(accion)}</p>
      </div>''')
    return ''.join(bloques)


page = f'''<title>Señales de demanda Gucci</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
/* Informe de lectura: arriba el KPI y qué lo mueve; abajo las alertas por código. Una columna, bloques con tablas y barras. */
:root {{
  --bg: #f4f6f9; --surface: #ffffff; --ink: #11151c; --ink-2: #4a5263; --muted: #6f7787; --line: #e2e6ed; --line-2: #c9cfda;
  --accent: #1f6fd6; --accent-wash: #e8f1fc; --vol: #b9c1cd; --good: #0f7a0f; --good-wash: #e7f4e7; --bad: #c43535; --bad-wash: #fbeaea;
  --font: system-ui, -apple-system, "SF Pro Text", "Segoe UI", Roboto, sans-serif;
  --mono: ui-monospace, "SF Mono", "Cascadia Mono", Menlo, monospace;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg: #0e1116; --surface: #161a21; --ink: #eef1f5; --ink-2: #b8c0cc; --muted: #8b93a1; --line: #262c36; --line-2: #3a4250;
    --accent: #4b93ea; --accent-wash: #16253a; --vol: #4a5262; --good: #4cc24c; --good-wash: #15291a; --bad: #ee7a7a; --bad-wash: #2e1b1d; color-scheme: dark;
  }}
}}
:root[data-theme="dark"] {{
  --bg: #0e1116; --surface: #161a21; --ink: #eef1f5; --ink-2: #b8c0cc; --muted: #8b93a1; --line: #262c36; --line-2: #3a4250;
  --accent: #4b93ea; --accent-wash: #16253a; --vol: #4a5262; --good: #4cc24c; --good-wash: #15291a; --bad: #ee7a7a; --bad-wash: #2e1b1d; color-scheme: dark;
}}
* {{ box-sizing: border-box; }}
body {{ background: var(--bg); color: var(--ink); font: 15px/1.55 var(--font); }}
.wrap {{ max-width: 1040px; margin: 0 auto; padding-block: 40px 64px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  display: grid; gap: 52px; }}
h1, h2, h3, h4 {{ margin: 0; text-wrap: balance; }}
p {{ margin: 0; }}
b {{ font-weight: 650; }}
a {{ color: var(--accent); }}
[tabindex]:focus-visible, summary:focus-visible, a:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 4px; }}
.eyebrow {{ font-size: 12px; font-weight: 650; letter-spacing: .07em; text-transform: uppercase; color: var(--ink-2); }}
.intro {{ display: grid; gap: 16px; }}
.intro h1 {{ font-size: clamp(30px, 5vw, 44px); line-height: 1.08; letter-spacing: -.02em; font-weight: 750; }}
.lede {{ font-size: 17px; color: var(--ink-2); max-width: 70ch; }}
.qs {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; counter-reset: q; }}
.qs a {{ display: grid; gap: 2px; padding: 12px 14px; background: var(--surface); border: 1px solid var(--line); border-radius: 12px; color: var(--ink); text-decoration: none; }}
.qs a:hover {{ border-color: var(--accent); }}
.qs b {{ font-size: 15px; }}
.qs span {{ font-size: 13px; color: var(--ink-2); }}

.block {{ display: grid; gap: 20px; scroll-margin-top: 16px; }}
.block > header {{ display: grid; gap: 8px; max-width: 74ch; }}
.block h2 {{ font-size: 25px; letter-spacing: -.01em; }}
.block > header p {{ color: var(--ink-2); }}
.card {{ background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 20px 22px; display: grid; gap: 14px; }}

/* KPI */
.tiles {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }}
.tile {{ background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 18px 20px; display: grid; gap: 6px; align-content: start; }}
.tile--good {{ background: var(--good-wash); border-color: transparent; }}
.tile-label {{ font-size: 13px; font-weight: 650; color: var(--ink-2); }}
.tile-kpi {{ display: flex; align-items: baseline; justify-content: space-between; gap: 12px; }}
.tile-kpi span {{ font-size: 13px; color: var(--ink-2); }}
.tile-kpi b {{ font-size: 28px; font-weight: 750; letter-spacing: -.02em; }}
.tile-note {{ font-size: 12.5px; color: var(--muted); }}
.gloss {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 10px; }}
.gloss div {{ background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 12px 14px; display: grid; gap: 4px; }}
.gloss b {{ font-size: 14px; }}
.gloss span {{ font-size: 13.5px; color: var(--ink-2); }}

/* Dónde se pierde */
.facts {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
.fact {{ background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: 16px 18px; display: grid; gap: 6px; align-content: start; }}
.fact-big {{ font-size: 30px; font-weight: 750; letter-spacing: -.02em; line-height: 1.1; }}
.fact-big small {{ font-size: 14px; font-weight: 500; color: var(--ink-2); letter-spacing: 0; }}
.fact p {{ font-size: 14px; color: var(--ink-2); }}
.fact p b {{ color: var(--ink); }}
.legend {{ display: flex; flex-wrap: wrap; gap: 6px 18px; font-size: 12.5px; color: var(--ink-2); }}
.legend span {{ display: inline-flex; align-items: center; gap: 6px; }}
.key {{ display: inline-block; width: 14px; height: 10px; border-radius: 0 3px 3px 0; }}
.key--vol {{ background: var(--vol); }} .key--err {{ background: var(--accent); }}
.pair {{ display: grid; grid-template-columns: minmax(150px, 220px) 1fr; gap: 6px 16px; align-items: center; padding: 10px 0; }}
.pair + .pair {{ border-top: 1px solid var(--line); }}
.pair-label {{ font-size: 14px; font-weight: 600; display: grid; }}
.pair-label span {{ font-size: 12px; font-weight: 400; color: var(--muted); }}
.pair-bars {{ display: grid; gap: 4px; min-width: 0; }}
.hbar {{ display: grid; grid-template-columns: 1fr 48px; gap: 10px; align-items: center; }}
.track {{ position: relative; height: 16px; display: flex; align-items: center; }}
.track::before {{ content: ""; position: absolute; inset: 7px 0 auto; height: 1px; background: var(--line); }}
.bar {{ position: relative; height: 12px; border-radius: 0 4px 4px 0; min-width: 2px; }}
.bar--vol {{ background: var(--vol); }} .bar--err {{ background: var(--accent); }}
.hval {{ font-size: 13px; font-weight: 600; text-align: right; font-variant-numeric: tabular-nums; }}

/* Reglas */
.rule {{ background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 22px 24px; display: grid; gap: 16px; }}
.rule-head {{ display: grid; gap: 6px; }}
.rule-tag {{ justify-self: start; font-size: 12px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: var(--good); background: var(--good-wash); padding: 4px 8px; border-radius: 6px; }}
.rule h3 {{ font-size: 21px; }}
.rule-why {{ color: var(--ink-2); max-width: 74ch; }}
.rule-res {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
.res {{ border-radius: 12px; background: var(--bg); padding: 12px 14px; display: grid; gap: 4px; }}
.res span {{ font-size: 12.5px; color: var(--ink-2); }}
.res b {{ font-size: 18px; font-variant-numeric: tabular-nums; }}
.example {{ border-left: 3px solid var(--accent); padding: 4px 0 4px 14px; display: grid; gap: 4px; font-size: 14px; color: var(--ink-2); }}
.example b {{ color: var(--ink); }}
.table-wrap {{ overflow-x: auto; }}
table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
th, td {{ text-align: left; vertical-align: top; padding: 10px 12px; border-bottom: 1px solid var(--line); }}
th {{ font-size: 11.5px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); font-weight: 650; }}
td {{ font-variant-numeric: tabular-nums; }}
tr:last-child td {{ border-bottom: 0; }}
tr.hl td {{ background: var(--accent-wash); font-weight: 650; }}
.cell-sub {{ display: block; font-size: 12.5px; color: var(--ink-2); font-weight: 400; margin-top: 2px; }}
.t-da {{ min-width: 520px; }}
.t-al {{ min-width: 760px; }}

/* Lo que no mejora */
.nots {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; }}
.not {{ background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: 16px 18px; display: grid; gap: 6px; align-content: start; }}
.not-tag {{ justify-self: start; font-size: 12px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: var(--bad); background: var(--bad-wash); padding: 4px 8px; border-radius: 6px; }}
.not b {{ font-size: 15.5px; }}
.not p {{ font-size: 14px; color: var(--ink-2); }}

/* Alertas por código */
.alertas {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 12px; }}
.alerta {{ background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: 16px 18px; display: grid; gap: 12px; align-content: start; }}
.alerta-head {{ display: grid; gap: 4px; }}
.alerta-head h4 {{ font-size: 17px; }}
.alerta-head p {{ font-size: 13.5px; color: var(--ink-2); }}
.conf {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; }}
.conf div {{ border-radius: 10px; background: var(--bg); padding: 8px 10px; display: grid; gap: 2px; }}
.conf span {{ font-size: 12px; color: var(--ink-2); }}
.conf b {{ font-size: 15px; }}
.conf-em {{ background: var(--accent-wash) !important; }}
.conf-em b {{ color: var(--accent); }}
.alerta-sub {{ font-size: 12.5px; color: var(--muted); }}
.sig-ul {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 6px; }}
.sig-ul li {{ display: grid; grid-template-columns: auto 1fr auto; gap: 8px; align-items: baseline; font-size: 13.5px; }}
.sig-id {{ font: 600 11px/1 var(--mono); color: var(--ink-2); border: 1px solid var(--line-2); border-radius: 5px; padding: 3px 5px; }}
.sig-txt {{ color: var(--ink); }}
.sig-p {{ font-size: 12px; color: var(--ink-2); white-space: nowrap; font-variant-numeric: tabular-nums; }}
.alerta-acc {{ font-size: 13.5px; color: var(--ink-2); border-top: 1px solid var(--line); padding-top: 10px; }}
.alerta-acc b {{ color: var(--ink); }}
details {{ background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 4px 20px; }}
summary {{ cursor: pointer; font-weight: 650; padding: 12px 0; }}
details ul {{ margin: 0 0 16px; padding-left: 20px; display: grid; gap: 8px; color: var(--ink-2); max-width: 84ch; }}
footer {{ font-size: 13px; color: var(--muted); }}
.tip {{ position: fixed; z-index: 20; max-width: 280px; padding: 8px 10px; border-radius: 8px; background: var(--ink); color: var(--bg); font-size: 12.5px; line-height: 1.4; pointer-events: none; box-shadow: 0 6px 20px rgba(0,0,0,.18); }}
@media (max-width: 760px) {{
  .tiles {{ grid-template-columns: 1fr; }}
  .facts {{ grid-template-columns: 1fr; }}
  .pair {{ grid-template-columns: 1fr; }}
  .rule-res {{ grid-template-columns: 1fr; }}
  .rule, .card {{ padding: 18px 16px; }}
}}
</style>

<div class="wrap">
  <header class="intro">
    <p class="eyebrow">Gucci · regulares · forecast frente a lo vendido</p>
    <h1>Señales de demanda Gucci</h1>
    <p class="lede">El objetivo es un buen KPI: bajar el WAPE y dejar el SPP entre −5 % y +5 %. Esta página responde a tres preguntas con los datos de las 14 fotos: dónde se pierde el KPI, qué cambio en el forecast lo mejora de verdad, y qué alertas sirven para decidir sobre códigos concretos.</p>
    <nav class="qs" aria-label="Secciones">
      <a href="#perdida"><b>1. Dónde se pierde el KPI</b><span>Qué códigos y qué meses generan el error</span></a>
      <a href="#mejora"><b>2. Qué lo mejora</b><span>Dos reglas probadas en datos que no vieron</span></a>
      <a href="#no"><b>3. Qué no lo mejora</b><span>Ideas que parecen buenas y no mueven el KPI</span></a>
      <a href="#alertas"><b>4. Alertas por código</b><span>Para stock, supply y phase-out</span></a>
    </nav>
  </header>

  <section class="block" id="kpi">
    <header>
      <h2>Tu KPI hoy y con las dos reglas</h2>
      <p>Regulares de Gucci, fotos 2026.M02 a 2026.M06, los 3 meses siguientes a cada foto. Es el periodo con datos limpios (ver método).</p>
    </header>
    <div class="tiles">
      {tile('Forecast real (hoy)', B['w'], B['s'], 'Lo que se comprometió en cada foto, frente a lo vendido.')}
      {tile('Con las dos reglas', JU['w26'], JU['s26'], 'Mismo forecast, aplicando las reglas 1 y 2 de la sección 2.', 'tile--good')}
      <div class="tile"><p class="tile-label">Meta del equipo</p><p class="tile-kpi"><span>WAPE90</span><b>≤ 40 %</b></p><p class="tile-kpi"><span>SPP3</span><b>±5 %</b></p><p class="tile-note">El resto del camino está en el timing de los pedidos grandes (sección 1).</p></div>
    </div>
    <div class="gloss">
      <div><b>WAPE90</b><span>Error absoluto de los meses 1 a 3 sumado (sin compensar meses ni códigos) dividido por lo vendido. Cuanto más bajo, mejor.</span></div>
      <div><b>SPP3</b><span>Lo vendido menos el forecast, dividido por lo vendido. Negativo = forecast por encima de lo vendido (sobre-forecast).</span></div>
    </div>
  </section>

  <section class="block" id="perdida">
    <header>
      <h2>1. Dónde se pierde el KPI</h2>
      <p>El WAPE se mide en unidades, así que manda el volumen. Un error grande en un código pequeño casi no cuenta; un error mediano en un código grande cuenta mucho.</p>
    </header>
    <div class="facts">
      <div class="fact"><p class="fact-big">{pct(dec['top20'])} <small>del error</small></p><p>Lo generan <b>20 códigos</b> de {dec['ncod']}. Revisar esos 20 a mano en cada foto vale más que cualquier regla general.</p></div>
      <div class="fact"><p class="fact-big">{pct(dec['pico_err'])} <small>del error</small></p><p>Sale de los <b>meses con un pedido grande</b> (2 veces la media o más), que son solo el {pct(dec['pico_filas'])} de los meses. Fallar el mes en que llega el pedido es el error más caro.</p></div>
      <div class="fact"><p class="fact-big">{pct(dec['da_err'])} <small>del error</small></p><p>Sale de los <b>meses en que el DA es más de la mitad del forecast</b>. En esos meses el forecast va un {pct(-dec['da_spp'])} por encima de lo vendido.</p></div>
      <div class="fact"><p class="fact-big">{pct(K['tam'][0]['err'])} <small>del error</small></p><p>Sale de los <b>{K['tam'][0]['cod']} códigos pequeños</b> (menos de 4.000 uds/año). No son el problema del KPI.</p></div>
    </div>
    <div class="card">
      <p class="eyebrow">Volumen frente a error, por tamaño del código</p>
      <div class="legend"><span><i class="key key--vol"></i>% del volumen vendido</span><span><i class="key key--err"></i>% del error (WAPE)</span></div>
      <div>{barras_tam()}</div>
      <p class="tile-note">Los lanzamientos (menos de 12 meses de vida) también aparecen en su tramo de tamaño. Por eso las filas suman más de 100 %.</p>
    </div>
  </section>

  <section class="block" id="mejora">
    <header>
      <h2>2. Qué mejora el KPI</h2>
      <p>Dos reglas. Cada una se calibró con las fotos de 2025 y se midió en las de 2026, y al revés. Mejoran el KPI en los dos periodos.</p>
    </header>

    <article class="rule">
      <div class="rule-head">
        <span class="rule-tag">Regla 1 · la de más impacto</span>
        <h3>Cuenta solo el 70 % del DA positivo</h3>
        <p class="rule-why">Cuando se planifica una promo o una acción (Total Demand Assumption positivo), en los datos llega como venta extra solo una parte: unas 55 unidades de cada 100 en regulares y unas 40 en One Shots. El forecast las suma enteras, y por eso en los meses con DA va por encima de lo vendido.</p>
      </div>
      <div class="rule-res">
        <div class="res"><span>2026 (fotos limpias)</span><b>WAPE90 {pct(B['w'], 1)} → {pct(D7['w26'], 1)}</b><span>SPP3 {pct(B['s'], 1, True)} → {pct(D7['s26'], 1, True)}</span></div>
        <div class="res"><span>2025 (fotos armonizadas)</span><b>WAPE90 {pct(DA[1.0]['w25'], 1)} → {pct(D7['w25'], 1)}</b><span>SPP3 {pct(DA[1.0]['s25'], 1, True)} → {pct(D7['s25'], 1, True)}</span></div>
      </div>
      <div class="table-wrap"><table class="t-da">
        <thead><tr><th>Cuánto DA se cuenta</th><th>WAPE90 2026</th><th>SPP3 2026</th><th>WAPE90 2025</th><th>SPP3 2025</th></tr></thead>
        <tbody>{tabla_da()}</tbody>
      </table></div>
      <p class="tile-note">Por debajo del 60 % el WAPE apenas mejora más y el SPP de 2026 se pasa de +5 %. El 70 % deja el SPP de 2026 en meta y es la opción más segura.</p>
      <div class="example"><b>Ejemplo real · {E(ej['desc'])}</b>
        <span>Foto {ej['foto']}, mes {ej['mes']}: forecast {num(ej['cons'])} uds, todo DA. Se vendieron {num(ej['A'])}. Con la regla, el forecast habría sido {num(ej['nuevo'])}: el error baja de {num(abs(ej['cons'] - ej['A']))} a {num(abs(ej['nuevo'] - ej['A']))} unidades.</span></div>
    </article>

    <article class="rule">
      <div class="rule-head">
        <span class="rule-tag">Regla 2</span>
        <h3>En los meses 7 a 12 tras el lanzamiento, rebaja el forecast un 30 %</h3>
        <p class="rule-why">Al lanzar un código, la mitad del volumen del primer año entra en los 3 primeros meses para llenar las tiendas. Un año después, los retailers todavía tienen en tienda 2,4 veces lo que han vendido (lo normal es 1,3), así que la recompra de los meses 7 a 12 es floja. El forecast de esos meses se pasa: SPP −31 % en 2026 y −160 % en 2025.</p>
      </div>
      <div class="rule-res">
        <div class="res"><span>2026, sola</span><b>WAPE90 {pct(B['w'], 1)} → {pct(LZ['w26'], 1)}</b><span>SPP3 {pct(B['s'], 1, True)} → {pct(LZ['s26'], 1, True)}</span></div>
        <div class="res"><span>2026, junto con la regla 1</span><b>WAPE90 {pct(B['w'], 1)} → {pct(JU['w26'], 1)}</b><span>SPP3 {pct(B['s'], 1, True)} → {pct(JU['s26'], 1, True)}</span></div>
      </div>
      <p class="tile-note">Con los datos de 2025 la rebaja óptima era mayor (×0,3). Se propone ×0,7 por prudencia: mejora en los dos periodos sin arriesgar el SPP.</p>
    </article>
  </section>

  <section class="block" id="no">
    <header>
      <h2>3. Qué no mejora el KPI</h2>
      <p>Probado con el mismo método. Aquí acertar no basta: una regla puede acertar casi siempre y aun así empeorar el WAPE si se equivoca en los códigos grandes.</p>
    </header>
    <div class="nots">
      <div class="not"><span class="not-tag">Empeora</span><b>Mover el volumen al mes en que el año pasado llegó el pedido</b><p>El timing de los pedidos grandes es el {pct(dec['pico_err'])} del error, pero el calendario del año pasado no lo anticipa: repartir los 3 meses así sube el WAPE 0,8 puntos. Ninguna señal encontrada acierta el mes del pedido más de la mitad de las veces.</p></div>
      <div class="not"><span class="not-tag">Empeora</span><b>Poner a cero el mes siguiente a un mes vacío</b><p>Acierta 9 de cada 10 veces, pero aplicado a todos los códigos sube el WAPE de 2026 en 3,3 puntos: falla justo en códigos grandes que piden un mes sí y otro no.</p></div>
      <div class="not"><span class="not-tag">No mueve</span><b>Las alertas por código (sección 4)</b><p>Aciertan mucho más que el azar, pero tocan menos del 0,5 % del volumen. Su efecto en el WAPE de la casa es de ±0,1 puntos. Sirven para otras decisiones.</p></div>
    </div>
  </section>

  <section class="block" id="alertas">
    <header>
      <h2>4. Alertas por código</h2>
      <p>Patrones que, en cada foto, avisan de lo que va a pasar con un código concreto. No mejoran el KPI de la casa, pero ayudan a no fabricar stock que no se venderá y a no quedarse sin producto. Cada alerta junta varias señales: cuantas más coinciden, más probable es que pase.</p>
    </header>
    <div class="card"><div class="table-wrap"><table class="t-al">
      <thead><tr><th>Alerta</th><th>Acierta con 2+ señales</th><th>Códigos en 2026</th><th>Efecto en el WAPE de la casa</th><th>Qué hacer</th></tr></thead>
      <tbody>{alertas_tabla()}</tbody>
    </table></div></div>
    <div class="alertas">{alertas_detalle()}</div>
    <div class="gloss">
      <div><b>Ritmo</b><span>Venta media mensual del código en los últimos 12 meses.</span></div>
      <div><b>Lo esperable</b><span>El ritmo del código ajustado por la estacionalidad de su brand el año anterior.</span></div>
      <div><b>Errático</b><span>Meses muy distintos entre sí (CV, desviación ÷ media, de 0,9 o más). Pide a saltos.</span></div>
      <div><b>Pedido grande</b><span>Un mes con al menos 2 veces la mediana de sus últimos 12 meses.</span></div>
      <div><b>Va bien hoy</b><span>Sus últimos 3 meses van al 60 % de su ritmo o más y no ha tenido meses a cero.</span></div>
      <div><b>Sin señal</b><span>Lo que pasa de media sin mirar ninguna señal. La alerta vale lo que supera a ese número.</span></div>
    </div>
  </section>

  <details>
    <summary>Método y límites</summary>
    <ul>
      <li><b>Datos:</b> 14 fotos de Gucci (2025.M09–2026.M10), regulares, actuals cerrados hasta 2026.M09. En la foto 2026.M02 cambió el perímetro del export (la historia subió un 29 %). Las fotos anteriores se armonizaron con un factor por código y se tratan aparte. Por eso el KPI de referencia es el de 2026.</li>
      <li><b>KPI:</b> WAPE90 = Σ|forecast − real| / Σ real en los meses 1 a 3 tras cada foto, mes a mes y código a código. SPP3 = Σ(real − forecast) / Σ real. Forecast = Consensus - Final de cada foto.</li>
      <li><b>Reglas de la sección 2:</b> el parámetro se eligió para minimizar WAPE + |SPP| en un periodo y se midió en el otro (2025 → 2026 y 2026 → 2025).</li>
      <li><b>Alertas de la sección 4:</b> se buscaron entre 75 indicadores y unas 200.000 combinaciones. Solo quedan las que se cumplen en el periodo antiguo, el reciente y cada mitad de los códigos, y en al menos 4 meses distintos.</li>
      <li><b>Límites:</b> solo Gucci; con 10 fotos medidas, las cifras pueden moverse unos puntos; hay que volver a medir cada trimestre y en cada casa.</li>
    </ul>
  </details>
  <footer>Análisis del 16/10/2026 sobre <code>data/Gucci/Consensus/</code>. Detalle en <code>analisis/SENALES-2026-10.md</code>.</footer>
</div>
<div class="tip" id="tip" hidden></div>
<script>
(() => {{
  const tip = document.getElementById('tip');
  const show = (el) => {{
    tip.textContent = el.getAttribute('data-tip'); tip.hidden = false;
    const r = el.getBoundingClientRect(), w = tip.offsetWidth, h = tip.offsetHeight;
    let x = r.left + r.width / 2 - w / 2, y = r.top - h - 8;
    x = Math.max(8, Math.min(x, window.innerWidth - w - 8)); if (y < 8) y = r.bottom + 8;
    tip.style.left = x + 'px'; tip.style.top = y + 'px';
  }};
  const hide = () => {{ tip.hidden = true; }};
  document.querySelectorAll('[data-tip]').forEach((el) => {{
    el.addEventListener('pointerenter', () => show(el)); el.addEventListener('pointerleave', hide);
    el.addEventListener('focus', () => show(el)); el.addEventListener('blur', hide);
  }});
  window.addEventListener('scroll', hide, {{ passive: true }});
}})();
</script>
'''
open(S + '/senales-gucci.html', 'w', encoding='utf-8').write(page)
print('ok', len(page))
