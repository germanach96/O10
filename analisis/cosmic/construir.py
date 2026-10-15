# Construye Cosmic a partir de la página de Skin Tint: mismos cálculos, varias product lines, sin WOS
import pandas as pd, json, sys, re
CSV, SRC, OUT, NOTES = sys.argv[1:5]
df=pd.read_csv(CSV,sep=';',skiprows=1,dtype={'EAN':str},encoding='utf-8-sig').dropna(subset=['EAN'])
assert not df.EAN.str.contains('E').any()
cols={'Actuals':'A','Supply Cuts':'C','EPOS':'E','Total Demand Assumption':'T','Consensus - Final':'K'}
for c in cols: df[c]=pd.to_numeric(df[c].astype(str).str.replace(',',''),errors='coerce')
# meses continuos desde el primer mes con algún dato (se descartan filas vacías, como una de 2021.M01)
has=df[list(cols)].notna().any(axis=1); df=df[has|(df.Month>='2024.M01')]
def mm(x): y,m=x.split('.M'); return int(y)*12+int(m)-1
lo,hi=min(map(mm,df[has].Month)),max(map(mm,df.Month))
months=[f"{v//12}.M{v%12+1:02d}" for v in range(lo,hi+1)]; df=df[df.Month.map(mm)>=lo]; mi={m:i for i,m in enumerate(months)}
notes=json.load(open(NOTES))
lines=[]
for pl,g in df.groupby('Product Line'):
    eans=[]
    for e,ge in g.groupby('EAN'):
        d={'ean':e,'desc':ge['Planning Item Description'].iloc[0].strip()}
        for c,k in cols.items():
            arr=[None]*len(months)
            for m,v in zip(ge.Month,ge[c]):
                if pd.notna(v): arr[mi[m]]=float(v) if v%1 else int(v)
            d[k]=arr
        eans.append(d)
    isff=int(g['Ignore System Forecast Flag'].dropna().iloc[0])
    short=re.sub(r'\s*\(\d+\)$','',pl)
    lines.append({'name':pl,'short':short,'house':g.House.iloc[0],'isff':isff,'eans':eans,**notes.get(short,{})})
D={'months':months,'foto':'2026.M10','lines':lines}
s=open(SRC).read()
def rep(a,b,n=1):
    global s
    assert s.count(a)==n,(a[:80],s.count(a)); s=s.replace(a,b)
# datos y selección de product line
i=s.index('const WOS='); j=s.index('\n',i); s=s[:i]+s[j+1:]
i=s.index('const D='); j=s.index('\n',i); s=s[:i]+'const D='+json.dumps(D,separators=(',',':'))+';'+s[j:]
rep("const E=D.eans;","const E=PL.eans, WOS={};")
rep('<title>Skin Tint</title>','<title>Cosmic</title>')
rep('/* Análisis puntual Kylie Skin Tint, foto 2026.M10.','/* Análisis puntual Cosmic (dos product lines), foto 2026.M10.')
rep('<div class="crumbs">Kylie Makeup › Kylie Skin Tint Foundation (00006730) · 24 EANs · ISFF 1 · Snapshot 2026.M10</div>\n      <h1>Skin Tint: Consensus vs proposed recipe</h1>',
    '<div class="crumbs" id="crumbs"></div>\n      <div class="plpick"><select id="pl" aria-label="Product line"></select></div>\n      <h1 id="h1"></h1>')
