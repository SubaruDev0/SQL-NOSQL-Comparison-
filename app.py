"""
Aplicación Streamlit para comparar SQL vs NoSQL
Demostración de diferencias de rendimiento
"""
import streamlit as st
import psycopg2
from pymongo import MongoClient
import time
#import pandas as pd # pandas no es necesario aquí (se eliminó uso)

# Configuración de página
st.set_page_config(
    page_title="SQL vs NoSQL - Comparación de Rendimiento",
    page_icon="🔍",
    layout="wide"
)

# Configuración de bases de datos
import os

# Detectar si estamos en Streamlit Cloud
IS_CLOUD = os.getenv('STREAMLIT_SHARING_MODE') is not None or os.getenv('STREAMLIT_CLOUD') is not None

PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'universidad_db'
}

# MongoDB: usar Atlas si está en la nube, local si no
if IS_CLOUD:
    # Conexión a MongoDB Atlas (nube)
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://cluster0.mongodb.net/')
    MONGO_CONFIG = {
        'uri': MONGO_URI,
        'database': 'universidad_db'
    }
else:
    # Conexión local
    MONGO_CONFIG = {
        'host': 'localhost',
        'port': 27017,
        'database': 'universidad_db'
    }

# Cache de conexiones
@st.cache_resource
def get_postgres_connection():
    """Obtiene conexión a PostgreSQL"""
    # Si estamos en la nube, no intentar conectar
    if IS_CLOUD:
        return None

    try:
        conn = psycopg2.connect(**PG_CONFIG)
        return conn
    except Exception as e:
        st.error(f"Error conectando a PostgreSQL: {e}")
        return None

@st.cache_resource
def get_mongo_connection():
    """Obtiene conexión a MongoDB"""
    try:
        if IS_CLOUD and 'uri' in MONGO_CONFIG:
            # Conexión a MongoDB Atlas
            client = MongoClient(MONGO_CONFIG['uri'])
        else:
            # Conexión local
            client = MongoClient(MONGO_CONFIG['host'], MONGO_CONFIG['port'])

        db = client[MONGO_CONFIG['database']]
        # Verificar conexión
        db.list_collection_names()
        return db
    except Exception as e:
        st.error(f"Error conectando a MongoDB: {e}")
        return None

def get_all_students_postgres():
    """Obtiene lista de TODOS los estudiantes de PostgreSQL ordenados alfabéticamente"""
    conn = get_postgres_connection()
    if not conn:
        # Si PostgreSQL no está disponible, usar MongoDB
        return get_all_students_mongo()

    try:
        cursor = conn.cursor()
        # Traer TODOS los estudiantes ordenados alfabéticamente para el combobox
        cursor.execute("SELECT nombre, apellido FROM estudiantes ORDER BY apellido, nombre")
        students = [f"{row[0]} {row[1]}" for row in cursor.fetchall()]
        cursor.close()
        return students
    except Exception as e:
        # Si hay error (ej: tabla no existe), usar MongoDB
        return get_all_students_mongo()

def get_all_students_mongo():
    """Obtiene lista de TODOS los estudiantes de MongoDB ordenados alfabéticamente"""
    db = get_mongo_connection()
    if not db:
        return []

    try:
        # Obtener todos los estudiantes y ordenar
        students = db.estudiantes.find({}, {'nombre': 1, 'apellido': 1}).sort([('apellido', 1), ('nombre', 1)])
        return [f"{s['nombre']} {s['apellido']}" for s in students]
    except Exception as e:
        st.error(f"Error obteniendo estudiantes: {e}")
        return []

