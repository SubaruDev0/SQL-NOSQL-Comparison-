# Explicación técnica

Este documento agrupa la información técnica del proyecto: qué bases de datos se usan, credenciales por defecto en el entorno local, comandos útiles para inspeccionar las bases, dónde se crean/insertan datos, dónde están las conexiones y las consultas, y qué muestra la aplicación.

---

## 1) Resumen rápido

- Base de datos relacional (SQL): PostgreSQL
  - Nombre de la base de datos usada por la app: `universidad_db`
  - Usuario: `postgres`
  - Contraseña (por defecto en este proyecto local): `postgres`
  - Host local: `localhost` puerto `5432`

- Base de datos documental (NoSQL): MongoDB
  - Nombre de la base de datos usada por la app: `universidad_db`
  - Host local: `localhost` puerto `27017`
  - En despliegue (Streamlit Cloud) se usa `MONGO_URI` (MongoDB Atlas) si está definido

> Nota: estas credenciales son para desarrollo local. En producción/hosted debes usar variables de entorno seguras.

---

## 2) Comandos útiles (PostgreSQL)

- Listar bases de datos (desde shell):

```bash
psql -U postgres -h localhost -p 5432 -l
```

- Conectarse a la base `universidad_db`:

```bash
psql -U postgres -h localhost -p 5432 -d universidad_db
```

- Dentro de `psql`: listar tablas

```
\dt
```

- Ver esquema / columnas de una tabla (ej. `estudiantes`):

```
\d estudiantes
```

- Contar registros:

```sql
SELECT COUNT(*) FROM estudiantes;
```

- Ver índices:

```sql
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'estudiantes';
```

- Eliminar/crear base de datos (desde shell):

```bash
PGPASSWORD=postgres psql -U postgres -h localhost -c "DROP DATABASE IF EXISTS universidad_db;"
PGPASSWORD=postgres psql -U postgres -h localhost -c "CREATE DATABASE universidad_db;"
```

- Reiniciar servicio (Linux systemd):

```bash
sudo systemctl restart postgresql@16-main
sudo systemctl status postgresql@16-main
```

---

## 3) Comandos útiles (MongoDB / mongosh)

- Abrir `mongosh` (cliente interactivo):

```bash
mongosh
```

- En `mongosh`, listar bases de datos:

```
show dbs
```

- Usar la base `universidad_db` y listar colecciones:

```
use universidad_db
show collections
```

- Contar documentos en la colección principal:

```
db.estudiantes.countDocuments()
```

- Ver un documento de ejemplo:

```
db.estudiantes.findOne()
```

- Ver índices:

```
db.estudiantes.getIndexes()
```

- Borrar base de datos (para reiniciar datos):

```
use universidad_db
db.dropDatabase()
```

---

## 4) Dónde se crean y cargan las bases / datos en el proyecto

- `cargar_datos.py` — script rápido que recrea la base `universidad_db` en PostgreSQL y copia los registros a MongoDB (configurable para 1k / 10k registros según parámetros en el script). Es el script recomendado para desarrollo local rápido.

- `setup_databases_fixed.py` — script más completo (original del proyecto) que también crea la base y carga datos desde `data_nosql.json` / `data_sql.sql`. Fue usado originalmente para poblar ambas DBs.

- `generate_data.py` — script que genera los datos sintéticos (archivos). Normalmente no es necesario ejecutarlo si usas `cargar_datos.py` que genera a vuelo.

> Ubicaciones de archivos clave:
> - Creación / inserción SQL: `cargar_datos.py` y `setup_databases_fixed.py` (líneas donde se ejecutan `CREATE TABLE` y `INSERT INTO`)
> - Generación de datos sinteticos: `generate_data.py` (guarda `data_nosql.json` y `data_sql.sql`)

---

## 5) Dónde están las conexiones (en el proyecto)

- `app.py` contiene las funciones de conexión y uso de las bases:
  - `get_postgres_connection()` — crea/cachea la conexión a PostgreSQL (usa `psycopg2` y `PG_CONFIG` con host/port/user/password/database)
  - `get_mongo_connection()` — crea/cachea la conexión a MongoDB (usa `MongoClient` con host/port o `MONGO_URI` si `IS_CLOUD`)

