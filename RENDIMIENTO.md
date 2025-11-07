mira # 📊 Análisis: SQL vs NoSQL

## ⚖️ Trade-off Principal: Precisión vs Velocidad

### 📘 SQL (PostgreSQL)
- ✅ **100% preciso**: Encuentra todos los registros, incluso duplicados
- ✅ **Consistencia garantizada**: Integridad referencial con JOINs
- ❌ **Más lento**: ~0.0025s por búsqueda con 4 tablas relacionadas

### 📗 NoSQL (MongoDB)  
- ✅ **2-3x más rápido**: ~0.0015s por búsqueda (sin JOINs)
- ✅ **Escalabilidad**: Mejor rendimiento con volúmenes grandes
- ⚠️ **~94% precisión**: Solo retorna el primer match con `find_one()`

## 🔍 ¿Por qué NoSQL encuentra menos registros?

**El verdadero problema**: MongoDB usa `find_one()` que solo devuelve **el primer documento** que coincide.

**Ejemplo real:**
- Si hay 3 estudiantes llamados "Juan Pérez" (IDs diferentes)
- **PostgreSQL**: Devuelve los 3 (cada uno en su búsqueda)
- **MongoDB**: Solo devuelve el primero, ignora los otros 2

**Resultado:** Si buscas 1000 estudiantes y algunos nombres están duplicados, MongoDB encontrará ~940 porque solo retorna 1 por cada nombre duplicado.

## 📊 Resultados Típicos (1000 búsquedas)

| Base de Datos | Encontrados | Tiempo | Por qué |
|---------------|-------------|--------|---------|
| PostgreSQL | 1000/1000 | ~2.5s | Cada búsqueda es independiente |
| MongoDB | ~940/1000 | ~1.5s | `find_one()` ignora duplicados |

**Conclusión**: NoSQL es más rápido pero SQL maneja mejor duplicados en búsquedas múltiples.

