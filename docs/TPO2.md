# TPO2 - Automatizacion de pruebas y pipeline CI/CD

**Alumno:** Laureano Tomás Flores  
**Legajo:** 1142069  
**Materia:** Testing de Aplicaciones (14883)  
**Docente:** ABEL ISRAEL LAIME HUANCA  
**Fecha:** 26/04/2026  
**Repositorio:** COMPLETAR_CON_URL_PUBLICA_DE_GITHUB  

## Indice

1. Introduccion
2. Parte 1 - Diseno del escenario de prueba
3. Parte 2 - Automatizacion de pruebas
4. Parte 3 - Pipeline CI/CD
5. Parte 4 - Evidencia y analisis
6. Parte 5 - Reflexion
7. Conclusiones personales
8. Futuras mejoras
9. Bibliografia

## 1. Introduccion

El objetivo del trabajo fue implementar un flujo basico de automatizacion de pruebas integrado a un pipeline de integracion continua. Para resolverlo se desarrollo una aplicacion simple en Python que calcula descuentos segun el tipo de cliente y el monto de la compra.

La solucion utiliza `pytest` para automatizar los casos de prueba y GitHub Actions para ejecutar las pruebas automaticamente ante cada `push` o `pull_request`. Ademas, el pipeline genera un reporte HTML con `pytest-html` y lo publica como artefacto.

## 2. Parte 1 - Diseno del escenario de prueba

### Funcionalidad desarrollada

Se desarrollo un sistema de descuentos con la funcion `calcular_precio_final(monto, tipo_cliente)`.

Reglas de negocio:

- Cliente `regular`: no recibe descuento.
- Cliente `premium`: recibe 10% de descuento.
- Cliente `vip`: recibe 20% de descuento.
- Compras desde $100000 reciben 5% adicional.
- Un monto negativo debe generar error.
- Un tipo de cliente desconocido debe generar error.

### Estructura del proyecto

```text
.
|-- .github/workflows/ci.yml
|-- docs/TPO2.md
|-- reports/pytest-report.html
|-- src/descuentos/
|   |-- __init__.py
|   |-- calculator.py
|   `-- main.py
|-- tests/test_calculator.py
|-- pyproject.toml
|-- requirements.txt
`-- README.md
```

### Casos de prueba definidos

| Caso | Contexto | Datos de entrada | Resultado esperado |
|---|---|---|---|
| Caso exitoso | Cliente premium realiza una compra valida | Monto: 10000, cliente: premium | Precio final: 9000 |
| Caso de error | Se ingresa un monto negativo | Monto: -1, cliente: regular | Se lanza `ValueError` |
| Caso borde | Compra exactamente en el limite del descuento adicional | Monto: 100000, cliente: vip | Precio final: 75000 |
| Caso de error adicional | Se ingresa un tipo de cliente inexistente | Monto: 5000, cliente: estudiante | Se lanza `ValueError` |

## 3. Parte 2 - Automatizacion de pruebas

Los tests fueron automatizados con Python y `pytest`. El archivo principal de pruebas es `tests/test_calculator.py`.

Tests implementados:

- `test_cliente_premium_recibe_descuento_exitoso`
- `test_monto_negativo_genera_error`
- `test_compra_en_limite_recibe_descuento_adicional`
- `test_tipo_cliente_desconocido_genera_error`

Comando utilizado para ejecutar las pruebas localmente:

```bash
pytest --html=reports/pytest-report.html --self-contained-html
```

Resultado local obtenido:

```text
4 passed
```

## 4. Parte 3 - Pipeline CI/CD

Se configuro GitHub Actions mediante el archivo `.github/workflows/ci.yml`.

El pipeline realiza los siguientes pasos:

1. Descarga el repositorio con `actions/checkout`.
2. Configura Python 3.12 con `actions/setup-python`.
3. Instala las dependencias desde `requirements.txt`.
4. Ejecuta los tests con `pytest`.
5. Genera el reporte HTML.
6. Publica el reporte como artefacto llamado `pytest-html-report`.

El pipeline se ejecuta automaticamente en:

- `push`
- `pull_request`

