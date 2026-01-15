# 🔍 SQL vs NoSQL - Comparación de Rendimiento

> **🌐 Demo en línea:** https://subarudev0-sql-nosql-comparison--app-1qvvcq.streamlit.app/
> 
> ⚠️ **Nota:** En la versión desplegada, PostgreSQL no está disponible (Streamlit Cloud no soporta bases de datos locales). MongoDB funciona correctamente via MongoDB Atlas. Para ver la comparación completa con ambas bases de datos, ejecuta el proyecto localmente siguiendo las instrucciones abajo.

Aplicación web que demuestra las diferencias de velocidad entre PostgreSQL (SQL) y MongoDB (NoSQL) al buscar datos en bases de datos extensas.

## 📋 ¿Qué hace este proyecto?

Compara el tiempo de búsqueda entre:
- **SQL (PostgreSQL)**: Datos en 4 tablas relacionadas que requieren JOINs
- **NoSQL (MongoDB)**: Datos en documentos únicos sin relaciones

**Resultado esperado**: NoSQL es 2-10x más rápido para este tipo de consultas.

---

## 🚀 Guía Paso a Paso (Para Configurar en Otro PC)

### Paso 1: Instalar Requisitos

**Python 3.8+** (verifica con `python3 --version`)

**PostgreSQL:**
```bash
# Ubuntu/Debian/Linux Mint
sudo apt update
sudo apt install postgresql postgresql-contrib

# Iniciar servicio
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Configurar contraseña (usa 'postgres' por defecto)
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"
```

**MongoDB:**
```bash
# Instalar MongoDB 7.0 desde tarball (compatible con Ubuntu 24.04)
cd /tmp
wget https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-ubuntu2204-7.0.14.tgz
tar -xzf mongodb-linux-x86_64-ubuntu2204-7.0.14.tgz

# Mover binarios
sudo mkdir -p /opt/mongodb
sudo cp -r mongodb-linux-x86_64-*/bin/* /opt/mongodb/

# Crear directorios de datos
sudo mkdir -p /var/lib/mongodb
sudo mkdir -p /var/log/mongodb

# Crear usuario
sudo useradd -r -s /bin/false mongodb
sudo chown -R mongodb:mongodb /var/lib/mongodb
sudo chown -R mongodb:mongodb /var/log/mongodb

# Crear archivo de configuración
sudo tee /etc/mongod.conf > /dev/null <<EOF
storage:
  dbPath: /var/lib/mongodb

systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log

net:
  port: 27017
  bindIp: 127.0.0.1
EOF

# Crear servicio systemd (versión mejorada sin --fork para evitar problemas de PID)
sudo tee /etc/systemd/system/mongod.service > /dev/null <<EOF
[Unit]
Description=MongoDB Database Server
After=network.target

[Service]
# Usar Type=simple y NO usar --fork: systemd gestiona el proceso directamente.
Type=simple
User=mongodb
Group=mongodb
ExecStart=/opt/mongodb/mongod --config /etc/mongod.conf
Restart=on-failure
# Opcional: limitar memoria, añadir watchdog, etc.

[Install]
WantedBy=multi-user.target
EOF

# Iniciar MongoDB
sudo ln -sf /opt/mongodb/mongod /usr/local/bin/mongod
sudo systemctl daemon-reload
sudo systemctl enable mongod
sudo systemctl start mongod
```

---

### Paso 2: Clonar/Copiar el Proyecto

```bash
# Si usas Git
git clone <tu-repositorio>
cd SqlNosql

# O simplemente copia la carpeta del proyecto
```

---

### Paso 3: Instalar Dependencias de Python

