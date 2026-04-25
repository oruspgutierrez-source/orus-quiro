import re
import asyncio
import random

async def send_raw_message(recipient_id: str, text: str):
    """
    Función base para simular el envío HTTP a Meta usando httpx.
    (Por ahora imprime en consola el POST simulado).
    """
    # En el futuro aquí iría la lógica de httpx.post
    print(f"\n>>>> [META API SIMULADA -> {recipient_id}] Enviando: {text}\n", flush=True)

async def send_humanized_response(recipient_id: str, full_text: str):
    """
    Recibe el texto crudo de la IA, lo fracciona de manera inteligente
    y envía los fragmentos simulando los tiempos de escritura humana.
    """
    print(f"\n--- [DEBUG] TEXTO COMPLETO RECIBIDO DE GEMINI ---\n{full_text}\n---------------------------------------------------", flush=True)
    
    # 1. Separación primaria usando Regex (blindado contra errores tipográficos de la IA)
    # Busca 2 o más caracteres '|' consecutivos
    raw_chunks = re.split(r'\|{2,}', full_text)
    
    # 2. Mecanismo de Degradación / Fallback (si la IA olvidó el delimitador)
    if len(raw_chunks) == 1:
        print("[META_CLIENT] Advertencia: Gemini olvidó el delimitador |||. Ejecutando Fallback a doble salto de línea (\\n\\n).", flush=True)
        raw_chunks = re.split(r'\n{2,}', full_text)
        
    # 3. Filtrado de fragmentos inválidos
    clean_chunks = [chunk.strip() for chunk in raw_chunks if len(chunk.strip()) > 1]
    
    print(f"\n--- [DEBUG] LISTA DE FRAGMENTOS LISTOS PARA ENVÍO ({len(clean_chunks)}) ---", flush=True)
    for i, c in enumerate(clean_chunks):
         print(f"[{i+1}]: {c}", flush=True)
    print("---------------------------------------------------", flush=True)
    
    # 4. Envío Serializado Asíncrono
    for chunk in clean_chunks:
        # Simulamos tiempo de "Escribiendo..."
        delay = random.uniform(3.0, 5.0)
        print(f"[META_CLIENT] Esperando {delay:.2f}s antes de enviar fragmento a {recipient_id}...", flush=True)
        await asyncio.sleep(delay)
        
        # En el futuro se encapsulará en un try...except con timeout
        await send_raw_message(recipient_id, chunk)
    
    print(f"[META_CLIENT] Secuencia de envío completada para {recipient_id}.\n", flush=True)