- Variables relevantes en `app.py`:
  - `PG_CONFIG` — host/port/user/password/database para PostgreSQL
  - `MONGO_CONFIG` / `MONGO_URI` — configuración para MongoDB (local o Atlas)
  - `IS_CLOUD` — flag que detecta ejecución en Streamlit Cloud (usa var. de entorno)

---

## 6) Dónde están las consultas (SQL y NoSQL)

- SQL (PostgreSQL) — en `app.py` dentro de la función `search_student_sql(student_name)`:
  - Se ejecuta una consulta con múltiples `JOIN` que une `estudiantes`, `universidades`, `paises` y `matriculas`. La consulta obtiene datos del estudiante, su universidad y estadísticas de sus matrículas (COUNT, AVG, SUM).
  - También existe `get_all_students_postgres()` que consulta `SELECT nombre, apellido FROM estudiantes ORDER BY apellido, nombre` para poblar el combobox.

- NoSQL (MongoDB) — en `app.py` dentro de la función `search_student_nosql(student_name)`:
  - Implementación final: búsqueda por nombre completo con `$expr` y `$concat` para comparar `nombre + ' ' + apellido` con la cadena buscada (esto maneja nombres compuestos correctamente).
  - `get_all_students_mongo()` se usa como fallback si PostgreSQL no está disponible; obtiene `nombre` y `apellido` desde la colección `estudiantes` y ordena por apellido/nombre.

---

## 7) Qué imprime / muestra la página (`app.py`) — descripción técnica

- Barra lateral (`st.sidebar`): muestra el estado de las conexiones
  - Indica si PostgreSQL está conectado o no
  - Indica si MongoDB está conectado o no
  - Muestra si la app se ejecuta en Streamlit Cloud o localmente

- Controles principales:
  - Slider `num_searches` — cantidad de estudiantes a buscar (ahora hasta 10,000)
  - `multiselect` para elegir estudiantes (opciones cargadas desde `students_list`, que proviene de PostgreSQL o MongoDB)
  - Botones: "Buscar TODOS en SQL", "Buscar TODOS en NoSQL", "Limpiar Resultados"

- Resultados:
  - Para cada motor (SQL / NoSQL) se muestran: texto de progreso, barra de progreso, métricas (Tiempo TOTAL, Promedio, Búsquedas) y una lista paginada de expanders con los estudiantes encontrados.
  - Cada expander muestra: Email, Edad, Promedio, Universidad, Ciudad, País, Cursos, Créditos, etc.

- Session state keys (importante para debugging):
  - `st.session_state.students_list` — lista mostrada en el multiselect
  - `st.session_state.selected_students` — lista seleccionada por el usuario
  - `st.session_state.sql_results`, `st.session_state.nosql_results` — resultados guardados
  - `st.session_state.sql_time`, `st.session_state.nosql_time` — tiempos totales
  - `st.session_state.sql_count`, `st.session_state.nosql_count` — número de búsquedas realizadas
  - `st.session_state.sql_show_count`, `st.session_state.nosql_show_count` — contadores de paginación

---

## 8) Comandos para reproducir la demo localmente (rápido)

```bash
# 1) Asegúrate de tener servicios corriendo
sudo systemctl start postgresql@16-main
sudo systemctl start mongod

# 2) Activar virtualenv (si existe)
source .venv/bin/activate

# 3) Cargar datos rápidos (script recomendado)
python cargar_datos.py

# 4) Ejecutar la app
streamlit run app.py
```

### Comandos alternativos / completos

```bash
# Generar datos (si quieres regenerar archivos):
python generate_data.py

# Cargar datos desde scripts completos
python setup_databases_fixed.py

# Ver conteos rápidos
psql -U postgres -d universidad_db -c "SELECT COUNT(*) FROM estudiantes;"
mongosh --eval "db = db.getSiblingDB('universidad_db'); print('Mongo count:', db.estudiantes.countDocuments())"
```

---

## 9) Variables de entorno y despliegue (Streamlit Cloud)

- `MONGO_URI` — si vas a desplegar en la nube, crea un cluster en MongoDB Atlas, copia la URI y colócala en las variables de entorno de la app:

```
MONGO_URI="mongodb+srv://<user>:<pass>@cluster0.xxxxxx.mongodb.net" 
```

