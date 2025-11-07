# 🚀 Guía Rápida para Desarrollo Local

## Problema Actual

Si ves errores de conexión a las bases de datos localmente, es porque las bases de datos están vacías o no configuradas.

## Solución Rápida (Recomendado)

### Opción 1: Configuración Rápida (1000 estudiantes - ~30 segundos)

```bash
# 1. Asegúrate de tener PostgreSQL y MongoDB corriendo
sudo systemctl start postgresql@16-main
sudo systemctl start mongod

# 2. Activa el entorno virtual
source .venv/bin/activate

# 3. Ejecuta el script rápido
python quick_setup.py
```

### Opción 2: Configuración Completa (25,000 estudiantes - ~5 minutos)

```bash
# 1. Genera los datos
python generate_data.py

# 2. Carga los datos
python setup_databases_fixed.py
```

## Verificar que todo funciona

```bash
# PostgreSQL
psql -U postgres -d universidad_db -c "SELECT COUNT(*) FROM estudiantes;"

# MongoDB
mongosh universidad_db --eval "db.estudiantes.countDocuments()"
```

## Ejecutar la Aplicación

```bash
streamlit run app.py
```

La aplicación se abrirá en `http://localhost:8501`

## Troubleshooting

### PostgreSQL no conecta

```bash
# Verificar estado
sudo systemctl status postgresql@16-main

# Iniciar
sudo systemctl start postgresql@16-main

# Ver logs
sudo journalctl -u postgresql@16-main -n 50
```

### MongoDB no conecta

```bash
# Verificar estado
sudo systemctl status mongod

# Iniciar
sudo systemctl start mongod

# Ver logs
sudo journalctl -u mongod -n 50
```

### Faker no instalado

```bash
pip install faker
```

### Regenerar todo desde cero

```bash
# Borrar bases de datos
psql -U postgres -c "DROP DATABASE IF EXISTS universidad_db;"
mongosh --eval "use universidad_db; db.dropDatabase();"

# Volver a configurar
python quick_setup.py
```

## Demo en Línea

Si no quieres configurar localmente, puedes ver la demo en:
https://subarudev0-sql-nosql-comparison--app-1qvvcq.streamlit.app/

⚠️ **Nota:** La demo en línea solo tiene MongoDB (PostgreSQL no está disponible en Streamlit Cloud).

