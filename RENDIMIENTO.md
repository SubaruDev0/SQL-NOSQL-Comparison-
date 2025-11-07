# 📊 Análisis: SQL vs NoSQL

## ⚖️ Trade-off Principal: Precisión vs Velocidad

### 📘 SQL (PostgreSQL)
- ✅ **100% preciso**: Encuentra todos los registros
- ✅ **Consistencia garantizada**: Integridad referencial con JOINs
- ❌ **Más lento**: ~0.0025s por búsqueda con 4 tablas relacionadas

### 📗 NoSQL (MongoDB)  
- ✅ **2-3x más rápido**: ~0.0015s por búsqueda (sin JOINs)
- ✅ **Escalabilidad**: Mejor rendimiento con volúmenes grandes
- ⚠️ **~94% precisión**: Puede fallar con caracteres especiales o regex complejas

## 🔍 ¿Por qué NoSQL encuentra menos registros?

**Problema**: MongoDB con regex case-insensitive puede fallar cuando:
- Nombres tienen caracteres especiales (`María`, `José`)
- Espacios extras o inconsistencias en los datos
- El regex no escapa correctamente metacaracteres

**SQL** usa `ILIKE` que maneja mejor estos casos.

## 📊 Resultados Típicos (1000 búsquedas)

| Base de Datos | Encontrados | Tiempo | Precisión |
|---------------|-------------|--------|-----------|
| PostgreSQL | 1000/1000 | ~2.5s | 100% |
| MongoDB | ~940/1000 | ~1.5s | ~94% |

**Conclusión**: NoSQL es más rápido pero SQL es más confiable para búsquedas complejas.