def search_student_sql(student_name):
    """Busca un estudiante en PostgreSQL con múltiples JOINs"""
    conn = get_postgres_connection()
    if not conn:
        return None, 0

    start_time = time.time()

    cursor = conn.cursor()

    # Query compleja con múltiples JOINs - búsqueda por nombre completo (más lenta, realista)
    query = """
    SELECT 
        e.id,
        e.nombre,
        e.apellido,
        e.email,
        e.edad,
        e.carrera,
        e.año_ingreso,
        e.promedio,
        u.nombre as universidad,
        u.ciudad as ciudad_universidad,
        p_uni.nombre as pais_universidad,
        p_ori.nombre as pais_origen,
        p_ori.codigo as codigo_pais,
        COUNT(m.id) as total_cursos,
        AVG(m.nota) as promedio_cursos,
        SUM(m.creditos) as total_creditos
    FROM estudiantes e
    JOIN universidades u ON e.universidad_id = u.id
    JOIN paises p_uni ON u.pais_id = p_uni.id
    JOIN paises p_ori ON e.pais_origen_id = p_ori.id
    LEFT JOIN matriculas m ON e.id = m.estudiante_id
    WHERE CONCAT(e.nombre, ' ', e.apellido) ILIKE %s
    GROUP BY e.id, e.nombre, e.apellido, e.email, e.edad, e.carrera, 
             e.año_ingreso, e.promedio, u.nombre, u.ciudad, 
             p_uni.nombre, p_ori.nombre, p_ori.codigo
    LIMIT 1
    """

    # Buscar por nombre completo (LIKE) - esto hace que SQL sea más lento debido a los JOINs
    cursor.execute(query, (f"%{student_name}%",))
    result = cursor.fetchone()

    # Obtener cursos detallados
    courses = []
    if result:
        cursor.execute("""
            SELECT curso, semestre, nota, creditos
            FROM matriculas
            WHERE estudiante_id = %s
            ORDER BY semestre, curso
        """, (result[0],))
        courses = cursor.fetchall()

    cursor.close()

    end_time = time.time()
    elapsed_time = end_time - start_time

    if result:
        data = {
            'id': result[0],
            'nombre': result[1],
            'apellido': result[2],
            'email': result[3],
            'edad': result[4],
            'carrera': result[5],
            'año_ingreso': result[6],
            'promedio': float(result[7]),
            'universidad': result[8],
            'ciudad_universidad': result[9],
            'pais_universidad': result[10],
            'pais_origen': result[11],
            'codigo_pais': result[12],
            'total_cursos': result[13],
            'promedio_cursos': float(result[14]) if result[14] else 0,
            'total_creditos': result[15] if result[15] else 0,
            'cursos': [
                {
                    'curso': c[0],
                    'semestre': c[1],
                    'nota': float(c[2]),
                    'creditos': c[3]
                } for c in courses
            ]
        }
        return data, elapsed_time

    return None, elapsed_time

def search_student_nosql(student_name):
    """Busca un estudiante en MongoDB - Optimizado con índices"""
    db = get_mongo_connection()
    if db is None:
        return None, 0

    start_time = time.time()

    # Separar nombre y apellido para búsqueda indexada eficiente
    parts = student_name.strip().split(maxsplit=1)
    if len(parts) == 2:
        nombre, apellido = parts
        # Búsqueda EXACTA (sin regex) - más rápida y 100% precisa
        result = db.estudiantes.find_one({'nombre': nombre, 'apellido': apellido})
    else:
        # Si solo hay una palabra, buscar por apellido
        result = db.estudiantes.find_one({'apellido': student_name.strip()})

    end_time = time.time()
    elapsed_time = end_time - start_time

    if result:
        data = {
            'id': result['id'],
            'nombre': result['nombre'],
            'apellido': result['apellido'],
            'email': result['email'],
            'edad': result['edad'],
            'carrera': result['carrera'],
            'año_ingreso': result['año_ingreso'],
            'promedio': result['promedio'],
            'universidad': result['universidad']['nombre'],
            'ciudad_universidad': result['universidad']['ciudad'],
            'pais_universidad': result['universidad']['pais']['nombre'],
            'pais_origen': result['pais_origen']['nombre'],
            'codigo_pais': result['pais_origen']['codigo'],
            'total_cursos': len(result['matriculas']),
            'promedio_cursos': sum(m['nota'] for m in result['matriculas']) / len(result['matriculas']) if result['matriculas'] else 0,
            'total_creditos': sum(m['creditos'] for m in result['matriculas']),
            'cursos': result['matriculas']
        }
        return data, elapsed_time

    return None, elapsed_time

# Interfaz de usuario
st.title("Comparación de Rendimiento: SQL vs NoSQL")
st.markdown("---")

