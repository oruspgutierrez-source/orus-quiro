# Spec 28: Sistema de Atención Manual y Transición en Inbox Chat

## 1. Objetivo
Diseñar la arquitectura técnica de la vista "Inbox Chat" en el Dashboard, definiendo cómo un operador humano asume el control de una conversación de WhatsApp y se comunica en tiempo real con el cliente.

---

## 2. Aclaración Clave sobre Evolution API y el Número de WhatsApp

**No es necesario crear un número nuevo en Evolution API para el Dashboard.** 
El diseño arquitectónico de Orus permite una **transición fluida y transparente (Seamless Handover)**:
1. El bot de IA y el operador humano utilizan exactamente **el mismo número de WhatsApp** (la misma instancia de Evolution API).
2. Cuando el usuario solicita ayuda, el bot cambia el `session_mode` a `HUMAN` y deja de responder automáticamente.
3. El operador, desde el Dashboard, lee el historial y envía su respuesta.
4. Para el cliente final, la experiencia es continua en el mismo chat, percibiendo simplemente que ha sido transferido a un humano.

---

## 3. Arquitectura del Chat Bidireccional

### 3.1 Recepción de Mensajes (Inbound)
1. El usuario de WhatsApp envía un mensaje.
2. Evolution API envía el payload al Webhook del Backend de Orus.
3. El Backend guarda el mensaje en la tabla `orus_messages` de Supabase.
4. **El Dashboard (React)** está suscrito mediante `supabase.channel('public:orus_messages')`. Al detectar la inserción, la UI actualiza la pantalla del chat instantáneamente sin recargar la página.

### 3.2 Envío de Mensajes por el Operador (Outbound)
1. El operador escribe un mensaje en el "Inbox Chat" y presiona enviar.
2. El Dashboard hace una petición HTTP `POST` a `/api/users/{user_id}/send_manual_message`.
3. El Backend de Orus recibe la petición y:
   - Extrae el número de teléfono del cliente desde `orus_users`.
   - Llama a `wa_client.send_message(...)` para enviarlo mediante Evolution API.
   - Registra el mensaje en `orus_messages` con el rol `assistant`.
4. El Dashboard se actualiza y muestra el mensaje del operador en la burbuja de chat verde.

---

## 4. Gestión del Ciclo de Vida de la Sesión (Handover)

* **Inicio de Intervención:** Cuando un cliente escribe algo crítico o pide hablar con un humano, el bot establece `session_mode = 'HUMAN'` e inserta un registro en la nueva tabla `orus_agent_interventions` (como se vio en Spec 27).
* **Finalización de Intervención:** El operador presiona un botón "Resolver / Retornar a IA" en el Dashboard, lo que llama al endpoint `/api/users/{user_id}/resolve`. Esto devuelve `session_mode = 'AI'` y el bot de WhatsApp retoma el control automático de la conversación.

---

## 5. Próximos Pasos para Desarrollo
1. Implementar la conexión de Supabase Realtime en el componente `InboxChatView.jsx`.
2. Habilitar la caja de texto para hacer el `POST` al endpoint existente de mensajes manuales.
3. Añadir el botón de "Finalizar Intervención" para devolver al bot al mando.
