# Spec 43: Corrección de RLS para el Registro Biométrico en Supabase

## 1. Diagnóstico del Problema

Tras analizar los registros en la base de datos de Supabase y verificar el comportamiento del cliente de la Web App biométrica, identificamos lo siguiente:

1. **Carga de Imágenes Exitosa**: Las fotos de las manos de los consultantes se suben correctamente al Storage de Supabase en el bucket `biometria_test` bajo carpetas asociadas al ID de registro único (ej. `cf192a34-4f12-41ff-8764-a79108ab0c00`).
2. **Actualización Bloqueada**: Al finalizar la subida de imágenes, la Web App ejecuta un `UPDATE` en la tabla `public.evaluaciones_completas` para establecer `fotos_completadas = true`. Esta consulta devuelve un resultado vacío `[]` con código HTTP 200, lo cual es el comportamiento característico de **Row-Level Security (RLS)** en Supabase cuando una operación de `UPDATE` carece de políticas que la autoricen.
3. **Trigger Inactivo**: Como el `UPDATE` es bloqueado por las políticas de seguridad de Supabase y no modifica la fila, la columna `fotos_completadas` permanece en `false`, impidiendo que el trigger `tr_evaluaciones_completas_update` detecte el cambio y dispare el webhook hacia la VPS.

---

## 2. Solución Propuesta

Para permitir que la Web App biométrica (que interactúa como un usuario anónimo a través de la clave pública API) actualice el registro biométrico una vez subidas las fotos, debemos proveer una política RLS que autorice operaciones `UPDATE` a usuarios del rol `anon`.

### Sentencia SQL para Supabase Editor:

```sql
-- 1. Crear una política de RLS que permita UPDATES a usuarios anónimos en evaluaciones_completas
DROP POLICY IF EXISTS "Permitir update a usuarios anónimos" ON public.evaluaciones_completas;

CREATE POLICY "Permitir update a usuarios anónimos" 
ON public.evaluaciones_completas 
FOR UPDATE 
TO anon 
USING (true) 
WITH CHECK (true);
```

---

## 3. Plan de Acción

1. **Paso 1:** Solicitar al usuario que ejecute la sentencia SQL anterior en el editor SQL de Supabase.
2. **Paso 2:** Realizar una prueba de actualización con la clave pública de Supabase desde la consola local para verificar que la fila `cf192a34-4f12-41ff-8764-a79108ab0c00` (o similar) se actualice exitosamente a `fotos_completadas: true` y que esto active el trigger de confirmación del webhook hacia la VPS.