rep('.scope{display:flex;','.plpick{margin:2px 0 8px}\n.plpick select{appearance:none;-webkit-appearance:none;padding:9px 38px 9px 16px;border-radius:999px;border:1px solid var(--edge);background:var(--glass-strong) url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'10\' height=\'6\'%3E%3Cpath d=\'M1 1l4 4 4-4\' fill=\'none\' stroke=\'%238e8e93\' stroke-width=\'1.6\'/%3E%3C/svg%3E") no-repeat right 15px center;color:var(--label);font:600 15px var(--font);box-shadow:var(--shadow);cursor:pointer;max-width:100%}\n.scope{display:flex;')
rep("const NAME=e=>e.desc.replace(/^KJ MU SKN TINT LIQFND ?30 ?ML /,'').replace(/ IV$/,'');","const NAME=e=>e.desc.replace(/^KJ COSMIC (INT )?/,'').replace(/ IV$/,'');")
s=s.replace(".replace(/^KJ MU SKN TINT LIQFND ?30 ?ML /,'').replace(/ IV$/,'')",".replace(/^KJ COSMIC (INT )?/,'').replace(/ IV$/,'')")
rep("const nm=SEL<0?'Skin Tint family':NAME(E[SEL]);","const nm=SEL<0?PL.short:NAME(E[SEL]);")
rep("sel.innerHTML=`<option value=\"-1\">Skin Tint family · 24 EANs</option>`","sel.innerHTML=`<option value=\"-1\">${PL.short} · ${E.length} EANs</option>`")
rep("xs.innerHTML=`<option value=\"-1\">All codes · 24</option>`","xs.innerHTML=`<option value=\"-1\">All codes · ${E.length}</option>`")
rep("'skintint-scope'","'cosmic-scope-'+PLI",2)
rep("'skintint-theme'","'cosmic-theme'",2)
rep("const SKEY='skintint-config';","const SKEY='cosmic-config-'+PLI;")
rep("localStorage.getItem(SKEY)||localStorage.getItem('o'+'10-skintint-config')||'null'","localStorage.getItem(SKEY)||'null'")
rep("a.download=`SkinTint_adjustments_","a.download=`Cosmic_${PL.short.replace(/\\W+/g,'_')}_adjustments_")
rep("Grey = what is in the system today (DAs + Reasonability Adjustments, ISFF 1).","Grey = what is in the system today (${PL.isff===2?'DAs, ISFF 2: all manual':'DAs + Reasonability Adjustments, ISFF 1'}).")
# sin WOS: fuera columnas, acción, gráfico y explicación
a=s.index('  <div class="res" style="margin-top:12px">\n    <div class="card glass">\n      <h3>Weeks of sales'); b=s.index('  <h2>How it was built, and open questions</h2>')
s=s[:a]+'\n'+s[b:]
rep("${th('w','WOS')}${th('pri','Action')}","")
rep("<td>${wosTxt(r.w)}</td><td style=\"text-align:left\">${actTxt(r)}</td>","")
rep("colspan=\"10\"","colspan=\"8\"")
rep("  renderWos(rows);\n","")
i=s.index('function renderWos(rows){'); j=s.index('\nconst sumArr=',i); s=s[:i]+s[j+1:]
rep("let sortKey='pri'","let sortKey='u'")
rep("<th>Shade</th>","<th style=\"text-align:left\">Item</th>")
# textos de explicación y preguntas por product line
a=s.index('    <div class="q glass howto">\n      <h4>How cuts enter the history</h4>'); b=s.index('  <h2>Export: adjustments')
s=s[:a]+'''    <div class="q glass howto">
      <h4>How the history is built</h4>
      <p><code>History(t) = Actuals(t) + c · Cuts(t)</code>. At c = 0% the history is actuals only; at c = 100% it is actuals plus every unit cut. <b style="color:var(--label)">Count repeated cuts once</b> keeps only the cuts that are new each month, <code>c · (Cuts(t) − Cuts(t−1))</code>.</p>
      <p>Demand Assumptions are left out of the history and of the future. The base is the mean of that history over the last B months (only months since the first sale count for a new code); the trend is its YoY over N months.</p>
      <div id="pl-notes"></div>
    </div>
    <div class="q glass">
      <h4>Questions for you</h4>
      <ol id="pl-qs"></ol>
    </div>
  </div>

'''+s[b:]
rep("<p class=\"note\" style=\"margin-top:8px\">Launched Jun 2024: comparisons against Jun 2024 – early 2025 are against the ramp-up and the cut period, so large positive YoY there says more about last year than about this one. EPOS is used only as a trend, never as volume.</p>",
    "<p class=\"note\" style=\"margin-top:8px\">${PL.trendNote||''} EPOS is used only as a trend, never as volume.</p>")