```bash
# Crear entorno virtual (opcional pero recomendado)
python3 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

---

### Paso 4: Generar Datos de Prueba

```bash
python generate_data.py
```

Esto genera:
- 10,000 estudiantes
- 100 universidades  
- 50 países
- ~55,000 matrículas
- Archivos: `data_sql.sql` (8.8 MB) y `data_nosql.json` (12 MB)

**Nota**: Para generar más datos, edita `NUM_ESTUDIANTES = 10000` en `generate_data.py`

---

### Paso 5: Configurar Credenciales

**Edita `setup_databases_fixed.py` línea 11-16:**
```python
PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',  # ⚠️ Cambia si usaste otra contraseña
    'database': 'postgres'
}
```

**Edita `app.py` línea 18-23:**
```python
PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',  # ⚠️ Cambia si usaste otra contraseña
    'database': 'universidad_db'
}
```

---

### Paso 6: Cargar Datos en las Bases de Datos

```bash
python setup_databases_fixed.py
```

Este script:
- ✅ Crea la base de datos `universidad_db` en PostgreSQL
- ✅ Carga 4 tablas: países, universidades, estudiantes, matrículas
- ✅ Crea índices optimizados en PostgreSQL
- ✅ Carga documentos en MongoDB
- ✅ Crea índices en MongoDB

Verás: "✓ ¡Todas las bases de datos están listas!"

---

### Paso 7: Ejecutar la Aplicación

```bash
streamlit run app.py
```

La app se abrirá en: **http://localhost:8501**

---

## 📖 Cómo Usar la Demo

### Interfaz:
- **Slider**: Ajusta cuántos estudiantes buscar (1-20)
- **Multiselect**: Selecciona los estudiantes específicos
- **Columna Izquierda**: PostgreSQL (SQL con JOINs)
- **Columna Derecha**: MongoDB (NoSQL sin JOINs)

### Pasos:
1. **Ajusta el slider** para elegir cantidad (recomendado: 5-10)
2. **Selecciona estudiantes** del multiselect
3. Haz clic en "🔎 Buscar TODOS" en ambos lados
4. **Compara los tiempos TOTALES** - La diferencia es mucho más evidente con múltiples búsquedas
5. NoSQL será 2-10x más rápido dependiendo de la cantidad ⚡

### 💡 Tip para la presentación:
**Busca 10 estudiantes** para que la diferencia de tiempo sea muy evidente:
- SQL: ~0.080 segundos (con 30-40 JOINs totales)
- NoSQL: ~0.005 segundos (sin JOINs)
- **Diferencia visual: 16x más rápido**

### Estudiantes de ejemplo:
- Jesusa Grifeo
- Carlos King
- Aaron Cortina
- Laura Schomber
- Gloria Traversa
- Rocco Bodin
- William Portero
- Luigi Conti
- Kathrin Rizzoli
- Alexandria Garcia

---

## 🔧 Solución de Problemas

### PostgreSQL no conecta:
```bash
sudo systemctl status postgresql
sudo systemctl start postgresql
```

### MongoDB no conecta:
```bash
sudo systemctl status mongod
sudo systemctl start mongod

# Ver logs
sudo tail -f /var/log/mongodb/mongod.log
```

### Error "relation estudiantes does not exist":
```bash
# Recargar las bases de datos
python setup_databases_fixed.py
```

### Error de autenticación PostgreSQL:
```bash
# Editar pg_hba.conf
sudo nano /etc/postgresql/*/main/pg_hba.conf

# Cambiar líneas 'peer' por 'md5'
# Reiniciar
sudo systemctl restart postgresql
```

---

## 📁 Estructura del Proyecto

```
SqlNosql/
├── app.py                      # Aplicación Streamlit
├── generate_data.py            # Generador de datos
├── setup_databases_fixed.py    # Configurador de BD
├── requirements.txt            # Dependencias Python
├── data_sql.sql               # Datos SQL (generado)
├── data_nosql.json            # Datos NoSQL (generado)
├── README.md                  # Esta guía
└── RESUMEN_PROYECTO.md        # Documentación adicional
```

---

## 💡 Para la Presentación

### Mensaje Clave:
- **SQL**: Múltiples tablas con JOINs → Más lento pero sin duplicación
- **NoSQL**: Todo en un documento → Más rápido pero con duplicación

### Cuándo usar cada uno:
- **SQL**: Bancos, transacciones críticas, integridad de datos
- **NoSQL**: Redes sociales, alto tráfico, escalabilidad horizontal

### Demo en vivo:
1. Buscar el mismo estudiante en ambos lados
2. Señalar la diferencia de tiempo
3. Explicar que NoSQL evita JOINs
4. Mencionar trade-offs (duplicación vs velocidad)

---

## 📊 Datos Técnicos

**PostgreSQL (Normalizado):**
- 4 tablas: `paises`, `universidades`, `estudiantes`, `matriculas`
- 3-4 JOINs por consulta
- ~65,000 registros totales

**MongoDB (Desnormalizado):**
- 1 colección: `estudiantes`
- Sin JOINs
- 10,000 documentos completos

---
