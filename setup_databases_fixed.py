"""
Script mejorado para configurar bases de datos con mejor manejo de errores
"""
import psycopg2
from pymongo import MongoClient
import json
import os

# Configuración PostgreSQL
PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'postgres'
}

# Configuración MongoDB
MONGO_CONFIG = {
    'host': 'localhost',
    'port': 27017,
    'database': 'universidad_db'
}

def setup_postgresql():
    """Configura PostgreSQL usando psycopg2 directamente"""
    print("Configurando PostgreSQL...")

    try:
        # Conectar y crear BD
        conn = psycopg2.connect(**PG_CONFIG)
        conn.autocommit = True
        cursor = conn.cursor()

        # Eliminar y crear BD limpia
        cursor.execute("DROP DATABASE IF EXISTS universidad_db;")
        cursor.execute("CREATE DATABASE universidad_db;")
        print("✓ Base de datos creada")
        cursor.close()
        conn.close()

        # Conectar a la nueva BD
        pg_config = PG_CONFIG.copy()
        pg_config['database'] = 'universidad_db'
        conn = psycopg2.connect(**pg_config)
        conn.autocommit = False
        cursor = conn.cursor()

        # Cargar datos JSON
        print("Cargando datos desde JSON...")
        with open('data_nosql.json', 'r', encoding='utf-8') as f:
            students_data = json.load(f)

        # Crear tablas
        print("Creando tablas...")
        cursor.execute("""
            DROP TABLE IF EXISTS matriculas CASCADE;
            DROP TABLE IF EXISTS estudiantes CASCADE;
            DROP TABLE IF EXISTS universidades CASCADE;
            DROP TABLE IF EXISTS paises CASCADE;
        """)

        cursor.execute("""
            CREATE TABLE paises (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                codigo VARCHAR(3) NOT NULL
            );
        """)

        cursor.execute("""
            CREATE TABLE universidades (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(200) NOT NULL,
                pais_id INTEGER REFERENCES paises(id),
                ciudad VARCHAR(100) NOT NULL
            );
        """)

        cursor.execute("""
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
        """)

        cursor.execute("""
            CREATE TABLE matriculas (
                id SERIAL PRIMARY KEY,
                estudiante_id INTEGER REFERENCES estudiantes(id),
                curso VARCHAR(100) NOT NULL,
                semestre INTEGER NOT NULL,
                nota DECIMAL(3,2) NOT NULL,
                creditos INTEGER NOT NULL
            );
        """)

        conn.commit()
        print("✓ Tablas creadas")

        # Extraer datos únicos
        print("Extrayendo datos...")
        paises_dict = {}
        universidades_dict = {}

        for student in students_data:
            pais_origen = student['pais_origen']
            pais_uni = student['universidad']['pais']
            universidad = student['universidad']

            # Agregar países
            if pais_origen['id'] not in paises_dict:
                paises_dict[pais_origen['id']] = pais_origen
            if pais_uni['id'] not in paises_dict:
                paises_dict[pais_uni['id']] = pais_uni

            # Agregar universidades
            if universidad['id'] not in universidades_dict:
                universidades_dict[universidad['id']] = universidad

        # Insertar países
        print(f"Insertando {len(paises_dict)} países...")
        for pais in paises_dict.values():
            cursor.execute(
                "INSERT INTO paises (id, nombre, codigo) VALUES (%s, %s, %s)",
                (pais['id'], pais['nombre'], pais['codigo'])
            )
        conn.commit()

        # Insertar universidades
        print(f"Insertando {len(universidades_dict)} universidades...")
        for uni in universidades_dict.values():
            cursor.execute(
                "INSERT INTO universidades (id, nombre, pais_id, ciudad) VALUES (%s, %s, %s, %s)",
                (uni['id'], uni['nombre'], uni['pais']['id'], uni['ciudad'])
            )
        conn.commit()

        # Insertar estudiantes
        print(f"Insertando {len(students_data)} estudiantes...")
        for student in students_data:
            cursor.execute(
                """INSERT INTO estudiantes (id, nombre, apellido, email, edad, universidad_id, 
                   pais_origen_id, carrera, año_ingreso, promedio) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (student['id'], student['nombre'], student['apellido'], student['email'],
                 student['edad'], student['universidad']['id'], student['pais_origen']['id'],
                 student['carrera'], student['año_ingreso'], student['promedio'])
            )

        if len(students_data) % 1000 == 0:
            conn.commit()

        conn.commit()

        # Insertar matrículas
        print("Insertando matrículas...")
        matricula_id = 1
        for student in students_data:
            for matricula in student['matriculas']:
                cursor.execute(
                    """INSERT INTO matriculas (id, estudiante_id, curso, semestre, nota, creditos)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (matricula_id, student['id'], matricula['curso'], matricula['semestre'],
                     matricula['nota'], matricula['creditos'])
                )
                matricula_id += 1

                if matricula_id % 5000 == 0:
                    conn.commit()
                    print(f"  {matricula_id} matrículas insertadas...")

        conn.commit()

        # Crear índices
        print("Creando índices...")
        cursor.execute("CREATE INDEX idx_estudiantes_nombre ON estudiantes(nombre, apellido);")
        cursor.execute("CREATE INDEX idx_matriculas_estudiante ON matriculas(estudiante_id);")
        conn.commit()

        # Verificar
        cursor.execute("SELECT COUNT(*) FROM estudiantes;")
        count = cursor.fetchone()[0]
        print(f"✓ {count} estudiantes cargados en PostgreSQL")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def setup_mongodb():
    """Configura MongoDB"""
    print("\nConfigurando MongoDB...")

    try:
        client = MongoClient(MONGO_CONFIG['host'], MONGO_CONFIG['port'], serverSelectionTimeoutMS=5000)
        # Verificar conexión
        client.server_info()

        db = client[MONGO_CONFIG['database']]
        db.estudiantes.drop()

        with open('data_nosql.json', 'r', encoding='utf-8') as f:
            students = json.load(f)

        print(f"Insertando {len(students)} documentos...")
        db.estudiantes.insert_many(students)

        print("Creando índices...")
        db.estudiantes.create_index([("nombre", 1), ("apellido", 1)])
        db.estudiantes.create_index([("email", 1)])

        count = db.estudiantes.count_documents({})
        print(f"✓ {count} estudiantes cargados en MongoDB")

        client.close()
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        print("  Asegúrate de que MongoDB esté corriendo")
        return False

def main():
    print("="*60)
    print("CONFIGURACIÓN DE BASES DE DATOS")
    print("="*60)
    print()

    if not os.path.exists('data_nosql.json'):
        print("✗ Archivo data_nosql.json no encontrado")
        print("  Ejecuta primero: python generate_data.py")
        return

    pg_ok = setup_postgresql()
    mongo_ok = setup_mongodb()

    print()
    print("="*60)
    if pg_ok and mongo_ok:
        print("✓ ¡Todas las bases de datos están listas!")
        print()
        print("Ahora puedes ejecutar la aplicación:")
        print("  streamlit run app.py")
    elif pg_ok:
        print("⚠ PostgreSQL OK, pero MongoDB falló")
        print("  Puedes probar solo con PostgreSQL modificando app.py")
    elif mongo_ok:
        print("⚠ MongoDB OK, pero PostgreSQL falló")
    else:
        print("✗ Error configurando las bases de datos")
    print("="*60)

if __name__ == "__main__":
    main()

