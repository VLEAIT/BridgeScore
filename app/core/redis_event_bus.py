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
    
            
       