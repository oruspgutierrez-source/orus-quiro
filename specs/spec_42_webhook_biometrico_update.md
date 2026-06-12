# Spec 42: Corrección de Webhook de Confirmación Biométrica (Disparo en Update)

## 1. Diagnóstico del Problema
1. La Web App de recolección biométrica (alojada en Vercel) registra los datos iniciales del consultante mediante una sentencia `INSERT` en la tabla `public.evaluaciones_completas`. En este momento inicial, la columna `fotos_completadas` es `false`.
2. Posteriormente, al finalizar la carga de todas las fotografías de las manos, la Web App ejecuta un `UPDATE` en Supabase para cambiar el valor de `fotos_completadas` a `true` (`.update({ fotos_completadas: true })`).
3. El trigger de la base de datos de Supabase (`tr_evaluaciones_completas_insert`) estaba configurado exclusivamente para eventos `AFTER INSERT`. Por lo tanto, cuando ocurre el `UPDATE` final que marca las fotos como completadas, el trigger no se activa y el webhook a la VPS no se envía.

---

## 2. Solución Propuesta

### A. Modificación del Trigger y Función en Supabase
Se debe reconfigurar el trigger en la base de datos de Supabase para que escuche eventos `UPDATE` (o `INSERT OR UPDATE`) y envíe la petición HTTP POST al backend sólo cuando el estado de `fotos_completadas` pase a ser `true`.

#### Script SQL para Supabase Editor:
```sql
-- 1. Modificar la función para evaluar el cambio de estado
CREATE OR REPLACE FUNCTION public.handle_evaluacion_completa()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
declare
  payload jsonb;
  request_id bigint;
begin
  -- Solo disparar el webhook si fotos_completadas cambia a true
  if (NEW.fotos_completadas = true AND (TG_OP = 'INSERT' OR OLD.fotos_completadas IS NULL OR OLD.fotos_completadas = false)) then
    payload := jsonb_build_object(
      'wa_id', NEW.wa_id,
      'nombre', NEW.nombre,
      'fotos_completadas', true
    );
    
    select net.http_post(
      url := 'https://api.orusquiroterapia.online/api/biometrics/completed',
      body := payload,
      headers := '{"Content-Type": "application/json"}'::jsonb
    ) into request_id;
  end if;
  
  return NEW;
end;
$function$;

-- 2. Eliminar el trigger antiguo de inserción
DROP TRIGGER IF EXISTS tr_evaluaciones_completas_insert ON public.evaluaciones_completas;

-- 3. Crear el nuevo trigger que escucha INSERT y UPDATE
CREATE TRIGGER tr_evaluaciones_completas_update
AFTER INSERT OR UPDATE ON public.evaluaciones_completas
FOR EACH ROW
EXECUTE FUNCTION handle_evaluacion_completa();
```

---

## 3. Plan de Acción
1. **Paso 1:** Entregar el código SQL al usuario para que lo ejecute en el SQL Editor de Supabase.
2. **Paso 2:** Monitorear logs del backend en la VPS para verificar la llegada del webhook cuando se completen las fotos.
