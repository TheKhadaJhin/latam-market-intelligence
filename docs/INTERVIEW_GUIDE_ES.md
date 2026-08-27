# Guía para explicar el proyecto en una entrevista

## Explicación para una persona no técnica

El proyecto compara seis mercados latinoamericanos con información pública del Banco Mundial.
Toma datos como crecimiento, inflación, empleo, conectividad digital y comercio; verifica que
sean utilizables; y produce un ranking acompañado de las razones que explican cada resultado.

No pretende decir automáticamente dónde debe expandirse una empresa. Sirve para organizar una
primera conversación estratégica, identificar fortalezas y riesgos, y mostrar qué información
adicional hace falta antes de decidir.

## Explicación técnica corta

Construí un producto de datos reproducible. Un adaptador consulta ocho indicadores del API del
Banco Mundial con timeout, reintentos, concurrencia limitada y validación de contrato. El
pipeline conserva los payloads crudos, realiza upserts idempotentes en PostgreSQL o SQLite,
calcula tres escenarios explicables y registra cada ejecución.

dbt transforma los datos en capas staging y marts con pruebas de frescura, relaciones,
unicidad y cobertura. FastAPI publica rankings e historial; Streamlit consume esa API; y el
repositorio incluye migraciones, Docker, CI, análisis de seguridad, métricas y runbooks.

## Decisiones que conviene defender

### ¿Por qué no usaste machine learning?

Porque no había una variable objetivo confiable ni suficientes decisiones históricas para
entrenar y validar un modelo. Un score explícito permite discutir cada supuesto. Llamarlo IA
habría sido exagerado.

### ¿Cómo manejas valores faltantes?

Uso el último dato disponible dentro de una ventana máxima de tres años. Exijo 75% de cobertura
ponderada, informo la cobertura y aplico una penalización pequeña. Nunca convierto un faltante
en cero de forma silenciosa.

### ¿Por qué guardas una instantánea?

Permite reproducir una demo y una prueba aunque la API cambie o esté caída. El modo conectado
sigue siendo la fuente normal; la instantánea es un fixture real y documentado.

### ¿Qué hace idempotente al pipeline?

Cada observación se identifica por país, indicador y año. Repetir una ejecución actualiza esa
clave en lugar de duplicar filas. Los scores se reemplazan únicamente dentro de la partición de
año y escenario.

### ¿Cuáles son los límites más importantes?

Los indicadores son anuales, pueden revisarse y no capturan regulación, competencia, clientes
ni diferencias locales. Además, los pesos son decisiones de análisis. Por eso el resultado es
una ayuda comparativa y no una recomendación final.

## Historia STAR sugerida

- **Situación:** una empresa necesita ordenar una primera comparación de mercados LATAM.
- **Tarea:** producir evidencia reproducible y explicable, no solo un notebook.
- **Acción:** diseñé contratos, pipeline, warehouse, controles de calidad, scoring, API,
  dashboard y operación automatizada.
- **Resultado:** cualquier persona puede ejecutar la misma instantánea, inspeccionar el origen
  de los datos, cambiar el escenario y entender por qué cambia el ranking.
