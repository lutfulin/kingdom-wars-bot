"""Pydantic models for Kingdom Wars API requests/responses."""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any


# === Request Models ===

class PlayerTower(BaseModel):
    playerId: int
    hp: int
    armor: int
    resources: int
    level: int


class EnemyTower(BaseModel):
    playerId: int
    hp: int
    armor: int
    level: int


class ActionEntry(BaseModel):
    playerId: int
    action: Dict[str, Any] = {}


class NegotiateRequest(BaseModel):
    gameId: int
    turn: int
    playerTower: PlayerTower
    enemyTowers: List[EnemyTower]
    combatActions: List[ActionEntry] = []


class CombatRequest(BaseModel):
    gameId: int
    turn: int
    playerTower: PlayerTower
    enemyTowers: List[EnemyTower]
    diplomacy: List[ActionEntry] = []
    previousAttacks: List[ActionEntry] = []
