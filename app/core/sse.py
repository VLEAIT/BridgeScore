import json 
from typing import Optional,Any

def format_sse(
    data:Any,
    event:Optional[str]=None,
    event_id:Optional[str]=None,
    retry:Optional[int]=None,
    ) -> str:
    lines = []
    if event_id :lines.append(f"id: {event_id}")
    if event :lines.append(f"event:{event}")
    if retry :lines.append(f"retry:{retry}")
    if isinstance(data, (dict,list)):
        payload=json.dumps(data,ensure_ascii=False)
    else:
        payload=str(data)

    for line in payload.splitlines():
        lines.append(f"data:{line}")    

    lines.append("")  
    return "\n".join(lines)+"\n"

def heartbeat()->str:
    return ":heartbeat\n\n"
