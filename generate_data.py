"""
Script para generar datos masivos para demostración SQL vs NoSQL
"""
import random
from faker import Faker
import json

fake = Faker(['es_ES', 'en_US', 'fr_FR', 'de_DE', 'it_IT'])

# Configuración - OPTIMIZADO para demostrar diferencia SQL vs NoSQL
# 25k estudiantes son suficientes para ver la diferencia de rendimiento
NUM_ESTUDIANTES = 25000  
NUM_UNIVERSIDADES = 150
NUM_PAISES = 80
NUM_DEPARTAMENTOS = 40
NUM_PROFESORES = 1500
NUM_CURSOS_CATALOGO = 150

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

def generate_departments():
    """Genera lista de departamentos académicos"""
    dept_names = ['Ingeniería', 'Ciencias', 'Humanidades', 'Medicina', 'Derecho',
                  'Economía', 'Arquitectura', 'Artes', 'Comunicación', 'Educación']
    departments = []
    for i in range(NUM_DEPARTAMENTOS):
        departments.append({
            'id': i + 1,
            'nombre': f"Departamento de {random.choice(dept_names)} {i+1}",
            'presupuesto': random.randint(100000, 5000000)
        })
    return departments

def generate_professors(departments):
    """Genera lista de profesores"""
    professors = []
    for i in range(NUM_PROFESORES):
        professors.append({
            'id': i + 1,
            'nombre': fake.first_name(),
            'apellido': fake.last_name(),
            'email': fake.email(),
            'departamento_id': random.choice(departments)['id'],
            'años_experiencia': random.randint(1, 35)
        })
    return professors

def generate_course_catalog(departments, professors):
    """Genera catálogo de cursos disponibles"""
    cursos_base = ['Matemáticas', 'Física', 'Química', 'Programación', 'Cálculo',
                   'Álgebra', 'Base de Datos', 'Redes', 'Algoritmos', 'Historia',
                   'Literatura', 'Biología', 'Estadística', 'Economía', 'Filosofía']
    
    courses = []
    for i in range(NUM_CURSOS_CATALOGO):
        courses.append({
            'id': i + 1,
            'codigo': f"CURSO{i+1:04d}",
            'nombre': f"{random.choice(cursos_base)} {random.choice(['I', 'II', 'III', 'Avanzado', 'Básico'])}",
            'creditos': random.choice([2, 3, 4, 5]),
            'departamento_id': random.choice(departments)['id'],
            'profesor_id': random.choice(professors)['id']
        })
    return courses

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

def generate_enrollment(students, courses):
    """Genera matrículas/cursos - ahora vinculadas al catálogo"""
    enrollments = []
    
    enrollment_id = 1
    for student in students:
        # Cada estudiante tiene entre 4 y 10 cursos del catálogo
        num_cursos = random.randint(4, 10)
        cursos_seleccionados = random.sample(courses, min(num_cursos, len(courses)))
        
        for curso in cursos_seleccionados:
            enrollments.append({
                'id': enrollment_id,
                'estudiante_id': student['id'],
                'curso_id': curso['id'],  # Ahora referencia al catálogo
                'semestre': random.randint(1, 10),
                'nota': round(random.uniform(2.0, 5.0), 2),
                'año': random.randint(2020, 2024)
            })
            enrollment_id += 1
    
    return enrollments

def escape_sql_string(s):
    """Escapa comillas simples para SQL"""
    return s.replace("'", "''")

