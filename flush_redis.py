import os
from dotenv import load_dotenv
load_dotenv()
import redis as redislib

url = os.getenv("UPSTASH_REDIS_URL", "redis://localhost:6379")
r = redislib.from_url(url)

all_keys = r.keys("*")

prefixes_to_delete = ["arq:", "buffer:", "debounce", "last_msg:", "last_msg_time:", "msg_seen:", "processing_lock:"]
to_delete = [k for k in all_keys if any(k.decode().startswith(p) for p in prefixes_to_delete)]

print(f"Total claves en Redis: {len(all_keys)}")
print(f"Claves a eliminar: {len(to_delete)}")

for k in to_delete:
    print(f"  - {k.decode()}")

if to_delete:
    r.delete(*to_delete)
    print(f"\nEliminadas {len(to_delete)} claves.")

remaining = len(r.keys("*"))
print(f"Claves restantes en Redis: {remaining}")
