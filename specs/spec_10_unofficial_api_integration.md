# Spec 10: Integración E2E con API No Oficial (Z-API / Evolution API)

> **Estado:** ✅ COMPLETADO (2026-05-12) — Todos los micro-pasos implementados y validados en producción con Evolution API v2.2.3 + Pipeline v3 asyncio.

Este documento traza la nueva ruta de arquitectura para conectar el bot a WhatsApp evadiendo la burocracia de la Cloud API oficial de Meta, utilizando un proveedor de emulación de sesión web.

## Micro-Paso 1: Configuración de Credenciales y Endpoint
**Objetivo:** Preparar el entorno para recibir las variables del nuevo proveedor.
**Acciones:**
1. Eliminar variables `META_APP_SECRET`, `META_ACCESS_TOKEN`, etc.
2. Incorporar nuevas variables en `.env`: `WA_API_URL`, `WA_INSTANCE_ID`, `WA_INSTANCE_TOKEN`.
3. Configurar la URL de nuestro servidor (ngrok) dentro del panel del proveedor (Z-API/Evolution) para que nos envíen los webhooks de tipo `on-message-received`.

## Micro-Paso 2: Refactor del Endpoint Receptor (Webhook)
**Objetivo:** Adaptar el endpoint `POST /webhook` para entender el JSON entrante del nuevo proveedor, el cual tiene una estructura distinta a la de Meta.
**Acciones:**
1. Modificar `api/routes/webhooks.py`.
2. Remover el validador de firmas de Meta (ya eliminado).
3. Extraer el número de teléfono del remitente (`phone`) y el texto del mensaje (`text`) según el esquema de Z-API/Evolution.
4. Enviar el mensaje al `orchestrator.py` de la misma manera que antes.

## Micro-Paso 3: Creación del Cliente de Envío (`wa_client.py`)
**Objetivo:** Reemplazar el antiguo `meta_client.py` para poder enviar mensajes de vuelta al usuario.
**Acciones:**
1. Crear un servicio `api/services/wa_client.py`.
2. Implementar la función `send_message(phone, text)` que hará un POST HTTP al endpoint `/send-text` del proveedor.
3. Mantener la lógica de "Fraccionamiento Humano" (separando por `|||`) para simular la escritura humana con `asyncio.sleep()`.

## Micro-Paso 4: Verificación End-to-End
**Objetivo:** Probar el ciclo completo en vivo.
**Acciones:**
1. El usuario envía un mensaje de prueba al número escaneado.
2. El Webhook lo recibe, orquesta, va a Gemini, y Gemini responde.
3. El `wa_client.py` envía los mensajes fragmentados de vuelta al teléfono.
