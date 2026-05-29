import os
import base64
import asyncio
import aiohttp
import json

class WhatsAppClient:
    def __init__(self):
        self.api_url = os.getenv("EVOLUTION_API_URL")
        self.instance_name = os.getenv("EVOLUTION_INSTANCE_NAME")
        self.api_key = os.getenv("EVOLUTION_API_KEY")
        self._lid_cache = {}
        
        if not self.api_url or not self.instance_name or not self.api_key:
            print("WARNING: Credenciales de Evolution API no configuradas en el .env")

    def _get_headers(self):
        return {
            "apikey": self.api_key,
            "Content-Type": "application/json",
            "Host": "whatsapp.orusquiroterapia.online"
        }

    async def resolve_lid(self, lid: str) -> str:
        """
        Resuelve un identificador @lid a un número @s.whatsapp.net buscando en los contactos
        las coincidencias de pushName o profilePicUrl.
        """
        if not lid or not lid.endswith("@lid"):
            return lid
            
        if lid in self._lid_cache:
            return self._lid_cache[lid]
            
        endpoint = f"{self.api_url}/chat/findContacts/{self.instance_name}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(endpoint, json={"where": {}}, headers=self._get_headers(), ssl=False) as response:
                    if response.status == 200:
                        contacts = await response.json()
                        lid_contact = None
                        for c in contacts:
                            if c.get("remoteJid") == lid:
                                lid_contact = c
                                break
                        
                        if not lid_contact:
                            return lid
                            
                        target_name = lid_contact.get("pushName")
                        target_pic = lid_contact.get("profilePicUrl")
                        
                        for c in contacts:
                            if c.get("remoteJid", "").endswith("@s.whatsapp.net"):
                                if target_name and c.get("pushName") == target_name:
                                    real_jid = c.get("remoteJid")
                                    self._lid_cache[lid] = real_jid
                                    print(f"[LID RESOLVER] {lid} resuelto a {real_jid} por pushName")
                                    return real_jid
                                elif target_pic and c.get("profilePicUrl") == target_pic:
                                    real_jid = c.get("remoteJid")
                                    self._lid_cache[lid] = real_jid
                                    print(f"[LID RESOLVER] {lid} resuelto a {real_jid} por profilePicUrl")
                                    return real_jid
            except Exception as e:
                print(f"Error resolviendo LID {lid}: {e}")
                
        return lid

    async def download_media(self, message_key: dict, message_obj: dict) -> bytes | None:
        """
        Descarga un archivo multimedia desde Evolution API.
        Usa el endpoint getBase64FromMediaMessage que recibe el mensaje completo,
        permitiendo que Evolution API lo desencripte al instante usando las llaves
        del webhook sin depender del storage interno.
        
        Args:
            message_key: El objeto 'key' del payload del webhook (contiene id, remoteJid, fromMe).
            message_obj: El objeto 'message' completo que contiene mediaKey, url, etc.
        
        Returns:
            bytes del archivo decodificado, o None si falla.
        """
        endpoint = f"{self.api_url}/chat/getBase64FromMediaMessage/{self.instance_name}"
        
        payload = {
            "message": {
                "key": message_key,
                "message": message_obj
            },
            "convertToMp4": False
        }
        
        msg_id = message_key.get('id', '???')
        print(f"[Media Download] POST {endpoint} (msg_id={msg_id})", flush=True)
        
        # Reintentos (con el objeto completo usualmente es instantáneo)
        MAX_RETRIES = 3
        DELAYS = [0, 2, 4]  # Segundos de espera antes de cada intento
        
        async with aiohttp.ClientSession() as session:
            for attempt in range(MAX_RETRIES):
                # Esperar antes de intentar (Evolution API necesita tiempo para almacenar)
                wait_time = DELAYS[attempt]
                print(f"[Media Download] Intento {attempt+1}/{MAX_RETRIES} — esperando {wait_time}s...", flush=True)
                await asyncio.sleep(wait_time)
                
                try:
                    async with session.post(endpoint, json=payload, headers=self._get_headers(), timeout=aiohttp.ClientTimeout(total=30), ssl=False) as response:
                        response_text = await response.text()
                        
                        if response.status == 400:
                            # "Message not found" — probablemente aún no se almacenó
                            print(f"[Media Download] 400 (intento {attempt+1}): {response_text[:200]}", flush=True)
                            continue  # Reintentar
                        
                        if response.status >= 300:
                            print(f"[Media Download] HTTP {response.status}: {response_text[:500]}", flush=True)
                            return None
                        
                        # Intentar parsear como JSON
                        try:
                            data = json.loads(response_text)
                        except json.JSONDecodeError:
                            print(f"[Media Download] Respuesta no-JSON ({len(response_text)} chars)", flush=True)
                            data = {"base64": response_text}
                        
                        # Debug: ver qué keys tiene la respuesta
                        debug_keys = {k: (f"<{len(str(v))} chars>" if len(str(v)) > 100 else v) for k, v in data.items()}
                        print(f"[Media Download] Respuesta keys: {debug_keys}", flush=True)
                        
                        # Buscar base64 en múltiples campos posibles
                        b64_string = data.get("base64") or data.get("mediaBase64") or data.get("data") or ""
                        
                        if not b64_string:
                            print(f"[Media Download] SIN base64 en respuesta. Keys: {list(data.keys())}", flush=True)
                            continue  # Reintentar
                        
                        # Evolution API retorna con prefijo data URI: "data:image/jpeg;base64,/9j/..."
                        if "," in b64_string:
                            b64_string = b64_string.split(",", 1)[1]
                        
                        media_bytes = base64.b64decode(b64_string)
                        print(f"[Media Download] OK — {len(media_bytes)} bytes descargados (intento {attempt+1})", flush=True)
                        return media_bytes
                        
                except asyncio.TimeoutError:
                    print(f"[Media Download] Timeout intento {attempt+1}", flush=True)
                    continue
                except Exception as e:
                    print(f"[Media Download] Excepcion intento {attempt+1}: {type(e).__name__}: {e}", flush=True)
                    continue
        
        print(f"[Media Download] FALLIDO después de {MAX_RETRIES} intentos para msg_id={msg_id}", flush=True)
        return None

    async def send_message(self, to: str, text: str) -> dict:
        """
        Envía un mensaje de texto plano a través de Evolution API.
        """
        if not self.api_url:
            raise ValueError("EVOLUTION_API_URL no está configurada")

        # Resolvemos el @lid si es necesario
        to = await self.resolve_lid(to)

        endpoint = f"{self.api_url}/message/sendText/{self.instance_name}"
        
        # Evolution API v2 permite y requiere el sufijo completo (@lid, @s.whatsapp.net, @g.us)
        # Si eliminamos el sufijo, asume @s.whatsapp.net, lo que causa error 400 en números @lid
        payload = {
            "number": to,
            "text": text,
            "delay": 1200  # Evolution API v2 permite delay para simular typing
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(endpoint, json=payload, headers=self._get_headers(), ssl=False) as response:
                    response_data = await response.json()
                    
                    if response.status not in (200, 201):
                        print(f"Error enviando mensaje WA a {to}: status={response.status}", flush=True)
                    else:
                        msg_id = response_data.get("key", {}).get("id", "unknown")
                        print(f"Éxito enviando a {to}: status={response.status}, msg_id={msg_id}", flush=True)
                    
                    return response_data
            except Exception as e:
                # Evitar fallar por impresión de emojis en el mensaje de error original si los hubiera
                print(f"Excepción en send_message para {to}: {type(e).__name__}", flush=True)
                return {"error": str(e)}

    async def send_audio_message(self, to: str, audio_path_or_url: str, delay: int = 1200) -> dict:
        """
        Envía un mensaje de audio (nota de voz pregrabada) a través de Evolution API.
        Soporta URLs públicas o rutas locales de archivos (las cuales convierte a Base64).
        """
        if not self.api_url:
            raise ValueError("EVOLUTION_API_URL no está configurada")

        # Resolvemos el @lid si es necesario
        to = await self.resolve_lid(to)

        endpoint = f"{self.api_url}/message/sendWhatsAppAudio/{self.instance_name}"

        # 1. Determinar si es una URL o una ruta local
        audio_data = audio_path_or_url
        if not (audio_path_or_url.startswith("http://") or audio_path_or_url.startswith("https://")):
            # Es un archivo local. Leer y codificar a Base64
            if not os.getenv("WORKSPACE_PATH"):
                # Asumir ruta absoluta o relativa basada en Cwd
                pass
            
            if not os.path.exists(audio_path_or_url):
                raise FileNotFoundError(f"No se encontró el archivo de audio local: {audio_path_or_url}")
            
            with open(audio_path_or_url, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            
            # Detectar mime-type por la extensión
            ext = os.path.splitext(audio_path_or_url)[1].lower()
            mime = "audio/ogg"
            if ext == ".mp3":
                mime = "audio/mpeg"
            elif ext == ".wav":
                mime = "audio/wav"
            elif ext == ".ogg":
                mime = "audio/ogg"
            
            audio_data = encoded

        # 2. Configurar payload
        payload = {
            "number": to,
            "audio": audio_data,
            "delay": delay,
            "encoding": True
        }

        async with aiohttp.ClientSession() as session:
            try:
                # Usamos headers estándar y bypass SSL
                async with session.post(endpoint, json=payload, headers=self._get_headers(), ssl=False) as response:
                    response_data = await response.json()
                    
                    if response.status not in (200, 201):
                        print(f"Error enviando audio WA a {to}: status={response.status}", flush=True)
                    else:
                        msg_id = response_data.get("key", {}).get("id", "unknown")
                        print(f"Éxito enviando audio a {to}: status={response.status}, msg_id={msg_id}", flush=True)
                    
                    return response_data
            except Exception as e:
                # Evitar crashes de codificación en consola Windows
                safe_err = str(e).encode('ascii', 'replace').decode('ascii')
                print(f"Excepción en send_audio_message para {to}: {safe_err}", flush=True)
                return {"error": str(e)}

    async def send_text_then_audio(self, to: str, text: str, audio_path: str, text_delay: int = 1200, gap_seconds: float = 2.0) -> dict:
        """
        Envía un texto descriptivo, espera gap_seconds, y luego envía un audio.
        Garantiza el orden de llegada en WhatsApp.
        """
        # Envía texto
        res_text = await self.send_message(to, text)
        if "error" in res_text:
            return res_text
        
        # Delay
        await asyncio.sleep(gap_seconds)
        
        # Envía audio
        res_audio = await self.send_audio_message(to, audio_path, delay=text_delay)
        return {"text_response": res_text, "audio_response": res_audio}

    async def send_document_message(self, to: str, file_path: str, file_name: str, caption: str = "") -> dict:
        """
        Envía un documento (como un PDF) a través de Evolution API.
        Convierte el archivo local a base64 y lo despacha de forma asíncrona.
        """
        if not self.api_url:
            raise ValueError("EVOLUTION_API_URL no está configurada")

        # Resolvemos el @lid si es necesario
        to = await self.resolve_lid(to)

        endpoint = f"{self.api_url}/message/sendMedia/{self.instance_name}"

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"No se encontró el archivo del documento local: {file_path}")

        # Leer el archivo y codificarlo en Base64
        with open(file_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")

        # Usar la cadena base64 cruda sin prefijo para evitar el error 400 en Evolution API
        media_data = encoded

        payload = {
            "number": to,
            "media": media_data,
            "mediatype": "document",
            "fileName": file_name,
            "caption": caption,
            "delay": 1200
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(endpoint, json=payload, headers=self._get_headers(), ssl=False) as response:
                    response_data = await response.json()
                    
                    if response.status not in (200, 201):
                        print(f"Error enviando documento WA a {to}: status={response.status}", flush=True)
                    else:
                        msg_id = response_data.get("key", {}).get("id", "unknown")
                        print(f"Éxito enviando documento a {to}: status={response.status}, msg_id={msg_id}", flush=True)
                    
                    return response_data
            except Exception as e:
                safe_err = str(e).encode('ascii', 'replace').decode('ascii')
                print(f"Excepción en send_document_message para {to}: {safe_err}", flush=True)
                return {"error": str(e)}

    async def send_image_message(self, to: str, file_path: str, caption: str = "") -> dict:
        """
        Envía una imagen a través de Evolution API.
        Convierte la imagen local a base64 y la despacha de forma asíncrona.
        """
        if not self.api_url:
            raise ValueError("EVOLUTION_API_URL no está configurada")

        # Resolvemos el @lid si es necesario
        to = await self.resolve_lid(to)

        endpoint = f"{self.api_url}/message/sendMedia/{self.instance_name}"

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"No se encontró la imagen local: {file_path}")

        # Leer el archivo y codificarlo en Base64
        with open(file_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")

        media_data = encoded

        payload = {
            "number": to,
            "media": media_data,
            "mediatype": "image",
            "caption": caption,
            "delay": 1200
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(endpoint, json=payload, headers=self._get_headers(), ssl=False) as response:
                    response_data = await response.json()
                    
                    if response.status not in (200, 201):
                        print(f"Error enviando imagen WA a {to}: status={response.status}", flush=True)
                    else:
                        msg_id = response_data.get("key", {}).get("id", "unknown")
                        print(f"Éxito enviando imagen a {to}: status={response.status}, msg_id={msg_id}", flush=True)
                    
                    return response_data
            except Exception as e:
                safe_err = str(e).encode('ascii', 'replace').decode('ascii')
                print(f"Excepción en send_image_message para {to}: {safe_err}", flush=True)
                return {"error": str(e)}

    async def send_reaction(self, to: str, message_id: str, emoji: str) -> dict:
        """
        (Opcional) Enviar reacción a un mensaje específico. 
        Útil para dar feedback inmediato al usuario ("He leído tu mensaje").
        """
        # Resolvemos el @lid si es necesario
        to = await self.resolve_lid(to)
        
        endpoint = f"{self.api_url}/message/sendReaction/{self.instance_name}"
        
        clean_number = to.split("@")[0]
        
        payload = {
            "number": clean_number,
            "reactionMessage": {
                "key": {
                    "id": message_id,
                    "remoteJid": to,
                    "fromMe": False
                },
                "text": emoji
            }
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(endpoint, json=payload, headers=self._get_headers(), ssl=False) as response:
                    return await response.json()
            except Exception as e:
                print(f"Excepción en send_reaction: {str(e)}")
                return {"error": str(e)}

# Instancia global (singleton)
wa_client = WhatsAppClient()

