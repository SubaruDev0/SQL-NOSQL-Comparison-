"""
Script rápido para configurar las bases de datos con datos mínimos
"""
import psycopg2
from pymongo import MongoClient
from faker import Faker
import random

fake = Faker(['es_ES'])

# Configuración
PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'postgres'
}

MONGO_CONFIG = {
    'host': 'localhost',
    'port': 27017,
    'database': 'universidad_db'
}

def setup_postgresql():
    """Configura PostgreSQL con datos mínimos"""
    print("Configurando PostgreSQL...")
    
    # Crear base de datos
    conn = psycopg2.connect(**PG_CONFIG)
    conn.autocommit = True
    cursor = conn.cursor()
    
    cursor.execute("DROP DATABASE IF EXISTS universidad_db;")
    cursor.execute("CREATE DATABASE universidad_db;")
    print("✓ Base de datos creada")
    cursor.close()
    conn.close()
    
    # Conectar a la nueva BD
    pg_config = PG_CONFIG.copy()
    pg_config['database'] = 'universidad_db'
    conn = psycopg2.connect(**pg_config)
    cursor = conn.cursor()
    
    # Crear tablas
    print("Creando tablas...")
    cursor.execute("""
        CREATE TABLE paises (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            codigo VARCHAR(10) NOT NULL
        );
        
        CREATE TABLE universidades (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(200) NOT NULL,
            pais_id INTEGER REFERENCES paises(id),
            ciudad VARCHAR(100) NOT NULL
        );
        
        CREATE TABLE estudiantes (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            apellido VARCHAR(100) NOT NULL,
            email VARCHAR(200) NOT NULL,
            edad INTEGER NOT NULL,
            universidad_id INTEGER REFERENCES universidades(id),
            pais_origen_id INTEGER REFERENCES paises(id),
            carrera VARCHAR(100) NOT NULL,
            año_ingreso INTEGER NOT NULL,
            promedio DECIMAL(3,2) NOT NULL
        );
        
        CREATE TABLE matriculas (
            id SERIAL PRIMARY KEY,
            estudiante_id INTEGER REFERENCES estudiantes(id),
            curso VARCHAR(200) NOT NULL,
            semestre VARCHAR(20) NOT NULL,
            nota DECIMAL(3,2) NOT NULL,
            creditos INTEGER NOT NULL
        );
    """)
    conn.commit()
    print("✓ Tablas creadas")
    
    # Insertar datos
    print("Insertando datos...")
    
    # Países
    paises = []
    for i in range(50):
        cursor.execute(
            "INSERT INTO paises (nombre, codigo) VALUES (%s, %s) RETURNING id",
            (fake.country(), fake.country_code())
        )
        paises.append(cursor.fetchone()[0])
    conn.commit()
    print(f"✓ {len(paises)} países insertados")
    
    # Universidades
    universidades = []
    for i in range(100):
        cursor.execute(
            "INSERT INTO universidades (nombre, pais_id, ciudad) VALUES (%s, %s, %s) RETURNING id",
            (f"Universidad {fake.company()}", random.choice(paises), fake.city())
        )
        universidades.append(cursor.fetchone()[0])
    conn.commit()
    print(f"✓ {len(universidades)} universidades insertadas")
    
    # Estudiantes y matrículas
    NUM_ESTUDIANTES = 1000
    carreras = ['Ingeniería', 'Medicina', 'Derecho', 'Economía', 'Arquitectura', 'Psicología']
    cursos = ['Matemáticas', 'Física', 'Química', 'Historia', 'Literatura', 'Programación', 'Estadística']
    
    for i in range(NUM_ESTUDIANTES):
        nombre = fake.first_name()
        apellido = fake.last_name()
        
        cursor.execute(
            """INSERT INTO estudiantes (nombre, apellido, email, edad, universidad_id, 
               pais_origen_id, carrera, año_ingreso, promedio) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (nombre, apellido, fake.email(), random.randint(18, 30), 
             random.choice(universidades), random.choice(paises),
             random.choice(carreras), random.randint(2018, 2024), 
             round(random.uniform(6.0, 10.0), 2))
        )
        estudiante_id = cursor.fetchone()[0]
        
        # Matriculas para cada estudiante
        num_cursos = random.randint(3, 8)
        for j in range(num_cursos):
            cursor.execute(
                """INSERT INTO matriculas (estudiante_id, curso, semestre, nota, creditos)
                   VALUES (%s, %s, %s, %s, %s)""",
                (estudiante_id, random.choice(cursos), f"2024-{random.randint(1,2)}", 
                 round(random.uniform(6.0, 10.0), 2), random.choice([3, 4, 5]))
            )
        
        if (i + 1) % 100 == 0:
            conn.commit()
            print(f"  {i + 1} estudiantes insertados...")
    
    conn.commit()
    
    # Crear índices
    print("Creando índices...")
    cursor.execute("CREATE INDEX idx_estudiantes_nombre ON estudiantes(nombre, apellido);")
    cursor.execute("CREATE INDEX idx_matriculas_estudiante ON matriculas(estudiante_id);")
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM estudiantes")
    count = cursor.fetchone()[0]
    print(f"✓ {count} estudiantes en PostgreSQL")
    
    cursor.close()
    conn.close()
    return True

def setup_mongodb():
    """Configura MongoDB con datos mínimos"""
    print("\nConfigurando MongoDB...")
    
    # Conectar a PostgreSQL para obtener datos
    pg_config = PG_CONFIG.copy()
    pg_config['database'] = 'universidad_db'
    pg_conn = psycopg2.connect(**pg_config)
    pg_cursor = pg_conn.cursor()
    
    # Conectar a MongoDB
    client = MongoClient(MONGO_CONFIG['host'], MONGO_CONFIG['port'])
    db = client[MONGO_CONFIG['database']]
    
    # Limpiar colección
    db.estudiantes.drop()
    
    # Obtener todos los estudiantes con sus datos relacionados
    pg_cursor.execute("""
        SELECT 
            e.id, e.nombre, e.apellido, e.email, e.edad, e.carrera, 
            e.año_ingreso, e.promedio,
            u.nombre as uni_nombre, u.ciudad as uni_ciudad,
            p_uni.nombre as pais_uni, p_uni.codigo as codigo_uni,
            p_ori.nombre as pais_ori, p_ori.codigo as codigo_ori
        FROM estudiantes e
        JOIN universidades u ON e.universidad_id = u.id
        JOIN paises p_uni ON u.pais_id = p_uni.id
        JOIN paises p_ori ON e.pais_origen_id = p_ori.id
    """)
    
    estudiantes = pg_cursor.fetchall()
    print(f"Obtenidos {len(estudiantes)} estudiantes de PostgreSQL")
    
    # Crear documentos para MongoDB
    documentos = []
    for est in estudiantes:
        # Obtener matrículas
        pg_cursor.execute("""
            SELECT curso, semestre, nota, creditos
            FROM matriculas
            WHERE estudiante_id = %s
        """, (est[0],))
        matriculas = pg_cursor.fetchall()
        
        doc = {
            'id': est[0],
            'nombre': est[1],
            'apellido': est[2],
            'email': est[3],
            'edad': est[4],
            'carrera': est[5],
            'año_ingreso': est[6],
            'promedio': float(est[7]),
            'universidad': {
                'nombre': est[8],
                'ciudad': est[9],
                'pais': {
                    'nombre': est[10],
                    'codigo': est[11]
                }
            },
            'pais_origen': {
                'nombre': est[12],
                'codigo': est[13]
            },
            'matriculas': [
                {
                    'curso': m[0],
                    'semestre': m[1],
                    'nota': float(m[2]),
                    'creditos': m[3]
                } for m in matriculas
            ]
        }
        documentos.append(doc)
        
        if len(documentos) % 100 == 0:
            print(f"  {len(documentos)} documentos preparados...")
    
    # Insertar en MongoDB
    print("Insertando en MongoDB...")
    db.estudiantes.insert_many(documentos)
    
    # Crear índices
    print("Creando índices...")
    db.estudiantes.create_index([('nombre', 1), ('apellido', 1)])
    db.estudiantes.create_index('email')
    
    count = db.estudiantes.count_documents({})
    print(f"✓ {count} estudiantes en MongoDB")
    
    pg_cursor.close()
    pg_conn.close()
    client.close()
    return True

if __name__ == "__main__":
    print("=" * 70)
    print("CONFIGURACIÓN RÁPIDA DE BASES DE DATOS")
    print("=" * 70)
    print()
    
    try:
        setup_postgresql()
        setup_mongodb()
        
        print("\n" + "=" * 70)
        print("✅ CONFIGURACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 70)
        print("\nAhora puedes ejecutar: streamlit run app.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

