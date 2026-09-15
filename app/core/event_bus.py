import asyncio,logging
from typing import Optional,Dict,Any

logger = logging.getLogger(__name__)

class EventBus:
    def __init__(self):
        self._queues:dict[str, asyncio.Queue] = {}

    def create(self, stream_id:str, max_size:int=100)->asyncio.Queue:
        q=asyncio.Queue(maxsize=max_size)
        self._queues[stream_id]=q
        return q

    def get(self, stream_id:str)->Optional[asyncio.Queue]:
        return self._queues.get(stream_id)

    async def publish(self, stream_id:str, event:dict)->bool:
        q=self._queues.get(stream_id)
        if not q:
            logger.warning(f"EventBus: No queue for stream_id {stream_id}")
            return False
        try:
            q.put_nowait(event)
            return True
        except asyncio.QueueFull:
            try:
                q.get_nowait()  
                q.put_nowait(event)
                logger.warning(f"EventBus: Queue full for stream_id {stream_id}, dropped oldest event")
                return True    
            except Exception:
                pass
            return False    
    async def listen(self,stream_id:str)->AsyncGenerator[Dict[str,Any],None]:
        q =self.get(stream_id)
        if not q:
            q = self.create(stream_id)
        try:
            while True:
                event=await q.get()
                if event is None or event.get("__signal__")=="close":
                    break
                yield event
        finally:
            await q.close(stream_id)        

    async def close(self, stream_id:str):
        q=self._queues.get(stream_id)
        if q:
            q.put_nowait({"__signal__":"close"})
            self._queues.pop(stream_id,None)
       

    def active_streams(self)->list[str]:
        return list(self._queues.keys())

event_bus=EventBus()                        
    





            
            
        
