import os 
import logging
from app.core.event_bus import event_bus
from app.core.redis_event_bus import redis_event_bus
from app.core.bus_interface import BaseEventBus
from app.core.config import settings

logger=logging.getLogger(__name__)

def get_event_bus()->BaseEventBus:
    if getattr(settings,"production",False):
        return redis_event_bus

    return event_bus    
   