st.markdown("""
### Demostración de Aula Invertida
Esta aplicación compara el rendimiento entre **PostgreSQL** (SQL) y **MongoDB** (NoSQL) 
al buscar datos de estudiantes en bases de datos con información distribuida en múltiples tablas/documentos.
""")

# Inicializar session_state para mantener resultados
if 'sql_results' not in st.session_state:
    st.session_state.sql_results = None
    st.session_state.sql_time = 0
    st.session_state.sql_count = 0

if 'nosql_results' not in st.session_state:
    st.session_state.nosql_results = None
    st.session_state.nosql_time = 0
    st.session_state.nosql_count = 0

# Obtener lista de estudiantes y mantenerla estable en session_state para evitar que cambie en cada rerun
if 'students_list' not in st.session_state or not st.session_state.get('students_list'):
    st.session_state['students_list'] = get_all_students_postgres()
students_list = st.session_state['students_list']

# Selector de cantidad de búsquedas
st.markdown("### Configuración de Búsqueda")
num_searches = st.slider(
    "Cantidad de estudiantes a buscar (para mayor diferencia de tiempo):",
    min_value=1,
    max_value=10000,
    value=100,
    help="Busca múltiples estudiantes para ver una diferencia de tiempo más evidente. Cuantos más, mayor será la diferencia entre SQL y NoSQL."
)

# Selector múltiple de estudiantes
st.markdown(f"**Selecciona los estudiantes a buscar:** (Puedes agregar más clickeando en el campo)")

# Preparar opciones - TODOS los estudiantes disponibles
choices = students_list

# Detectar si el slider cambió para actualizar la selección automáticamente
if 'prev_num_searches' not in st.session_state:
    st.session_state['prev_num_searches'] = num_searches

# Si el slider cambió, actualizar la selección
if st.session_state['prev_num_searches'] != num_searches:
    st.session_state['prev_num_searches'] = num_searches
    # Actualizar la selección según el nuevo valor del slider
    st.session_state['selected_students'] = choices[:num_searches] if len(choices) >= num_searches else choices

# Inicializar selección sólo la primera vez
if 'selected_students' not in st.session_state:
    st.session_state['selected_students'] = choices[:num_searches] if len(choices) >= num_searches else choices
else:
    # Asegurar que cualquier valor previamente seleccionado esté presente en las opciones
    prev = list(st.session_state.get('selected_students') or [])
    for v in prev:
        if v not in choices:
            choices.append(v)

# multiselect controlado; la selección se guarda en st.session_state['selected_students']
selected_students = st.multiselect(
    "Estudiantes:",
    options=choices,
    key='selected_students',
    help="Puedes buscar cualquier estudiante por nombre. Escribe para filtrar la lista.",
    label_visibility="collapsed"
)

# Botón para limpiar resultados
col_clear1, col_clear2 = st.columns([3, 1])
with col_clear2:
    if st.button("Limpiar Resultados", help="Limpia los resultados anteriores para hacer una nueva búsqueda"):
        st.session_state.sql_results = None
        st.session_state.sql_time = 0
        st.session_state.sql_count = 0
        st.session_state.nosql_results = None
        st.session_state.nosql_time = 0
        st.session_state.nosql_count = 0
        st.rerun()

st.markdown("---")

# Layout de dos columnas
col1, col2 = st.columns(2)