Fragmento principal del workflow:

```yaml
- name: Run automated tests
  run: |
    mkdir -p reports
    pytest --html=reports/pytest-report.html --self-contained-html

- name: Upload test report artifact
  uses: actions/upload-artifact@v4
  with:
    name: pytest-html-report
    path: reports/pytest-report.html
```

## 5. Parte 4 - Evidencia y analisis

### Evidencia del pipeline

Al subir el proyecto a GitHub y realizar un `push`, debe observarse el workflow `Python tests` dentro de la pestaña **Actions** del repositorio.

Capturas a incorporar luego de subir el repositorio:

- Captura 1: workflow ejecutandose en GitHub Actions.
- Captura 2: workflow finalizado correctamente con estado verde.
- Captura 3: artefacto `pytest-html-report` disponible para descarga.

### Resultado de los tests

| Test | Resultado |
|---|---|
| Cliente premium recibe descuento exitoso | OK |
| Monto negativo genera error | OK |
| Compra en limite recibe descuento adicional | OK |
| Tipo de cliente desconocido genera error | OK |

Resultado general:

```text
4 passed
```

### Explicacion de resultados

Los tests finalizaron correctamente porque la funcion respeta las reglas de negocio definidas. El caso exitoso confirma el descuento para cliente premium. El caso de error valida que un monto negativo no sea aceptado. El caso borde comprueba que una compra exactamente igual a $100000 recibe el descuento adicional. El caso de cliente desconocido verifica que la aplicacion rechace datos no contemplados.

### Ventajas de automatizar pruebas dentro del pipeline

Automatizar pruebas dentro del pipeline permite detectar errores de forma temprana cada vez que se sube codigo al repositorio. Esto evita depender solamente de pruebas manuales y reduce la posibilidad de integrar cambios defectuosos.

### Impacto en la calidad del software

El impacto es positivo porque aumenta la confianza sobre el codigo, permite validar cambios de manera repetible y ayuda a mantener estable la aplicacion. Tambien mejora la trazabilidad, ya que cada ejecucion queda registrada en los logs de GitHub Actions.

## 6. Parte 5 - Reflexion

### Beneficios de automatizar pruebas frente a hacerlas manualmente

Automatizar pruebas ahorra tiempo, evita errores humanos y permite repetir las validaciones todas las veces que sea necesario. En proyectos con cambios frecuentes, esto es especialmente importante porque ayuda a encontrar regresiones rapidamente.

### Dificultades encontradas al implementar el pipeline

La principal dificultad fue asegurar que el entorno de ejecucion tuviera todas las dependencias necesarias y que el comando de pruebas generara correctamente el reporte HTML. Tambien es importante respetar la estructura de carpetas para que los tests puedan importar la aplicacion sin problemas.

### Aplicacion en un entorno real

Aplicaria este enfoque en cualquier proyecto donde varias personas realicen cambios sobre el mismo codigo. Por ejemplo, en sistemas web, APIs, aplicaciones internas de empresas o sistemas de facturacion, donde un error puede afectar procesos importantes.

## 7. Conclusiones personales

Este trabajo permite comprender como se conectan el desarrollo, el testing y DevOps. La automatizacion de pruebas no reemplaza completamente el criterio humano, pero aporta una base objetiva para validar el funcionamiento del software ante cada cambio.

Tambien permite entender que un pipeline no solo ejecuta comandos, sino que funciona como un control de calidad continuo dentro del ciclo de desarrollo.

## 8. Futuras mejoras

Como mejoras futuras se podrian agregar:

- Mas reglas de descuento.
- Tests parametrizados para cubrir mas combinaciones.
- Analisis de cobertura con `pytest-cov`.
- Validaciones de estilo con `ruff`.
- Publicacion del reporte como pagina estatica.
- Separacion de ambientes para desarrollo, testing y produccion.

## 9. Bibliografia

- Documentacion oficial de Python: https://docs.python.org/3/
- Documentacion oficial de pytest: https://docs.pytest.org/
- Documentacion oficial de GitHub Actions: https://docs.github.com/actions
- Documentacion de pytest-html: https://pytest-html.readthedocs.io/
