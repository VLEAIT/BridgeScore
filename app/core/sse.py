import json 

def format_sse(
    data:dict,
    event:str=None,
    event_id:str=None,
    retry:int=None,
    ) -> str:
    lines = []
    if event_id :lines.append(f"id: {event_id}")
    if event :lines.append(f"event:{event}")
    if retry :lines.append(f"retry:{retry}")
    lines.append(f"data:{json.dumps(data,ensure_ascii=False)}")
    lines.append("")  
    return "\n".join(lines)+"\n"

def heartbeat()->str:
    return ":heartbeat\n\n"
