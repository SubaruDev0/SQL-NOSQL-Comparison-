"""
Script para generar datos masivos para demostración SQL vs NoSQL
"""
import random
from faker import Faker
import json

fake = Faker(['es_ES', 'en_US', 'fr_FR', 'de_DE', 'it_IT'])

# Configuración
NUM_ESTUDIANTES = 10000  # Puedes aumentar esto para más datos
NUM_UNIVERSIDADES = 100
NUM_PAISES = 50

def generate_countries():
    """Genera lista de países"""
    countries = []
    for i in range(NUM_PAISES):
        countries.append({
            'id': i + 1,
            'nombre': fake.country(),
            'codigo': fake.country_code()
        })
    return countries

def generate_universities(countries):
    """Genera lista de universidades"""
    universities = []
    for i in range(NUM_UNIVERSIDADES):
        universities.append({
            'id': i + 1,
            'nombre': f"Universidad {fake.company()}",
            'pais_id': random.choice(countries)['id'],
            'ciudad': fake.city()
        })
    return universities

def generate_students(universities, countries):
    """Genera lista de estudiantes"""
    students = []
    carreras = ['Ingeniería', 'Medicina', 'Derecho', 'Psicología', 'Arquitectura',
                'Economía', 'Biología', 'Física', 'Química', 'Matemáticas']

    for i in range(NUM_ESTUDIANTES):
        nombre = fake.first_name()
        apellido = fake.last_name()
        students.append({
            'id': i + 1,
            'nombre': nombre,
            'apellido': apellido,
            'email': f"{nombre.lower()}.{apellido.lower()}@{fake.domain_name()}",
            'edad': random.randint(18, 35),
            'universidad_id': random.choice(universities)['id'],
            'pais_origen_id': random.choice(countries)['id'],
            'carrera': random.choice(carreras),
            'año_ingreso': random.randint(2015, 2024),
            'promedio': round(random.uniform(2.5, 5.0), 2)
        })
    return students

def generate_enrollment(students):
    """Genera matrículas/cursos"""
    enrollments = []
    cursos = ['Matemáticas I', 'Física I', 'Química I', 'Programación I',
              'Cálculo', 'Álgebra', 'Base de Datos', 'Redes', 'Algoritmos']

    enrollment_id = 1
    for student in students:
        # Cada estudiante tiene entre 3 y 8 cursos
        num_cursos = random.randint(3, 8)
        cursos_seleccionados = random.sample(cursos, num_cursos)

        for curso in cursos_seleccionados:
            enrollments.append({
                'id': enrollment_id,
                'estudiante_id': student['id'],
                'curso': curso,
                'semestre': random.randint(1, 10),
                'nota': round(random.uniform(2.0, 5.0), 2),
                'creditos': random.choice([2, 3, 4, 5])
            })
            enrollment_id += 1

    return enrollments

def escape_sql_string(s):
    """Escapa comillas simples para SQL"""
    return s.replace("'", "''")

def save_sql_data(countries, universities, students, enrollments):
    """Guarda datos en formato SQL"""
    with open('data_sql.sql', 'w', encoding='utf-8') as f:
        # Crear tablas
        f.write("""
-- Crear base de datos
CREATE DATABASE IF NOT EXISTS universidad_db;

-- Tabla de países
DROP TABLE IF EXISTS matriculas CASCADE;
DROP TABLE IF EXISTS estudiantes CASCADE;
DROP TABLE IF EXISTS universidades CASCADE;
DROP TABLE IF EXISTS paises CASCADE;

CREATE TABLE paises (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    codigo VARCHAR(3) NOT NULL
);

-- Tabla de universidades
CREATE TABLE universidades (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    pais_id INTEGER REFERENCES paises(id),
    ciudad VARCHAR(100) NOT NULL
);

-- Tabla de estudiantes
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

-- Tabla de matrículas
CREATE TABLE matriculas (
    id SERIAL PRIMARY KEY,
    estudiante_id INTEGER REFERENCES estudiantes(id),
    curso VARCHAR(100) NOT NULL,
    semestre INTEGER NOT NULL,
    nota DECIMAL(3,2) NOT NULL,
    creditos INTEGER NOT NULL
);

-- Insertar países
""")

        for country in countries:
            nombre = escape_sql_string(country['nombre'])
            f.write(f"INSERT INTO paises (id, nombre, codigo) VALUES ({country['id']}, '{nombre}', '{country['codigo']}');\n")

        f.write("\n-- Insertar universidades\n")
        for uni in universities:
            nombre = escape_sql_string(uni['nombre'])
            ciudad = escape_sql_string(uni['ciudad'])
            f.write(f"INSERT INTO universidades (id, nombre, pais_id, ciudad) VALUES ({uni['id']}, '{nombre}', {uni['pais_id']}, '{ciudad}');\n")

        f.write("\n-- Insertar estudiantes\n")
        for student in students:
            nombre = escape_sql_string(student['nombre'])
            apellido = escape_sql_string(student['apellido'])
            carrera = escape_sql_string(student['carrera'])
            f.write(f"INSERT INTO estudiantes (id, nombre, apellido, email, edad, universidad_id, pais_origen_id, carrera, año_ingreso, promedio) VALUES ({student['id']}, '{nombre}', '{apellido}', '{student['email']}', {student['edad']}, {student['universidad_id']}, {student['pais_origen_id']}, '{carrera}', {student['año_ingreso']}, {student['promedio']});\n")

        f.write("\n-- Insertar matrículas\n")
        for enrollment in enrollments:
            curso = escape_sql_string(enrollment['curso'])
            f.write(f"INSERT INTO matriculas (id, estudiante_id, curso, semestre, nota, creditos) VALUES ({enrollment['id']}, {enrollment['estudiante_id']}, '{curso}', {enrollment['semestre']}, {enrollment['nota']}, {enrollment['creditos']});\n")

        f.write("\n-- Crear índices para mejorar rendimiento\n")
        f.write("CREATE INDEX idx_estudiantes_nombre ON estudiantes(nombre, apellido);\n")
        f.write("CREATE INDEX idx_matriculas_estudiante ON matriculas(estudiante_id);\n")

    print(f"✓ Archivo SQL generado: data_sql.sql")

