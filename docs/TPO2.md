# Portada

# TPO2 - Automatizacion de pruebas y pipeline CI/CD

**Alumno:** Laureano Tomás Flores  
**Legajo:** 1142069  
**Materia:** Testing de Aplicaciones (14883)  
**Docente:** ABEL ISRAEL LAIME HUANCA  
**Fecha:** 28/04/2026  

<!-- pagebreak -->

## Indice

1. Introduccion
2. Objetivo del trabajo
3. Desarrollo de la aplicacion
4. Parte 1 - Diseno del escenario de prueba
5. Parte 2 - Automatizacion de pruebas
6. Parte 3 - Pipeline CI/CD
7. Parte 4 - Evidencia y analisis
8. Parte 5 - Reflexion
9. Conclusiones personales
10. Propuestas de futuras mejoras
11. Bibliografia
12. Estado de cumplimiento

<!-- pagebreak -->

## 1. Introduccion

Este trabajo practico tiene como objetivo aplicar conceptos de testing automatizado y DevOps mediante una solucion simple desarrollada en Python. La propuesta consiste en crear una funcionalidad sencilla, definir escenarios de prueba, automatizarlos con pytest e integrarlos a un pipeline de integracion continua usando GitHub Actions.

La funcionalidad elegida fue un sistema de descuentos. La aplicacion calcula el precio final de una compra de acuerdo con el tipo de cliente y el monto ingresado. Esta eleccion permite cubrir casos exitosos, errores de validacion y casos borde de forma clara.

### Repositorio y archivos entregados

El repositorio publico del trabajo es:

https://github.com/LaureanoFloresU/tpo2-testing-pipeline

Ademas, se incluye el proyecto local empaquetado en el archivo `Flores_1142069_26042026_TPO2_repositorio.zip`, que contiene el codigo fuente, los tests, el workflow de GitHub Actions y el reporte HTML generado localmente.

## 2. Objetivo del trabajo

El objetivo es implementar un flujo basico de automatizacion de pruebas integrado a un pipeline CI/CD. Para cumplirlo se desarrollo una aplicacion en Python, se escribieron pruebas automatizadas con pytest y se configuro un workflow de GitHub Actions que instala dependencias, ejecuta los tests y genera un reporte HTML como artefacto.

## 3. Desarrollo de la aplicacion

La aplicacion se encuentra dentro de la carpeta `src/descuentos`. La funcion principal es `calcular_precio_final(monto, tipo_cliente)`.

Reglas implementadas:

- Cliente `regular`: no recibe descuento.
- Cliente `premium`: recibe 10% de descuento.
- Cliente `vip`: recibe 20% de descuento.
- Compras desde $100000 reciben 5% adicional.
- No se aceptan montos negativos.
- No se aceptan tipos de cliente desconocidos.

Estructura del proyecto:

```text
.
|-- .github/workflows/ci.yml
|-- docs/TPO2.md
|-- reports/pytest-report.html
|-- scripts/generate_pdf.py
|-- src/descuentos/
|   |-- __init__.py
|   |-- calculator.py
|   `-- main.py
|-- tests/test_calculator.py
|-- pyproject.toml
|-- requirements.txt
`-- README.md
```

## 4. Parte 1 - Diseno del escenario de prueba

### Escenario de prueba

El escenario elegido representa una compra en la que el sistema debe calcular el precio final luego de aplicar descuentos. El contexto simula una aplicacion comercial simple donde diferentes tipos de clientes obtienen distintos beneficios.

### Casos de prueba definidos

| Caso | Tipo | Datos de entrada | Resultado esperado |
|---|---|---|---|
| Cliente premium | Caso exitoso | Monto: 10000, cliente: premium | Precio final: 9000 |
| Monto negativo | Caso de error | Monto: -1, cliente: regular | Se lanza ValueError |
| Compra en limite | Caso borde | Monto: 100000, cliente: vip | Precio final: 75000 |
| Cliente inexistente | Caso de error adicional | Monto: 5000, cliente: estudiante | Se lanza ValueError |

El caso borde es importante porque verifica que el descuento adicional se aplique exactamente en el limite definido por la regla de negocio: compras desde $100000.

## 5. Parte 2 - Automatizacion de pruebas

Los casos fueron automatizados con Python y pytest. El archivo de pruebas es `tests/test_calculator.py`.

Tests automatizados:

