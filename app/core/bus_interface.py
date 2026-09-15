from typing import Protocol,AsyncGenerator,Dict,Any,runtime_checkable

@runtime_checkable
class BaseEventBus(Protocol):
    async def publish(self,stream_id:str,event:dict)->bool:
        ...

    async def listen(self,stream_id:str)->AsyncGenerator[Dict[str,Any],None]:
        ...

    async def close(self,stream_id:str)->None:
        ...    

