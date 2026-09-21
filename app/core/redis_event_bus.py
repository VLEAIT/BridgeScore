import json 
import asyncio
import logging
from typing import Optional,AsyncGenerator
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class RedisEventBus:
    def __init__(self,redis_url:str="redis://localhost:6379"):
        self.redis_url=redis_url
        self.pool:Optional[redis.ConnectionPool]=None

    async def initialize(self):
        if self.pool is None:
            self.pool =redis.ConnectionPool.from_url(
                self.redis_url,
                decode_responses=True,
                max_connections=50
            ) 

    async def close_pool(self):
        if self.pool:
            await self.pool.disconnect() 

    def _get_client(self)->redis.Redis:
        if self.pool is None:
            self.pool =redis.ConnectionPool.from_url(self.redis_url,decode_responses=True)

        return redis.Redis(connection_pool=self.pool)

    async def publish(self,stream_id:str,event:dict)->bool:
        try:
            client=self._get_client()
            payload=json.dumps(event)
            await client.publish(f"sse:{stream_id}",payload)
            return True
        except Exception as e:
            logger.error(f"Failed to publish event to Redis from stream {stream_id}:{e}")  
            return False      
    async def listen(self,stream_id:str)->AsyncGenerator[dict,None]:
        client=self._get_client()
        pubsub=client.pubsub() 
        await pubsub.subscribe(f"sse:{stream_id}")   

        try:
            while True:
                message =await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0
                )    
                if message and message["type"]=="message":
                    data=json.loads(message["data"])
                    if data.get("__signal__")=="close":
                        break
                    yield data

                await asyncio.sleep(0.01)
        finally:
            await  pubsub.unsubscribe(f"sse:{stream_id}")
            await pubsub.close()        

    async def close(self,stream_id:str):
        await self.publish(stream_id,{"__signal__":"close"})

redis_event_bus=RedisEventBus()





       