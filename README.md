# O10 · Brújulas de Demand — fase 1

Especificación completa en `CLAUDE.md` (empieza por ahí).

```bash
pip install -r requirements.txt
python -m motor.pipeline            # lee data/<Casa>/Consensus/*.csv y genera diseno/ejemplos/BRUJULAS_ejemplo.html
python -m motor.pipeline --sin-cubo # igual, sin escribir el cubo Parquet
python -m pytest tests
# En las sesiones en la nube de Claude Code, .claude/hooks/session-start.sh instala requirements.txt al arrancar
```

## Mapa del repo

```
O10/
├── CLAUDE.md                 especificación (KPIs, datos, recetas, detector, interfaz)
├── README.md                 este mapa
├── requirements.txt
├── motor/                    cálculo en Python (sin nada de interfaz)
│   ├── config.json           rejillas, tope del trend, pesos, tolerancia inicial, filtro de tipos
│   ├── lector.py             lectura y validación de una foto (EAN, mes, scope, edad, tamaño)
│   ├── recetas.py            forecast de las 75.816 recetas por código y foto (MotorFoto, Rejilla)
│   ├── escenarios.py         escenarios frente al Consensus: señales, pesos y probabilidad por código y grupo
│   └── pipeline.py           actuals posteriores, tramos, cubo, resúmenes, score multi-foto, detector
├── interfaz/                 código de la página
│   ├── plantilla.html        HTML + CSS + JS de O10; el pipeline incrusta los datos
│   ├── html.py               genera el HTML autocontenido a partir de la plantilla
│   └── vendor/               d3-hierarchy incrustado (licencia ISC)
├── O10.0.5.html              versión oficial de la página (en la raíz; se abre sin servidor)
├── VERSION                   número de versión que muestra la página (O10.0.1, O10.0.2…)
├── diseno/                   decisiones de diseño y ejemplos
│   ├── DESIGN.md             sistema de diseño vigente (iOS / iPadOS 26, cristal líquido)
│   ├── PRODUCT.md            para quién es y qué tiene que transmitir
│   ├── SKILLS-DISENO.md      skills de diseño obligatorias (lo importa CLAUDE.md)
│   ├── referencia/           guías antiguas, ya no se aplican
│   └── ejemplos/             BRUJULAS_ejemplo.html, la página generada (se abre sin servidor)
├── data/                     datos de entrada, una carpeta por casa
│   ├── filters.csv           listas de EANs para los filtros de selección (una por columna)
│   ├── Gucci/
│   │   ├── Consensus/        fotos mensuales: Gucci_2025_11.csv, Gucci_2026_09.csv
│   │   └── Promos/           (vacía) promos, para la 2ª etapa
│   ├── Gucci MU/             Consensus/ y Promos/ (vacías)
│   ├── Kylie MU/             ídem
│   ├── Kylie Frag/           ídem
│   ├── Burberry/             ídem
│   ├── Burberry MU/          ídem
│   └── Marc Jacobs MU/       ídem
├── analisis/                 informes de análisis de datos (señales de Gucci) y sus scripts
├── scripts/                  búsqueda de patrones señal → resultado (patrones_01…07, ver resultados/informe_patrones.md)
│                             y relevancia de los trends (tendencias_01 casos, 02 métricas, 04 matriz)
├── resultados/               informe de patrones, tarjetas (CSV), gráficos; cache/ no se versiona
├── signals.html              tarjetas de señales en el estilo de O10 (la genera scripts/patrones_08_html.py; se abre sin servidor)
├── trend_matrix.html         Trend analysis: trend × base (media 12M, LY, estacionalidad 50/100%) × horizonte (tendencias_04_matriz.py)
├── tests/                    tests del lector, el motor, los KPIs y los escenarios
└── salida/                   (no versionada) cubo Parquet, resúmenes JSON, logs
```

Una foto nueva se añade dejando su CSV en `data/<Casa>/Consensus/` con el nombre `<Casa>_AAAA_MM.csv` y volviendo a ejecutar el pipeline. La casa sale del nombre del archivo. El pipeline solo lee las carpetas `Consensus/`; `Promos/` queda preparada para cuando se diferencien los tipos de promo.
