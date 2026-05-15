import os
import asyncio
import time
from dotenv import load_dotenv
from redis.asyncio import Redis

load_dotenv()

async def main():
    r = Redis.from_url(os.getenv('UPSTASH_REDIS_URL'))
    await r.rpush('buffer:553598869018@s.whatsapp.net', 'Hola')
    await r.set('last_msg:553598869018@s.whatsapp.net', str(time.time() - 20))
    print('Done')

if __name__ == "__main__":
    asyncio.run(main())
