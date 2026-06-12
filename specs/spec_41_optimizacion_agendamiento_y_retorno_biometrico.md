# Spec 41: Optimización de Agendamiento y Retorno Biométrico

Este documento especifica el diagnóstico, el plan de acción y las tareas para resolver dos problemas críticos del flujo de confirmación y recolección biométrica del Consultante.

---

## 1. Diagnóstico Técnico

### 1.1. Problema A: Fallos en el Registro Interactivo del Calendario
El enlace directo `htmlLink` de la cita de Google Calendar que se envía al consultante genera fallos de experiencia o compatibilidad en dispositivos móviles (requiere inicio de sesión en Google en navegadores móviles, fallos de redirección, etc.). Las 3 imágenes de guías visuales y los textos largos añaden fricción a la conversación.

*   **Diagnóstico:** La reserva de la cita **ya es real y firme** en el Google Calendar del especialista (Orus Peña) desde que el bot ejecuta la llamada a la API de Calendar. La acción del consultante de agregarlo a su propio calendario es opcional y de conveniencia.
*   **Decisión Propuesta:** Eliminar el flujo explicativo, los retardos y el envío de las 3 imágenes guías de calendario. Reducir la confirmación a un único mensaje simple, directo y asertivo con los detalles de fecha/hora, seguido de inmediato por el link de la Web App biométrica.

### 1.2. Problema B: Retorno sin Mensaje Automático de la Web App
El consultante completa su carga de fotos en la Web App (Vercel) y regresa al chat de WhatsApp, pero el bot de producción no envía el mensaje de confirmación automática de recepción biométrica.

*   **Causa Raíz:** La función del trigger de Supabase `handle_evaluacion_completa` que despacha el webhook de base de datos (`pg_net.http_post`) tiene cableada una URL de pruebas obsoleta (`https://annually-murmuring-reuse.ngrok-free.dev/api/biometrics/completed`).
*   **Consecuencia:** La base de datos intenta enviar la confirmación a un túnel ngrok inexistente, por lo que el endpoint `/api/biometrics/completed` en la VPS nunca es notificado del registro y el bot no despacha el mensaje de felicitaciones/éxito al WhatsApp del consultante.

---

## 2. Plan de Acción Propuesto

### Fase 1: Simplificación Conversacional (Eliminación de Fricción de Calendario)
1.  **Modificar el backend (`api/services/calendar_client.py` o donde se envíen las guías):**
    *   Remover la carga y el envío de las 3 imágenes guía de Google Calendar (`guia_cal_1.png`, `guia_cal_2.png`, `guia_cal_3.png`).
    *   Formatear la respuesta de confirmación para que de inmediato anuncie que la reserva se completó con éxito (mostrando fecha, hora local y enlace biométrico).
    *   Ejemplo de mensaje unificado propuesto:
        > *"¡Excelente! Tu cita para la Auditoría Biosemiótica ha quedado reservada con éxito para el **{dia_semana} {fecha_formateada}** a las **{hora_formateada}**.\n\nPara completar tu proceso de preparación, el siguiente paso es registrar tus datos y fotos biométricas en nuestro formulario seguro: https://ruta-del-escultor.vercel.app/"*

### Fase 2: Corrección del Webhook Reactivo de Supabase
1.  **Ejecutar Script de Migración SQL en Supabase:**
    *   Actualizar la función de trigger `handle_evaluacion_completa` para redirigir las notificaciones HTTP POST al host de producción de la VPS: `https://api.orusquiroterapia.online/api/biometrics/completed`.
2.  **Optimización del Enlace de Retorno en la Web App:**
    *   Modificar la Web App biométrica (`ruta-del-escultor.vercel.app`) para que el botón de retorno a WhatsApp use una URL formateada con un texto predefinido que invite al consultante a enviar un mensaje voluntario (por ejemplo: `https://wa.me/55.../?text=Listo,%20ya%20registré%20mis%20datos%20biométricos`). Esto reactivará inmediatamente el hilo de conversación en WhatsApp en caso de demoras en la red.

---

## 3. Tareas a Ejecutar (Fase de Implementación)

### Tarea 1: Remoción de Guías Visuales de Calendario
*   **Archivo:** `api/services/calendar_client.py` (o el servicio que despache el protocolo del calendario).
*   **Cambio:** Comentar o eliminar la rutina de despacho secuencial de imágenes de guía y simplificar el mensaje de confirmación enviando de forma directa la fecha/hora y el link de la Web App biométrica.

### Tarea 2: Script SQL de Actualización de Webhook en Supabase
*   **Acción:** Ejecutar el siguiente DDL en el editor SQL de Supabase:
    ```sql
    CREATE OR REPLACE FUNCTION public.handle_evaluacion_completa()
     RETURNS trigger
     LANGUAGE plpgsql
     SECURITY DEFINER
    AS $function$
    declare
      payload jsonb;
      request_id bigint;
    begin
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
      
      return NEW;
    end;
    $function$
    ```

---

## 4. Estado de Viabilidad y Seguridad
*   **Riesgos:** Ninguno. La cita ya se agenda de forma real en Google Calendar independientemente de si el usuario añade la invitación a su propio calendario o no. La simplificación eliminará de raíz los problemas de soporte por compatibilidad.
*   **Seguridad (REPORT_ONLY):** No se ejecutará ningún cambio en el código fuente de producción hasta recibir la confirmación explícita del usuario.
