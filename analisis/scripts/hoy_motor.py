"""Rehace los 'códigos hoy' de la página de análisis con el motor de O10 (corrige y3_ly en las últimas fotos)."""
import json, math
S = '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad'
D = json.load(open(S + '/cons_cartas.json')); E = json.load(open(S + '/esc_out.json'))
at = json.load(open(S + '/datos_o10.json'))['casas']['Gucci']['atributos']
ESC = ['bajo', 'muy_bajo', 'alto', 'muy_alto', 'orden']
rid = [r['id'] for r in E['reglas']]
vnames = [v[0] for v in E['ver']]
i12 = vnames.index('Units sold in 12 months') if 'Units sold in 12 months' in vnames else None
# los puntos del motor son los mismos que los de la página de análisis
for e in ESC:
    assert {rid[i]: p for i, p in E['cats'][e]['pts']} == {s['id']: s['puntos'] for s in D['categorias']['Y_' + e]['senales']}, e
hoy = []
for ean, c in E['codigos'].items():
    a = at.get(ean, {})
    d = dict(ean=ean, desc=a.get('desc', ean), brand=a.get('brand', ''), seg=a.get('segmento', ''),
             vol12=float(c['v'][i12]) if i12 is not None and c['v'][i12] is not None else 0.0, c3=float(sum(x or 0 for x in c['c'])))
    for k, e in enumerate(ESC):
        pts = {rid[i]: p for i, p in E['cats'][e]['pts']}
        act = [(rid[i], pts[rid[i]]) for i in c['a'] if rid[i] in pts]
        d['Y_' + e] = c['p'][k]; d['Y_' + e + '_pts'] = int(sum(p for _, p in act)); d['Y_' + e + '_act'] = act
    hoy.append(d)
D['hoy'] = sorted(hoy, key=lambda d: -d['c3'])
json.dump(D, open(S + '/cons_cartas.json', 'w'), ensure_ascii=False)
x = next(h for h in D['hoy'] if 'EDPI PRFM 100 ML INTENSE' in h['desc'])
print(len(hoy), 'códigos · Flora Intense: bajo', round(x['Y_bajo'], 3), x['Y_bajo_pts'], 'pts')
