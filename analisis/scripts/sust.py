from base import *
TAM = ATR['tamano'].to_numpy(); DESC = ATR['Planning Item Description'].to_numpy()
# último mes con venta relevante
def ultimo(i):
    a = ACT[i]; nz = np.where(a > 0)[0]; return MESES[nz[-1]] if len(nz) else -1
ULT = np.array([ultimo(i) for i in range(len(EANS))])
rows = []
for j in np.where((PRIMER >= 2022*12+8) & ~OS)[0]:
    Lm = PRIMER[j]
    cand = np.where((PL == PL[j]) & (TAM == TAM[j]) & ~OS & (PRIMER > 0) & (PRIMER < Lm - 3) & (np.arange(len(EANS)) != j))[0]
    for i in cand:
        pre = ACT[i, max(k(Lm-6),0):k(Lm)].sum(); post = ACT[i, k(Lm)+3:min(k(Lm)+9, NM)].sum()
        newv = ACT[j, k(Lm):min(k(Lm)+6, NM)].sum()
        if pre <= 0: continue
        rows.append(dict(nuevo=DESC[j], viejo=DESC[i], L=m(Lm), tam=TAM[j], pre6=pre, post_m3_9=post, caida=post/pre-1 if pre>0 else np.nan, nuevo6=newv, ratio_nuevo_viejo=newv/pre))
D = pd.DataFrame(rows)
pd.set_option('display.width', 250); pd.set_option('display.max_colwidth', 40)
D['sustitucion'] = D.caida < -0.8
print('pares nuevo/viejo con misma PL y tamaño:', len(D), ' sustituciones (viejo cae >80%):', D.sustitucion.sum())
print(D.sort_values('L').round(2).to_string(index=False))
s = D[D.sustitucion]
print(f'\nEn sustituciones: volumen 6M del nuevo / volumen 6M previo del viejo: mediana {s.ratio_nuevo_viejo.median():.2f}, media ponderada {s.nuevo6.sum()/s.pre6.sum():.2f}')
D.to_pickle(S+'/sust.pkl')
import re
STOP = {'IV','RG','REG','NS','VP','GUCCI','EDP','EDT','ML','G','GAL','NANSA','S/G','PS','23IV','24IV','22IV','20IV','19IV','18IV','21IV','25IV','FY23','FY24','FY25','SCREW','RGIV','PSPRAY','PENSPRAY'}
def toks(d):
    d = re.sub(r'\d+(\.\d+)?\s*(ML|G)\b', ' ', d.upper()); d = re.sub(r'\b\d+\b', ' ', d)
    return {t for t in re.split(r'[^A-Z0-9/]+', d) if t and t not in STOP and not re.fullmatch(r'\d+IV|\d+', t)}
D['sim'] = [len(toks(a) & toks(b)) / max(len(toks(a) | toks(b)), 1) for a, b in zip(D.nuevo, D.viejo)]
P2 = D[(D.sim >= 0.5)]
print('\n=== Pares con descripción parecida (Jaccard >= 0.5):', len(P2), ' sustituciones:', P2.sustitucion.sum())
print(P2.sort_values('L')[['L','nuevo','viejo','pre6','post_m3_9','caida','nuevo6','ratio_nuevo_viejo','sim']].round(2).to_string(index=False))
s = P2[P2.sustitucion]
print(f'\nSustituciones: nuevo 6M / viejo 6M previos: mediana {s.ratio_nuevo_viejo.median():.2f}  agregada {s.nuevo6.sum()/s.pre6.sum():.2f}  n={len(s)}')
P2.to_pickle(S+'/sust2.pkl')
