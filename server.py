"""Kingdom Wars Bot — FastAPI Server (Optimized)"""

import sys
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from models import NegotiateRequest, CombatRequest
import strategy

app = FastAPI(
    title="Kingdom Wars Bot - Apex Predator",
    version="2.0"
)

TEAM_NAME = "Apex Predator"


# ─── Logging middleware ──────────────────────────────────────────────

@app.middleware("http")
async def kw_log(request: Request, call_next):
    """Required logging for game system."""
    print("[KW-BOT] Mega ogudor", flush=True)
    return await call_next(request)


# ─── Error handling middleware ───────────────────────────────────────

@app.middleware("http")
async def error_handler(request: Request, call_next):
    """Ensure we never crash - return empty actions on error."""
    try:
        return await call_next(request)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr, flush=True)
        # Return empty action list on any error
        return JSONResponse(content=[], status_code=200)


# ─── Endpoints ───────────────────────────────────────────────────────

@app.get("/healthz")
async def healthz():
    """Health check endpoint."""
    return {"status": "OK"}


@app.get("/info")
async def info():
    """Bot metadata endpoint."""
    return {
        "name": TEAM_NAME,
        "strategy": "AI-trapped-strategy",
        "version": "2.0"
    }


@app.post("/negotiate")
async def negotiate(req: NegotiateRequest):
    """Negotiation phase - return diplomatic proposals."""
    try:
        player = req.playerTower.model_dump()
        enemies = [e.model_dump() for e in req.enemyTowers]
        actions = [a.model_dump() for a in req.combatActions]

        result = strategy.negotiate(
            gid=req.gameId,
            turn=req.turn,
            player=player,
            enemies=enemies,
            combat_actions=actions,
        )
        
        # Ensure valid response
        if not isinstance(result, list):
            return []
        
        return result
    
    except Exception as e:
        print(f"[NEGOTIATE ERROR] {e}", file=sys.stderr, flush=True)
        return []


@app.post("/combat")
async def combat(req: CombatRequest):
    """Combat phase - return actions (armor/attack/upgrade)."""
    try:
        player = req.playerTower.model_dump()
        enemies = [e.model_dump() for e in req.enemyTowers]
        diplo = [d.model_dump() for d in req.diplomacy]
        prev = [p.model_dump() for p in req.previousAttacks]

        result = strategy.combat(
            gid=req.gameId,
            turn=req.turn,
            player=player,
            enemies=enemies,
            diplomacy=diplo,
            previous_attacks=prev,
        )
        
        # Ensure valid response
        if not isinstance(result, list):
            return []
        
        return result
    
    except Exception as e:
        print(f"[COMBAT ERROR] {e}", file=sys.stderr, flush=True)
        return []


# ─── Startup / Shutdown ──────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    """Bot initialization."""
    print("[STARTUP] Apex Predator Bot initialized", flush=True)
    print("[STARTUP] Strategy: Elite multi-factor prediction with trust system", flush=True)


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    strategy.memory.cleanup()
    print("[SHUTDOWN] Bot terminated gracefully", flush=True)


# ─── Main ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        workers=1,
        log_level="info"
    )
