# TPO2 - Automatizacion de pruebas y pipeline CI/CD

Proyecto para la materia Testing de Aplicaciones (14883).

La aplicacion implementa un sistema simple de descuentos para calcular el precio final de una compra segun el tipo de cliente y el monto.

## Estructura

```text
.
|-- .github/workflows/ci.yml
|-- docs/
|-- src/descuentos/
|-- tests/
|-- requirements.txt
`-- README.md
```

## Ejecutar localmente

```bash
python -m pip install -r requirements.txt
pytest --html=reports/pytest-report.html --self-contained-html
```

## Pipeline

El workflow de GitHub Actions se ejecuta automaticamente en cada `push` y `pull_request`. Instala dependencias, ejecuta los tests y publica el reporte HTML como artefacto.