- `test_cliente_premium_recibe_descuento_exitoso`
- `test_monto_negativo_genera_error`
- `test_compra_en_limite_recibe_descuento_adicional`
- `test_tipo_cliente_desconocido_genera_error`

Comando para ejecutar las pruebas:

```bash
pytest --html=reports/pytest-report.html --self-contained-html
```

Resultado local obtenido:

```text
4 passed
```

Este resultado confirma que la logica del sistema cumple con los escenarios definidos.

## 6. Parte 3 - Pipeline CI/CD

El pipeline fue configurado con GitHub Actions en el archivo `.github/workflows/ci.yml`.

El workflow se ejecuta automaticamente ante:

- `push`
- `pull_request`

Pasos del pipeline:

1. Descarga el repositorio con `actions/checkout@v4`.
2. Configura Python 3.12 con `actions/setup-python@v5`.
3. Instala dependencias desde `requirements.txt`.
4. Ejecuta los tests automatizados con pytest.
5. Genera el reporte HTML con pytest-html.
6. Publica el reporte como artefacto llamado `pytest-html-report`.

Fragmento del pipeline:

```yaml
name: Python tests

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: pytest --html=reports/pytest-report.html --self-contained-html
```

El artefacto generado permite descargar un reporte visual de los tests ejecutados.

## 7. Parte 4 - Evidencia y analisis

### Evidencia de ejecucion local

La ejecucion local de pytest finalizo correctamente:

```text
tests/test_calculator.py::test_cliente_premium_recibe_descuento_exitoso PASSED
tests/test_calculator.py::test_monto_negativo_genera_error PASSED
tests/test_calculator.py::test_compra_en_limite_recibe_descuento_adicional PASSED
tests/test_calculator.py::test_tipo_cliente_desconocido_genera_error PASSED
4 passed
```

### Evidencia del pipeline

El pipeline fue configurado correctamente en `.github/workflows/ci.yml`. La evidencia disponible en esta entrega es:

- Archivo de workflow incluido en `.github/workflows/ci.yml`.
- Ejecucion local de pytest finalizada correctamente.
- Reporte HTML generado en `reports/pytest-report.html`.
- Proyecto empaquetado en `Flores_1142069_26042026_TPO2_repositorio.zip`.
- Repositorio publico: https://github.com/LaureanoFloresU/tpo2-testing-pipeline
- Pipeline ejecutado correctamente en GitHub Actions: https://github.com/LaureanoFloresU/tpo2-testing-pipeline/actions/runs/24967311464
- Job `test` finalizado correctamente: https://github.com/LaureanoFloresU/tpo2-testing-pipeline/actions/runs/24967311464/job/73104237761
- Artefacto generado: `pytest-html-report`.

Al realizar el `push`, el workflow `Python tests` debe verse en la pestaña Actions del repositorio. La ejecucion correcta debe mostrar:

- Estado general del workflow: completed / success.
- Job `test`: completed / success.
- Paso `Install dependencies`: OK.
- Paso `Run automated tests`: OK.
- Artefacto disponible: `pytest-html-report`.
- Commit ejecutado: `7f2af7318fc92a41bb6031231e8c22b561819775`.

### Resultado de los tests

| Test | Resultado |
|---|---|
| Cliente premium recibe descuento exitoso | OK |
| Monto negativo genera error | OK |
| Compra en limite recibe descuento adicional | OK |
| Tipo de cliente desconocido genera error | OK |

### Explicacion de resultados

Los tests pasaron porque la funcion implementada respeta las reglas de negocio. El caso exitoso confirma el descuento premium, el caso de error valida que un monto negativo no sea aceptado, el caso borde comprueba el limite exacto de $100000 y el caso de cliente inexistente verifica que el sistema rechace datos invalidos.

### Ventaja de automatizar pruebas dentro del pipeline

Automatizar pruebas dentro del pipeline permite detectar errores automaticamente cada vez que se sube codigo al repositorio. Esto evita depender solamente de revisiones manuales y ayuda a impedir que cambios defectuosos lleguen a la rama principal.

### Impacto en la calidad del software

El impacto es positivo porque aumenta la confianza sobre cada cambio. Tambien mejora la trazabilidad, ya que GitHub Actions conserva logs de cada ejecucion. Esto permite saber que version del codigo fue probada, que tests se ejecutaron y cual fue el resultado.

## 8. Parte 5 - Reflexion

### Beneficios de automatizar pruebas frente a hacerlas manualmente