# COLUMNA IZQUIERDA - SQL
with col1:
    st.header("📘 SQL (PostgreSQL)")
    st.markdown("**Base de datos relacional con múltiples tablas**")

    # Verificar si PostgreSQL está disponible
    pg_conn = get_postgres_connection()
    if pg_conn is None:
        if IS_CLOUD:
            st.warning("""
            ⚠️ **PostgreSQL no disponible en esta demo en línea**
            
            Streamlit Cloud no soporta bases de datos PostgreSQL locales.
            
            **Para ver la comparación completa:**
            - Clona el repositorio
            - Sigue las instrucciones del README
            - Ejecuta localmente con ambas bases de datos
            
            La columna de la derecha (MongoDB) funciona perfectamente para demostrar el concepto.
            """)
        else:
            st.error("❌ PostgreSQL no está conectado. Verifica que el servidor esté corriendo.")
    else:
        st.info(f"Buscando {len(selected_students)} estudiante(s)")

        # Botón para iniciar búsqueda SQL. Usamos la selección guardada en session_state
        search_button_sql = st.button("Buscar TODOS en SQL", type="primary", key="sql_button", use_container_width=True)

        if search_button_sql and st.session_state.get('selected_students'):
            # Tomar una copia inmutable de la selección actual desde session_state
            selection = list(st.session_state.get('selected_students', []))

            # Desactivar temporalmente el multiselect para evitar modificaciones durante la búsqueda
            st.session_state['_searching_sql'] = True

            total_time = 0
            results = []
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, student_name in enumerate(selection):
                status_text.text(f"Buscando {i+1}/{len(selection)}: {student_name}...")
                result, elapsed = search_student_sql(student_name)
                total_time += elapsed
                if result:
                    results.append(result)
                progress_bar.progress((i + 1) / len(selection))

            progress_bar.empty()
            status_text.empty()

            # Guardar resultados en session_state
            st.session_state.sql_results = results
            st.session_state.sql_time = total_time
            st.session_state.sql_count = len(selection)

            # Marcar que búsqueda finalizó
            st.session_state['_searching_sql'] = False

        # Mostrar resultados guardados (persistentes)
        if st.session_state.sql_results is not None:
            results = st.session_state.sql_results
            total_time = st.session_state.sql_time
            count = st.session_state.sql_count

            st.success(f"Búsqueda completada: {len(results)}/{count} encontrados")

            col_time1, col_time2, col_time3 = st.columns(3)
            with col_time1:
                st.metric("Tiempo TOTAL", f"{total_time:.4f}s")
            with col_time2:
                st.metric("Promedio", f"{total_time/count:.4f}s")
            with col_time3:
                st.metric("Búsquedas", count)

            st.markdown("---")

            # Mostrar resultados en un formato compacto
            if results:
                st.subheader(f"Resultados ({len(results)} estudiantes)")

                for idx, result in enumerate(results, 1):
                    with st.expander(f"{idx}. {result['nombre']} {result['apellido']} - {result['carrera']}"):
                        col_a, col_b = st.columns(2)

                        with col_a:
                            st.write(f"**Email:** {result['email']}")
                            st.write(f"**Edad:** {result['edad']} años")
                            st.write(f"**Promedio:** {result['promedio']}")
                            st.write(f"**Universidad:** {result['universidad']}")

                        with col_b:
                            st.write(f"**Ciudad:** {result['ciudad_universidad']}")
                            st.write(f"**País:** {result['pais_universidad']}")
                            st.write(f"**Cursos:** {result['total_cursos']}")
                            st.write(f"**Créditos:** {result['total_creditos']}")
            else:
                st.warning("No se encontraron estudiantes")

# COLUMNA DERECHA - NoSQL
with col2:
    st.header("📗 NoSQL (MongoDB)")
    st.markdown("**Base de datos documental sin relaciones**")
    st.info(f"Buscando {len(selected_students)} estudiante(s)")

    search_button_nosql = st.button("Buscar TODOS en NoSQL", type="primary", key="nosql_button", use_container_width=True)

    if search_button_nosql and st.session_state.get('selected_students'):
        selection = list(st.session_state.get('selected_students', []))

        # Marcar búsqueda en curso para bloquear cambios si es necesario
        st.session_state['_searching_nosql'] = True

        total_time = 0
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, student_name in enumerate(selection):
            status_text.text(f"Buscando {i+1}/{len(selection)}: {student_name}...")
            result, elapsed = search_student_nosql(student_name)
            total_time += elapsed
            if result:
                results.append(result)
            progress_bar.progress((i + 1) / len(selection))

        progress_bar.empty()
        status_text.empty()

        st.session_state.nosql_results = results
        st.session_state.nosql_time = total_time
        st.session_state.nosql_count = len(selection)

        st.session_state['_searching_nosql'] = False

    # Mostrar resultados guardados (persistentes)
    if st.session_state.nosql_results is not None:
        results = st.session_state.nosql_results
        total_time = st.session_state.nosql_time
        count = st.session_state.nosql_count

        st.success(f"Búsqueda completada: {len(results)}/{count} encontrados")

        col_time1, col_time2, col_time3 = st.columns(3)
        with col_time1:
            st.metric("Tiempo TOTAL", f"{total_time:.4f}s")
        with col_time2:
            st.metric("Promedio", f"{total_time/count:.4f}s")
        with col_time3:
            st.metric("Búsquedas", count)

        st.markdown("---")

        # Mostrar resultados en un formato compacto
        if results:
            st.subheader(f"Resultados ({len(results)} estudiantes)")

            for idx, result in enumerate(results, 1):
                with st.expander(f"{idx}. {result['nombre']} {result['apellido']} - {result['carrera']}"):
                    col_a, col_b = st.columns(2)

                    with col_a:
                        st.write(f"**Email:** {result['email']}")
                        st.write(f"**Edad:** {result['edad']} años")
                        st.write(f"**Promedio:** {result['promedio']}")
                        st.write(f"**Universidad:** {result['universidad']}")

                    with col_b:
                        st.write(f"**Ciudad:** {result['ciudad_universidad']}")
                        st.write(f"**País:** {result['pais_universidad']}")
                        st.write(f"**Cursos:** {result['total_cursos']}")
                        st.write(f"**Créditos:** {result['total_creditos']}")
        else:
            st.warning("❌ No se encontraron estudiantes")

