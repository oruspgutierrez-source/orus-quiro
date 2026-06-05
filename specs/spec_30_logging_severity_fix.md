# Spec 30: Estandarización de Severidad en Logs del Sistema (System Logs)

## 1. Objetivo
Garantizar que la tabla `orus_logs` en Supabase refleje con precisión la criticidad de los eventos del sistema, evitando "falsos positivos" donde operaciones rutinarias (como el envío de mensajes a usuarios) se registran con severidad `ERROR`. El objetivo final es que cualquier evento listado en color rojo en el Dashboard sea un riesgo real para la infraestructura o la operación.

---

## 2. Diagnóstico del Problema

### El Síntoma
En el Dashboard de Orus Quiro (sección **System Logs**), los mensajes enviados rutinariamente por el agente hacia los pacientes (`event_type: OUTBOUND_MESSAGE_SENT`) aparecían marcados en **ROJO** con la severidad `ERROR`. 

### La Causa Raíz
Al analizar el archivo `api/services/message_processor.py` en la línea 382, la función encargada de enviar mensajes realizaba un `insert()` en la tabla `orus_logs` **sin especificar** explícitamente el parámetro `severity`. 
Al no proveer este parámetro, y dada la forma en que el Dashboard (o Supabase por defecto) interpreta los valores nulos para eventos de bitácora, el sistema asignaba `ERROR` por defecto.

---

## 3. Solución Implementada

Se realizó una intervención en el código base (Backend) para forzar la declaración explícita de severidad.

### Archivo Modificado
`api/services/message_processor.py` (Fragmentación y envío de mensajes).

### Cambio Aplicado:
Se eliminó por completo el registro de `OUTBOUND_MESSAGE_SENT` cuando el mensaje se envía exitosamente, ya que esto saturaba la base de datos de manera innecesaria y redundante (los mensajes ya existen en `orus_messages`). En su lugar, el bloque `try...except` ahora intercepta fallos reales y los inserta como `OUTBOUND_MESSAGE_ERROR` con severidad `ERROR`.

```python
# ANTES: Falso positivo y saturación de la DB
supabase.table('orus_logs').insert({
    'event_type': 'OUTBOUND_MESSAGE_SENT',
    'source_identifier': real_sender_id,
    'raw_payload': message_id or "evolution_api_outbound",
    'error_message': chunk[:500]
}).execute()

# DESPUÉS: Solo se registra si falla el envío de la API de WhatsApp
except Exception as e:
    supabase.table('orus_logs').insert({
        'event_type': 'OUTBOUND_MESSAGE_ERROR',
        'severity': 'ERROR',
        'source_identifier': real_sender_id,
        'error_message': f"Error enviando fragmento: {str(e)}",
        'raw_payload': chunk[:500]
    }).execute()
```

---

## 4. Auditoría de Otros Eventos

Para asegurar que esto no ocurra en otros flujos, se auditaron todas las inserciones en `orus_logs` dentro de la API:

1. **`EVOLUTION_CONNECTION_UPDATE`** (`webhooks.py`):
   - Mapea correctamente `INFO` si el estado es `open` o `connecting`.
   - Mapea a `ERROR` en caso de desconexión. (Correcto).

2. **`WEBHOOK_BIOMETRICS_ERROR`** (`webhooks.py`):
   - Mapea errores de procesamiento del webhook de base de datos.
   - Default = `ERROR` (Correcto, es un fallo real).

3. **`BILLING_PIPELINE_ERROR` y `PAYMENT_PROCESSING_ERROR`** (`payments.py`):
   - Mapea fallos en generación de PDF de facturas o fallos asíncronos post-pago.
   - Default = `ERROR` (Correcto, requiere atención humana).

---

## 5. Próximos Pasos (Opcional para el Mantenimiento)
1. Desplegar esta actualización en **EasyPanel**.
2. Una vez desplegada, el Dashboard comenzará a mostrar los nuevos mensajes enviados bajo la severidad verde/neutra de `INFO`.
3. (Opcional en Supabase): Para limpiar el historial de falsos positivos visuales en el Dashboard, se podría ejecutar una query SQL de limpieza:
   ```sql
   UPDATE orus_logs 
   SET severity = 'INFO' 
   WHERE event_type = 'OUTBOUND_MESSAGE_SENT';
   ```
   *Esto arreglará retroactivamente los logs anteriores para que dejen de verse en rojo.*
