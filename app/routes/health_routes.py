from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.db import get_db

router = APIRouter(tags=["Health"])
log = get_logger("health")


@router.get("/health")
async def health(db=Depends(get_db)):
    """Liveness + database check. 200 when Mongo answers a ping, 503 otherwise."""
    try:
        await db.command("ping")
    except Exception:
        log.warning("Health check: database ping failed", exc_info=True)
        return JSONResponse(
            status_code=503, content={"status": "degraded", "database": "unreachable"}
        )
    return {"status": "ok", "database": "ok"}
