import logging
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger=logging.getLogger("bridgescore.http")

class LoggingMiddleware(BaseHTTPMiddlware):
    async def dispatch(self,request:Request,call_next)->Response:
        request_id=str(uuid.uuid4())[:8]
        logger.info(
            f"-> REQUEST [{request_id}] {request.method} {request.url.path}"
        )

        start_time=time.perf_counter()
        try:
            response=await call_next(request)
            duration_ms=(time.perf_counter()-start_time)*1000
            logger.info(
                f"<- RESPONSE [{request_id}]{response.status_code}"
                f"{request.method} {request.url.post}"
                f"completed in {duration_ms:.2f}ms"
            )
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as e:
            duration_ms=(time.perf_counter()-start_time)*1000
            logger.error(
                f"x ERROR [{request_id}] {request.method} {request.url.path}"
                f"failed after {duration_ms:.2f}ms -{str(e)}"
            )
            raise   

        