- La app detecta `IS_CLOUD` y en ese caso no intenta conectar a PostgreSQL local (porque Streamlit Cloud no mantiene un PostgreSQL local). En la nube, PostgreSQL debe ser un servicio externo (p. ej. ElephantSQL, Supabase) y sus credenciales deben guardarse como variables de entorno y adaptarse en `app.py`.

---

## 10) Troubleshooting (errores comunes y soluciones rápidas)

- Error `connection refused` a PostgreSQL: verifica que el servicio esté corriendo y que el puerto 5432 esté escuchando. Ejecuta:

```bash
sudo systemctl status postgresql@16-main
sudo journalctl -u postgresql@16-main -n 100
```

- Error `numeric field overflow` al insertar promedios: se ajustó el script para usar valores ≤ 9.99 (DECIMAL(3,2)). Si aparece, revisa `cargar_datos.py` para restringir random.uniform(6.0, 9.99).

- MongoDB `Connection refused`: verifica `mongod`:

```bash
sudo systemctl status mongod
sudo journalctl -u mongod -n 100
```

- Si la app tarda mucho en renderizar: la solución implementada es paginación (20 por página) y "Ver más".

- Si la demo en la nube no debe usar PostgreSQL, edita `app.py` o configura un PostgreSQL en la nube y proporciona sus credenciales en variables de entorno.

---

## 11) Pequeño mapa del código (funciones/archivos clave)

- `app.py`
  - `get_postgres_connection()` — conexión a PostgreSQL
  - `get_mongo_connection()` — conexión a MongoDB (local o Atlas via `MONGO_URI`)
  - `get_all_students_postgres()` — lista estudiantes desde PostgreSQL (fallback a Mongo)
  - `get_all_students_mongo()` — lista estudiantes desde MongoDB
  - `search_student_sql(student_name)` — query SQL con JOINs
  - `search_student_nosql(student_name)` — búsqueda en MongoDB (usa `$expr` + `$concat` en la versión final)
  - UI: manejo de `st.session_state` y paginación (`sql_show_count`, `nosql_show_count`)

- `cargar_datos.py` — crea BD en PostgreSQL y copia documentos a MongoDB. Parametrizable (NUM_ESTUDIANTES)
- `setup_databases_fixed.py` — script alternativo para cargar datos desde JSON/SQL
- `generate_data.py` — genera los datos sintéticos (archivos `data_nosql.json` y `data_sql.sql`)

---

## 12) Ejemplos rápidos de consultas que se usan internamente

- SQL (simplificado):

```sql
SELECT e.id, e.nombre, e.apellido, e.email, e.edad, e.carrera, e.año_ingreso, e.promedio,
       u.nombre as universidad, u.ciudad as ciudad_universidad,
       p_uni.nombre as pais_universidad, p_ori.nombre as pais_origen,
       COUNT(m.id) as total_cursos, AVG(m.nota) as promedio_cursos, SUM(m.creditos) as total_creditos
FROM estudiantes e
JOIN universidades u ON e.universidad_id = u.id
JOIN paises p_uni ON u.pais_id = p_uni.id
JOIN paises p_ori ON e.pais_origen_id = p_ori.id
LEFT JOIN matriculas m ON e.id = m.estudiante_id
WHERE CONCAT(e.nombre, ' ', e.apellido) ILIKE %s
GROUP BY e.id, ...
LIMIT 1;
```

- MongoDB (interno final):

```js
// Busca por nombre completo (concat en documento)
db.estudiantes.findOne({
  $expr: { $eq: [ { $concat: ['$nombre', ' ', '$apellido'] }, 'Jose Miguel Falcón 1623' ] }
});
```

---

## 13) Recomendaciones finales

- Para la demo en la nube: usa MongoDB Atlas (setear `MONGO_URI`) y opcionalmente un PostgreSQL en la nube si quieres comparar con SQL en producción.
- Para medir con precisión, usar `cargar_datos.py` con el número deseado de estudiantes y luego correr pruebas con el slider (100, 1000, 10000).
- Mantener las credenciales fuera del repo y usar variables de entorno en producción.

---

Si quieres, puedo:
- Añadir instrucciones para configurar una cuenta gratuita en MongoDB Atlas y conectar la app en Streamlit Cloud.
- Añadir pequeños scripts de comprobación automatizados (pytest o scripts de verificación rápida).

Fin del documento.

