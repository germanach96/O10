from base import *
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 300); pd.set_option('display.max_colwidth', 45)
L = pd.DataFrame({'ean': EANS, 'primer': PRIMER, 'os': OS, 'brand': BRAND, 'pl': PL, 'seg': SEG,
                  'desc': ATR['Planning Item Description'].to_numpy(), 'resp': ATR['Final Responsibility'].to_numpy(),
                  'vol12': [ACT[i, max(k(p),0):max(k(p),0)+12].sum() if p>0 else 0 for i,p in enumerate(PRIMER)],
                  'tam': ATR['tamano'].to_numpy()})
L = L[L.primer >= 2022*12+8]
L['mes'] = L.primer.map(m)
print('Lanzamientos (primer venta >= 2022.M09):', len(L), ' regular', (~L.os).sum(), ' one shot', L.os.sum())
print(L.groupby(['os', L.primer//12]).size().unstack(fill_value=0))
print('\nRegulares nuevos (volumen primeros 12 meses):')
print(L[~L.os].sort_values('primer')[['mes','brand','pl','desc','tam','resp','vol12']].to_string(index=False))
# PL nuevas: primer venta de la PL
plfirst = L.groupby('pl').primer.min()
allpl = pd.Series(PRIMER, index=PL).groupby(level=0).apply(lambda s: s[s>0].min())
print('\nProduct Lines nuevas (primera venta de la línea >= 2022.M09):')
print(allpl[allpl >= 2022*12+8].map(m).to_string())
