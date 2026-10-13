# Brújulas de Demand — ejemplo fase 1

Especificación completa en `CLAUDE.md`.

```bash
pip install -r requirements.txt
python -m brujulas.pipeline            # lee *_AAAA_MM.csv de la raíz, genera BRUJULAS_ejemplo.html
python -m brujulas.pipeline --sin-cubo # igual, sin escribir el cubo Parquet
python -m pytest tests
```

- `brujulas/config.json`: rejillas, tope del trend, pesos por tramo, tolerancias y decisiones abiertas.
- `brujulas/lector.py`: lectura y validación de fotos (EAN, mes, scope, edad, tamaño).
- `brujulas/motor.py`: forecast de las 12.393 recetas por código y foto.
- `brujulas/pipeline.py`: actuals posteriores, tramos, cubo Parquet (`salida/cubo`), resúmenes, score multi-foto y detector.
- `BRUJULAS_ejemplo.html`: página autocontenida con los datos precalculados (se abre sin servidor).
