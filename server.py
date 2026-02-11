"""Kingdom Wars Bot — FastAPI Server"""

import sys
from fastapi import FastAPI, Request
from models import NegotiateRequest, CombatRequest
import strategy

app = FastAPI(title="Kingdom Wars Bot")

TEAM_NAME = "Adaptive Predator"


# ─── Logging middleware ──────────────────────────────────────────────

@app.middleware("http")
async def kw_log(request: Request, call_next):
    print("[KW-BOT] Mega ogudor", flush=True)
    return await call_next(request)


# ─── Endpoints ───────────────────────────────────────────────────────

@app.get("/healthz")
async def healthz():
    return {"status": "OK"}


@app.get("/info")
async def info():
    return {
        "name": TEAM_NAME,
        "strategy": "AI-trapped-strategy",
        "version": "1.0"
    }


@app.post("/negotiate")
async def negotiate(req: NegotiateRequest):
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
    return result


@app.post("/combat")
async def combat(req: CombatRequest):
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
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, workers=2)
