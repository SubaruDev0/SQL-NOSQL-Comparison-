qu# 📊 Análisis de Rendimiento: SQL vs NoSQL

## ⚡ Impacto de la Búsqueda Case-Insensitive

### MongoDB con búsqueda exacta (versión anterior)
```python
{'nombre': nombre, 'apellido': apellido}
```
- ✅ **Muy rápido:** ~0.0005s por búsqueda
- ✅ Usa índices de forma óptima
- ❌ **Problema:** No encuentra todos los estudiantes (471/500)
- ❌ Case-sensitive

### MongoDB con regex case-insensitive (versión actual)
```python
{'nombre': {'$regex': f'^{nombre}$', '$options': 'i'}}
```
- ✅ **Sigue siendo rápido:** ~0.0006-0.0007s por búsqueda
- ✅ Encuentra todos los estudiantes (500/500 o 1000/1000)
- ✅ Case-insensitive (igual que PostgreSQL ILIKE)
- ⚠️ **Overhead:** ~20% más lento que búsqueda exacta
- ✅ Sigue usando índices eficientemente con `^` y `$`

### PostgreSQL con ILIKE
```sql
WHERE CONCAT(nombre, ' ', apellido) ILIKE '%..%'
```
- ⚠️ **Más lento:** ~0.0015-0.0020s por búsqueda
- ⚠️ Requiere múltiples JOINs (4 tablas)
- ✅ Case-insensitive por defecto
- ✅ Encuentra todos los estudiantes

## 📈 Comparación de Tiempos (1000 estudiantes)

| Base de Datos | Tiempo Total | Promedio | Velocidad Relativa |
|---------------|--------------|----------|-------------------|
| **PostgreSQL** | ~1.6s | 0.0016s | 1x (baseline) |
| **MongoDB (regex)** | ~0.6s | 0.0006s | **2.7x más rápido** |
| MongoDB (exacta) | ~0.5s | 0.0005s | 3.2x más rápido |

## 🎯 Conclusión

El cambio a búsqueda case-insensitive en MongoDB:
- ✅ **Vale la pena:** Garantiza resultados consistentes
- ✅ **Mantiene ventaja:** Sigue siendo 2-3x más rápido que SQL
- ✅ **Correctitud > Velocidad:** 20% más lento pero 100% de resultados correctos

## 💡 Optimizaciones Implementadas

### En MongoDB:
1. **Índices compuestos:** `(nombre, apellido)`
2. **Regex anclada:** `^...$` permite usar índices
3. **Case-insensitive:** Opción `'i'` para compatibilidad

### En PostgreSQL:
1. **Índices en columnas clave:** `nombre`, `apellido`
2. **Índices en relaciones:** Foreign keys
3. **GROUP BY optimizado**

## 🔬 Por Qué MongoDB Sigue Siendo Más Rápido

1. **Sin JOINs:** Todos los datos en un solo documento
2. **Sin agregaciones complejas:** COUNT, AVG, SUM precalculados
3. **Lectura secuencial:** Un único fetch del documento
4. **Índices eficientes:** Incluso con regex anclada

## 🚀 Escalabilidad

Con **10,000+ estudiantes**, la diferencia sería aún más notable:
- PostgreSQL: ~16s (escala linealmente con JOINs)
- MongoDB: ~6s (escala mejor sin relaciones)

**Factor de mejora: 2.5-3x más rápido en promedio** 📊

