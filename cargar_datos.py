#!/usr/bin/env python3
"""
Script simplificado para cargar datos en ambas bases de datos
"""
import psycopg2
from pymongo import MongoClient
from faker import Faker
import random
import sys

fake = Faker(['es_ES'])

print("="*70)
print("CARGANDO DATOS EN BASES DE DATOS")
print("="*70)

# Configuración
NUM_PAISES = 30
NUM_UNIVERSIDADES = 50
NUM_ESTUDIANTES = 500  # Reducido para ser más rápido
CURSOS = ['Matemáticas I', 'Física I', 'Química', 'Programación', 'Estadística', 
          'Literatura', 'Historia', 'Biología', 'Inglés', 'Filosofía']
CARRERAS = ['Ingeniería Informática', 'Medicina', 'Derecho', 'Economía', 
            'Arquitectura', 'Psicología', 'Biología', 'Matemáticas']

print(f"\nConfiguración: {NUM_ESTUDIANTES} estudiantes")

# ============= POSTGRESQL =============
print("\n📘 Configurando PostgreSQL...")
try:
    # Conectar como superusuario
    conn = psycopg2.connect(host='localhost', port=5432, user='postgres', 
                           password='postgres', database='postgres')
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Recrear BD
    print("  - Eliminando BD anterior...")
    cursor.execute("DROP DATABASE IF EXISTS universidad_db;")
    print("  - Creando BD nueva...")
    cursor.execute("CREATE DATABASE universidad_db;")
    cursor.close()
    conn.close()
    
    # Conectar a la nueva BD
    conn = psycopg2.connect(host='localhost', port=5432, user='postgres',
                           password='postgres', database='universidad_db')
    cursor = conn.cursor()
    
    # Crear tablas
    print("  - Creando tablas...")
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
    
    # Insertar países
    print("  - Insertando países...")
    paises_ids = []
    for _ in range(NUM_PAISES):
        cursor.execute(
            "INSERT INTO paises (nombre, codigo) VALUES (%s, %s) RETURNING id",
            (fake.country(), fake.country_code())
        )
        paises_ids.append(cursor.fetchone()[0])
    conn.commit()
    
    # Insertar universidades
    print("  - Insertando universidades...")
    universidades_ids = []
    for _ in range(NUM_UNIVERSIDADES):
        cursor.execute(
            "INSERT INTO universidades (nombre, pais_id, ciudad) VALUES (%s, %s, %s) RETURNING id",
            (f"Universidad {fake.company()}", random.choice(paises_ids), fake.city())
        )
        universidades_ids.append(cursor.fetchone()[0])
    conn.commit()
    
    # Insertar estudiantes
    print(f"  - Insertando {NUM_ESTUDIANTES} estudiantes...")
    estudiantes = []
    for i in range(NUM_ESTUDIANTES):
        nombre = fake.first_name()
        apellido = fake.last_name()
        cursor.execute(
            """INSERT INTO estudiantes (nombre, apellido, email, edad, universidad_id, 
               pais_origen_id, carrera, año_ingreso, promedio) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (nombre, apellido, fake.email(), random.randint(18, 30),
             random.choice(universidades_ids), random.choice(paises_ids),
             random.choice(CARRERAS), random.randint(2018, 2024),
             round(random.uniform(6.0, 9.99), 2))
        )
        est_id = cursor.fetchone()[0]
        estudiantes.append({'id': est_id, 'nombre': nombre, 'apellido': apellido})
        
        # Matrículas
        num_cursos = random.randint(4, 8)
        for _ in range(num_cursos):
            cursor.execute(
                """INSERT INTO matriculas (estudiante_id, curso, semestre, nota, creditos)
                   VALUES (%s, %s, %s, %s, %s)""",
                (est_id, random.choice(CURSOS), f"2024-{random.randint(1,2)}",
                 round(random.uniform(6.0, 9.99), 2), random.choice([3, 4, 5]))
            )
        
        if (i + 1) % 100 == 0:
            conn.commit()
            print(f"    {i + 1} estudiantes insertados...")
    
    conn.commit()
    
    # Crear índices
    print("  - Creando índices...")
    cursor.execute("CREATE INDEX idx_estudiantes_nombre ON estudiantes(nombre, apellido);")
    cursor.execute("CREATE INDEX idx_matriculas_estudiante ON matriculas(estudiante_id);")
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM estudiantes")
    count = cursor.fetchone()[0]
    print(f"  ✅ {count} estudiantes en PostgreSQL")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"  ❌ Error en PostgreSQL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============= MONGODB =============
print("\n📗 Configurando MongoDB...")
try:
    # Conectar a PostgreSQL para copiar datos
    pg_conn = psycopg2.connect(host='localhost', port=5432, user='postgres',
                               password='postgres', database='universidad_db')
    pg_cursor = pg_conn.cursor()
    
    # Conectar a MongoDB
    mongo_client = MongoClient('localhost', 27017)
    db = mongo_client['universidad_db']
    
    # Limpiar colección
    print("  - Limpiando colección anterior...")
    db.estudiantes.drop()
    
    # Obtener todos los estudiantes con datos relacionados
    print("  - Obteniendo datos de PostgreSQL...")
    pg_cursor.execute("""
        SELECT 
            e.id, e.nombre, e.apellido, e.email, e.edad, e.carrera,
            e.año_ingreso, e.promedio,
            u.nombre, u.ciudad,
            p_uni.nombre, p_uni.codigo,
            p_ori.nombre, p_ori.codigo
        FROM estudiantes e
        JOIN universidades u ON e.universidad_id = u.id
        JOIN paises p_uni ON u.pais_id = p_uni.id
        JOIN paises p_ori ON e.pais_origen_id = p_ori.id
    """)
    
    estudiantes = pg_cursor.fetchall()
    
    # Crear documentos para MongoDB
    print(f"  - Creando {len(estudiantes)} documentos...")
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
    
    # Insertar en MongoDB
    print("  - Insertando en MongoDB...")
    db.estudiantes.insert_many(documentos)
    
    # Crear índices
    print("  - Creando índices...")
    db.estudiantes.create_index([('nombre', 1), ('apellido', 1)])
    db.estudiantes.create_index('email')
    
    count = db.estudiantes.count_documents({})
    print(f"  ✅ {count} estudiantes en MongoDB")
    
    pg_cursor.close()
    pg_conn.close()
    mongo_client.close()
    
except Exception as e:
    print(f"  ❌ Error en MongoDB: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*70)
print("✅ ¡DATOS CARGADOS EXITOSAMENTE!")
print("="*70)
print(f"\n  PostgreSQL: {NUM_ESTUDIANTES} estudiantes")
print(f"  MongoDB: {NUM_ESTUDIANTES} estudiantes")
print(f"\n💡 Ahora ejecuta: streamlit run app.py")
print("="*70)