def save_sql_data(countries, universities, students, enrollments, departments, professors, courses):
    """Guarda datos en formato SQL - ESTRUCTURA COMPLEJA CON MUCHOS JOINS"""
    with open('data_sql.sql', 'w', encoding='utf-8') as f:
        # Crear tablas
        f.write("""
-- Crear base de datos
CREATE DATABASE IF NOT EXISTS universidad_db;

-- Eliminar tablas existentes
DROP TABLE IF EXISTS matriculas CASCADE;
DROP TABLE IF EXISTS cursos_catalogo CASCADE;
DROP TABLE IF EXISTS profesores CASCADE;
DROP TABLE IF EXISTS departamentos CASCADE;
DROP TABLE IF EXISTS estudiantes CASCADE;
DROP TABLE IF EXISTS universidades CASCADE;
DROP TABLE IF EXISTS paises CASCADE;

-- Tabla de países
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

-- Tabla de departamentos
CREATE TABLE departamentos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    presupuesto INTEGER NOT NULL
);

-- Tabla de profesores
CREATE TABLE profesores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(200) NOT NULL,
    departamento_id INTEGER REFERENCES departamentos(id),
    años_experiencia INTEGER NOT NULL
);

-- Catálogo de cursos
CREATE TABLE cursos_catalogo (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    creditos INTEGER NOT NULL,
    departamento_id INTEGER REFERENCES departamentos(id),
    profesor_id INTEGER REFERENCES profesores(id)
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

-- Tabla de matrículas (vincula estudiantes con cursos del catálogo)
CREATE TABLE matriculas (
    id SERIAL PRIMARY KEY,
    estudiante_id INTEGER REFERENCES estudiantes(id),
    curso_id INTEGER REFERENCES cursos_catalogo(id),
    semestre INTEGER NOT NULL,
    nota DECIMAL(3,2) NOT NULL,
    año INTEGER NOT NULL
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

        f.write("\n-- Insertar departamentos\n")
        for dept in departments:
            nombre = escape_sql_string(dept['nombre'])
            f.write(f"INSERT INTO departamentos (id, nombre, presupuesto) VALUES ({dept['id']}, '{nombre}', {dept['presupuesto']});\n")

        f.write("\n-- Insertar profesores\n")
        for prof in professors:
            nombre = escape_sql_string(prof['nombre'])
            apellido = escape_sql_string(prof['apellido'])
            f.write(f"INSERT INTO profesores (id, nombre, apellido, email, departamento_id, años_experiencia) VALUES ({prof['id']}, '{nombre}', '{apellido}', '{prof['email']}', {prof['departamento_id']}, {prof['años_experiencia']});\n")

        f.write("\n-- Insertar catálogo de cursos\n")
        for curso in courses:
            nombre = escape_sql_string(curso['nombre'])
            f.write(f"INSERT INTO cursos_catalogo (id, codigo, nombre, creditos, departamento_id, profesor_id) VALUES ({curso['id']}, '{curso['codigo']}', '{nombre}', {curso['creditos']}, {curso['departamento_id']}, {curso['profesor_id']});\n")

        f.write("\n-- Insertar estudiantes (en lotes para velocidad)\n")
        batch_size = 1000
        for i in range(0, len(students), batch_size):
            batch = students[i:i+batch_size]
            for student in batch:
                nombre = escape_sql_string(student['nombre'])
                apellido = escape_sql_string(student['apellido'])
                carrera = escape_sql_string(student['carrera'])
                f.write(f"INSERT INTO estudiantes (id, nombre, apellido, email, edad, universidad_id, pais_origen_id, carrera, año_ingreso, promedio) VALUES ({student['id']}, '{nombre}', '{apellido}', '{student['email']}', {student['edad']}, {student['universidad_id']}, {student['pais_origen_id']}, '{carrera}', {student['año_ingreso']}, {student['promedio']});\n")
            if (i + batch_size) % 5000 == 0:
                print(f"  {i + batch_size} estudiantes escritos...")

        f.write("\n-- Insertar matrículas (en lotes para velocidad)\n")
        for i in range(0, len(enrollments), batch_size):
            batch = enrollments[i:i+batch_size]
            for enrollment in batch:
                f.write(f"INSERT INTO matriculas (id, estudiante_id, curso_id, semestre, nota, año) VALUES ({enrollment['id']}, {enrollment['estudiante_id']}, {enrollment['curso_id']}, {enrollment['semestre']}, {enrollment['nota']}, {enrollment['año']});\n")
            if (i + batch_size) % 10000 == 0:
                print(f"  {i + batch_size} matrículas escritas...")

        f.write("\n-- Crear índices para mejorar rendimiento (pero aún así SQL será más lento)\n")
        f.write("CREATE INDEX idx_estudiantes_nombre ON estudiantes(nombre, apellido);\n")
        f.write("CREATE INDEX idx_matriculas_estudiante ON matriculas(estudiante_id);\n")
        f.write("CREATE INDEX idx_matriculas_curso ON matriculas(curso_id);\n")
        f.write("CREATE INDEX idx_profesores_departamento ON profesores(departamento_id);\n")
        f.write("CREATE INDEX idx_cursos_departamento ON cursos_catalogo(departamento_id);\n")

    print(f"✓ Archivo SQL generado: data_sql.sql")


def save_nosql_data(countries, universities, students, enrollments, departments, professors, courses):
    """Guarda datos en formato NoSQL (MongoDB) - TODO EN UN DOCUMENTO"""
    # Crear diccionarios para búsqueda rápida
    countries_dict = {c['id']: c for c in countries}
    universities_dict = {u['id']: u for u in universities}
    departments_dict = {d['id']: d for d in departments}
    professors_dict = {p['id']: p for p in professors}
    courses_dict = {c['id']: c for c in courses}

    # Crear diccionario de matrículas por estudiante
    enrollments_by_student = {}
    for enrollment in enrollments:
        student_id = enrollment['estudiante_id']
        if student_id not in enrollments_by_student:
            enrollments_by_student[student_id] = []
        
        # Obtener información completa del curso
        curso = courses_dict[enrollment['curso_id']]
        profesor = professors_dict[curso['profesor_id']]
        departamento = departments_dict[curso['departamento_id']]
        
        enrollments_by_student[student_id].append({
            'curso_codigo': curso['codigo'],
            'curso_nombre': curso['nombre'],
            'creditos': curso['creditos'],
            'semestre': enrollment['semestre'],
            'nota': enrollment['nota'],
            'año': enrollment['año'],
            'profesor': {
                'nombre': profesor['nombre'],
                'apellido': profesor['apellido'],
                'email': profesor['email'],
                'años_experiencia': profesor['años_experiencia']
            },
            'departamento': {
                'nombre': departamento['nombre'],
                'presupuesto': departamento['presupuesto']
            }
        })

    # Crear documentos completos (TOTALMENTE desnormalizados - TODO en 1 documento)
    print("  Creando documentos NoSQL...")
    nosql_students = []
    for idx, student in enumerate(students):
        if (idx + 1) % 5000 == 0:
            print(f"  {idx + 1} documentos creados...")
        
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

    print("  Escribiendo archivo JSON...")
    with open('data_nosql.json', 'w', encoding='utf-8') as f:
        json.dump(nosql_students, f, ensure_ascii=False)

    print(f"✓ Archivo NoSQL generado: data_nosql.json")

def main():
    print("=" * 70)
    print("GENERANDO DATOS MASIVOS - SQL vs NoSQL")
    print("=" * 70)
    print(f"- {NUM_PAISES} países")
    print(f"- {NUM_UNIVERSIDADES} universidades")
    print(f"- {NUM_DEPARTAMENTOS} departamentos")
    print(f"- {NUM_PROFESORES} profesores")
    print(f"- {NUM_CURSOS_CATALOGO} cursos en catálogo")
    print(f"- {NUM_ESTUDIANTES} estudiantes")
    print("\n⚠️  ESTO PUEDE TOMAR 10-30 MINUTOS...\n")

    countries = generate_countries()
    print("✓ Países generados")

    universities = generate_universities(countries)
    print("✓ Universidades generadas")

    departments = generate_departments()
    print("✓ Departamentos generados")

    professors = generate_professors(departments)
    print("✓ Profesores generados")

    courses = generate_course_catalog(departments, professors)
    print("✓ Catálogo de cursos generado")

    students = generate_students(universities, countries)
    print(f"✓ {len(students)} estudiantes generados")

    enrollments = generate_enrollment(students, courses)
    print(f"✓ {len(enrollments)} matrículas generadas")

    print("\nGuardando archivos (esto puede tardar)...")
    save_sql_data(countries, universities, students, enrollments, departments, professors, courses)
    save_nosql_data(countries, universities, students, enrollments, departments, professors, courses)

    print("\n" + "=" * 70)
    print("¡DATOS GENERADOS EXITOSAMENTE!")
    print("=" * 70)
    total_sql = len(countries) + len(universities) + len(departments) + len(professors) + len(courses) + len(students) + len(enrollments)
    print(f"Total de registros SQL: {total_sql:,}")
    print(f"Total de documentos NoSQL: {len(students):,}")
    print(f"\nSQL necesitará 6-7 JOINs por búsqueda")
    print(f"NoSQL lee 1 documento completo")
    print("=" * 70)

if __name__ == "__main__":
    main()

