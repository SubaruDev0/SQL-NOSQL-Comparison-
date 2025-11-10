#!/usr/bin/env python3
"""
Herramienta mínima para inspeccionar MongoDB cuando `mongosh` no está disponible.
Muestra:
- Lista de bases de datos (lista de nombres)
- Conteo de colecciones y documentos en `universidad_db`
- Un documento de ejemplo de `estudiantes`

Uso:
    python mongo_inspect.py

Opciones (flags):
    --dbs       : lista las bases de datos
    --count     : muestra conteos de colecciones y documentos en `universidad_db`
    --sample    : muestra un documento de ejemplo de `estudiantes`

Si no pasas flags mostrará todo.
"""
import sys
from pymongo import MongoClient


def main():
    args = set(sys.argv[1:])
    client = MongoClient('localhost', 27017)

    def list_dbs():
        try:
            dbs = client.list_database_names()
            print("Bases de datos encontradas:")
            for d in dbs:
                print(f"  - {d}")
        except Exception as e:
            print(f"Error listando bases: {e}")

    def inspect_universidad():
        try:
            db = client['universidad_db']
            cols = db.list_collection_names()
            print(f"\nColecciones en 'universidad_db': {len(cols)}")
            for c in cols:
                print(f"  - {c}: {db[c].count_documents({})} documentos")
        except Exception as e:
            print(f"Error inspeccionando 'universidad_db': {e}")

    def sample_student():
        try:
            db = client['universidad_db']
            doc = db.estudiantes.find_one()
            if not doc:
                print("No se encontraron documentos en 'estudiantes'.")
                return
            print("\nDocumento de ejemplo (estudiantes):")
            # Mostrar campos relevantes
            keys = ['id', 'nombre', 'apellido', 'email', 'edad', 'carrera', 'promedio']
            for k in keys:
                if k in doc:
                    print(f"  {k}: {doc[k]}")
            # Si existe universidad mostrar su nombre
            if 'universidad' in doc and isinstance(doc['universidad'], dict):
                print(f"  universidad.nombre: {doc['universidad'].get('nombre')}")
        except Exception as e:
            print(f"Error leyendo documento: {e}")

    if not args or '--dbs' in args:
        list_dbs()
    if not args or '--count' in args:
        inspect_universidad()
    if not args or '--sample' in args:
        sample_student()


if __name__ == '__main__':
    main()