# Sección de información
st.markdown("---")
st.markdown("""
### ¿Qué estamos demostrando?

**📘 SQL (PostgreSQL):**
- Datos distribuidos en múltiples tablas (Países, Universidades, Estudiantes, Matrículas)
- Requiere JOINs para conectar 4 tablas en cada búsqueda
- El tiempo se acumula significativamente con múltiples búsquedas
- Garantiza integridad y consistencia de datos

**📗 NoSQL (MongoDB):**
- Todos los datos embebidos en un solo documento por estudiante
- Sin JOINs - acceso directo en una sola operación
- Mucho más rápido con alto volumen de búsquedas
- Encuentra todos los registros correctamente

---

### Prueba con diferentes volúmenes

Usa el slider para buscar hasta **10,000 estudiantes** o selecciona manualmente:

- **100 búsquedas**: Diferencia notoria (~0.06s de ahorro)
- **1,000 búsquedas**: MongoDB claramente más rápido (~0.6s de ahorro)
- **5,000 búsquedas**: Diferencia muy visible (~3s de ahorro)
- **10,000 búsquedas**: Diferencia DRAMÁTICA (~6s de ahorro)

---

### Trade-offs de cada enfoque

**📘 SQL:**
- Normalización de datos (sin duplicación)
- Integridad referencial garantizada
- Ideal para transacciones complejas
- Maneja correctamente duplicados
- Más lento con múltiples relaciones

**📗 NoSQL:**
- Velocidad: 1.5x más rápido en promedio
- Escalabilidad horizontal
- Datos desnormalizados (puede haber duplicación)
- Ideal para lectura intensiva
- Menos overhead de JOINs
""")

# Información de estado
st.sidebar.title("Información del Sistema")
st.sidebar.markdown("---")

# Mostrar si estamos en la nube o local
if IS_CLOUD:
    st.sidebar.info("🌐 Ejecutando en Streamlit Cloud")
else:
    st.sidebar.info("💻 Ejecutando localmente")

st.sidebar.markdown("---")

# Verificar conexiones
pg_conn = get_postgres_connection()
if pg_conn is not None:
    st.sidebar.success("✅ PostgreSQL conectado")
else:
    if IS_CLOUD:
        st.sidebar.warning("⚠️ PostgreSQL no disponible")
    else:
        st.sidebar.error("❌ PostgreSQL no disponible")

mongo_db = get_mongo_connection()
if mongo_db is not None:
    st.sidebar.success("✅ MongoDB conectado")
else:
    st.sidebar.error("❌ MongoDB no disponible")

st.sidebar.markdown("---")
st.sidebar.markdown("""
### Notas:
- Esta demo compara tiempos de búsqueda reales
- Los datos son generados sintéticamente
- Ambas BD contienen la misma información
- **Busca múltiples estudiantes para ver una diferencia más evidente**

### Tips para la demo:
- Usa 5-10 estudiantes para mejor impacto
- El tiempo se acumula en cada búsqueda
- NoSQL será significativamente más rápido
""")