def save_nosql_data(countries, universities, students, enrollments):
    """Guarda datos en formato NoSQL (MongoDB)"""
    # Crear diccionario de países y universidades para búsqueda rápida
    countries_dict = {c['id']: c for c in countries}
    universities_dict = {u['id']: u for u in universities}

    # Crear diccionario de matrículas por estudiante
    enrollments_by_student = {}
    for enrollment in enrollments:
        student_id = enrollment['estudiante_id']
        if student_id not in enrollments_by_student:
            enrollments_by_student[student_id] = []
        enrollments_by_student[student_id].append({
            'curso': enrollment['curso'],
            'semestre': enrollment['semestre'],
            'nota': enrollment['nota'],
            'creditos': enrollment['creditos']
        })

    # Crear documentos completos (desnormalizados)
    nosql_students = []
    for student in students:
        uni = universities_dict[student['universidad_id']]
        pais_uni = countries_dict[uni['pais_id']]
        pais_origen = countries_dict[student['pais_origen_id']]

        nosql_students.append({
            'id': student['id'],
            'nombre': student['nombre'],
            'apellido': student['apellido'],
            'email': student['email'],
            'edad': student['edad'],
            'carrera': student['carrera'],
            'año_ingreso': student['año_ingreso'],
            'promedio': student['promedio'],
            'universidad': {
                'id': uni['id'],
                'nombre': uni['nombre'],
                'ciudad': uni['ciudad'],
                'pais': {
                    'id': pais_uni['id'],
                    'nombre': pais_uni['nombre'],
                    'codigo': pais_uni['codigo']
                }
            },
            'pais_origen': {
                'id': pais_origen['id'],
                'nombre': pais_origen['nombre'],
                'codigo': pais_origen['codigo']
            },
            'matriculas': enrollments_by_student.get(student['id'], [])
        })

    with open('data_nosql.json', 'w', encoding='utf-8') as f:
        json.dump(nosql_students, f, ensure_ascii=False, indent=2)

    print(f"✓ Archivo NoSQL generado: data_nosql.json")

def main():
    print("Generando datos...")
    print(f"- {NUM_PAISES} países")
    print(f"- {NUM_UNIVERSIDADES} universidades")
    print(f"- {NUM_ESTUDIANTES} estudiantes")

    countries = generate_countries()
    print("✓ Países generados")

    universities = generate_universities(countries)
    print("✓ Universidades generadas")

    students = generate_students(universities, countries)
    print("✓ Estudiantes generados")

    enrollments = generate_enrollment(students)
    print(f"✓ {len(enrollments)} matrículas generadas")

    save_sql_data(countries, universities, students, enrollments)
    save_nosql_data(countries, universities, students, enrollments)

    print("\n¡Datos generados exitosamente!")
    print(f"Total de registros SQL: {len(countries) + len(universities) + len(students) + len(enrollments)}")
    print(f"Total de documentos NoSQL: {len(students)}")

if __name__ == "__main__":
    main()

