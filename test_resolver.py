import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("EVOLUTION_API_URL")
INSTANCE = os.getenv("EVOLUTION_INSTANCE_NAME")
API_KEY = os.getenv("EVOLUTION_API_KEY")

class WhatsAppClientMock:
    def __init__(self):
        self.api_url = API_URL
        self.instance_name = INSTANCE
        self.api_key = API_KEY
        self._lid_cache = {}

    def _get_headers(self):
        return {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }

    async def resolve_lid(self, lid: str) -> str:
        if not lid.endswith("@lid"):
            return lid
            
        if lid in self._lid_cache:
            return self._lid_cache[lid]
            
        endpoint = f"{self.api_url}/chat/findContacts/{self.instance_name}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(endpoint, json={"where": {}}, headers=self._get_headers()) as response:
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
                                    print(f"LID {lid} resuelto a {real_jid} por pushName")
                                    return real_jid
                                elif target_pic and c.get("profilePicUrl") == target_pic:
                                    real_jid = c.get("remoteJid")
                                    self._lid_cache[lid] = real_jid
                                    print(f"LID {lid} resuelto a {real_jid} por profilePicUrl")
                                    return real_jid
            except Exception as e:
                print(f"Error resolviendo LID: {e}")
                
        return lid

async def main():
    client = WhatsAppClientMock()
    result = await client.resolve_lid("37598781259882@lid")
    print(f"Resultado: {result}")

if __name__ == "__main__":
    asyncio.run(main())