Automatizar pruebas permite ahorrar tiempo, repetir validaciones sin esfuerzo adicional y reducir errores humanos. Las pruebas manuales pueden ser utiles para explorar el sistema, pero las pruebas automatizadas son mejores para comprobar reglas conocidas de manera constante.

### Dificultades encontradas al implementar el pipeline

Una dificultad fue asegurar que todas las dependencias estuvieran declaradas correctamente en `requirements.txt`. Otra dificultad fue ordenar la estructura del proyecto para que pytest pudiera importar el codigo desde `src`. Tambien fue necesario generar un artefacto HTML para cumplir con la evidencia solicitada.

### Donde aplicaria este enfoque en un entorno real

Aplicaria este enfoque en proyectos web, APIs, sistemas administrativos, sistemas de ventas, facturacion o cualquier aplicacion que tenga reglas de negocio importantes. En un entorno real, automatizar pruebas dentro del pipeline ayuda a trabajar en equipo y reduce el riesgo de romper funcionalidades existentes.

## 9. Conclusiones personales

El trabajo muestra como se conectan el desarrollo de software, el testing y las practicas DevOps. La automatizacion no reemplaza completamente el criterio humano, pero permite construir una base de validacion objetiva y repetible.

Integrar pytest con GitHub Actions permite que cada cambio sea verificado automaticamente. Esto mejora la calidad del proceso de desarrollo y facilita detectar errores antes de que lleguen a produccion.

## 10. Propuestas de futuras mejoras

Como mejoras futuras se podrian implementar:

- Agregar mas reglas de descuento.
- Usar tests parametrizados para cubrir mas combinaciones.
- Incorporar cobertura de codigo con `pytest-cov`.
- Agregar analisis de estilo con `ruff`.
- Publicar el reporte HTML como pagina estatica.
- Agregar ramas protegidas para exigir que el pipeline pase antes de integrar cambios.
- Incorporar pruebas de integracion si la aplicacion crece.

## 11. Bibliografia

- Python Software Foundation. Documentacion oficial de Python: https://docs.python.org/3/
- pytest. Documentacion oficial: https://docs.pytest.org/
- GitHub. Documentacion oficial de GitHub Actions: https://docs.github.com/actions
- pytest-html. Documentacion oficial: https://pytest-html.readthedocs.io/

## 12. Estado de cumplimiento

| Requisito | Estado | Observacion |
|---|---|---|
| Funcionalidad simple en Python | Cumplido | Sistema de descuentos implementado en `src/descuentos/calculator.py`. |
| Estructura de proyecto real | Cumplido | Separacion entre `src`, `tests`, `docs`, `reports` y `.github/workflows`. |
| Escenario de prueba | Cumplido | Escenario comercial de calculo de precio final con descuentos. |
| Al menos 3 casos de prueba | Cumplido | Se definieron 4 casos. |
| Python + pytest | Cumplido | Tests en `tests/test_calculator.py`. |
| Caso exitoso | Cumplido | Cliente premium con descuento correcto. |
| Caso de error | Cumplido | Monto negativo y cliente desconocido generan `ValueError`. |
| Caso borde | Cumplido | Compra exacta de $100000 aplica descuento adicional. |
| GitHub Actions configurado | Cumplido | Workflow `Python tests` en `.github/workflows/ci.yml`. |
| Ejecutarse al hacer push | Cumplido en configuracion | El workflow tiene trigger `push`. |
| Instalar dependencias | Cumplido | Paso `Install dependencies`. |
| Ejecutar tests | Cumplido | Paso `Run automated tests`. |
| Mostrar logs | Cumplido en configuracion | GitHub Actions mostrara logs por cada paso. |
| Artefacto de reporte | Cumplido en configuracion y localmente | `pytest-html-report` en GitHub Actions y `reports/pytest-report.html` local. |
| Capturas / evidencia del pipeline | Cumplido | Pipeline ejecutado correctamente: https://github.com/LaureanoFloresU/tpo2-testing-pipeline/actions/runs/24967311464 |
| Repositorio publico accesible | Cumplido | https://github.com/LaureanoFloresU/tpo2-testing-pipeline |
| PDF con portada, indice y paginas | Cumplido | Archivo `Flores_1142069_26042026_TPO2.pdf`. |
| Conclusiones y futuras mejoras | Cumplido | Incluidas en las secciones 9 y 10. |
| Bibliografia | Cumplido | Incluida en la seccion 11. |