# ventana de la base (B)
rep("const DEF={c:0,once:false,s:0,w:0,m:0,N:6};","""let PLI=0;try{const r=localStorage.getItem('cosmic-pl'),v=+r;if(r!==null&&v>=0&&v<D.lines.length)PLI=v}catch(e){}
const PL=D.lines[PLI];
const DEF={c:0,once:false,B:12,s:0,w:0,m:0,N:6,...(PL.def||{})};""")
rep("['c','Cuts added to actuals (c)',0,1,.01,v=>Math.round(v*100)+'%'],","['c','Cuts added to actuals (c)',0,1,.01,v=>Math.round(v*100)+'%'],['B','Base window (B)',3,12,1,v=>v+'M'],")
rep(".recipe{display:grid;grid-template-columns:repeat(5,minmax(0,1fr)) auto;",".recipe{display:grid;grid-template-columns:repeat(6,minmax(0,1fr)) auto;")
rep("const h=tr.hs[i], a=Math.max(fo-12,first[i]<0?fo:first[i]);","const h=tr.hs[i], a=Math.max(fo-p.B,first[i]<0?fo:first[i]);")
rep("const mean=fo>a?s/(fo-a):0,","const mean=fo>a?s/(fo-a):0; MEANS[i]=mean; const")
rep("function forecast(fo,p){","const MEANS=[];\nfunction forecast(fo,p){")
rep("base:sl(H,FOTO-12,FOTO)/12,","base:0,")
rep("const sd=scope(SEL);","CUR=forecast(FOTO,P);const sd=scope(SEL);",0) if False else None
rep("  return {i,A,C,K,T,H,Ep,","  const bse=i<0?(forecast(FOTO,P),MEANS.reduce((p,q)=>p+q,0)):(forecast(FOTO,P),MEANS[i]);\n  return {i,A,C,K,T,H,Ep,")
rep("base:0,","base:bse,")
rep("band:{a:FOTO-12,b:FOTO-1,v:sd.base}","band:{a:FOTO-P.B,b:FOTO-1,v:sd.base}")
rep(">12M base ${k(opt.band.v)}",">${P.B}M base ${k(opt.band.v)}")
rep("Blue = proposal: actuals + ${","Blue = proposal: ${P.B}-month base on actuals + ${")
rep("Base = 12-month mean of that history.","")
# arranque: cabecera y textos de la product line
rep("const sel=document.getElementById('scope');","""document.getElementById('crumbs').textContent=`${PL.house} › ${PL.name} · ${E.length} EANs · ISFF ${PL.isff} · Snapshot ${D.foto}`;
document.getElementById('h1').textContent=`Cosmic: Consensus vs proposed recipe`;
const plSel=document.getElementById('pl');
plSel.innerHTML=D.lines.map((l,i)=>`<option value="${i}">${l.name}</option>`).join('');plSel.value=String(PLI);
plSel.addEventListener('change',()=>{try{localStorage.setItem('cosmic-pl',plSel.value)}catch(e){}location.reload()});
document.getElementById('pl-notes').innerHTML=PL.notes||'';
document.getElementById('pl-qs').innerHTML=(PL.questions||[]).map(q=>`<li>${q}</li>`).join('');
const sel=document.getElementById('scope');""")
rep("'actuals a month, no cuts since July'","'actuals a month'")
rep("['c','Cuts added to actuals (c)',","['c','Cuts added (c)',")
rep("`Family trend over the last ${P.N} months","`Trend over the last ${P.N} months")
assert 'Skin Tint' not in s and 'skintint' not in s and 'O10' not in s, [m.start() for m in re.finditer('Skin Tint|skintint|O10',s)]
open(OUT,'w').write(s)
print('ok', [ (l['short'],len(l['eans'])) for l in lines])
