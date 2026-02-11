"""
Kingdom Wars AI Strategy: "Adaptive Predator"

Core principles:
1. ECONOMY FIRST: Rush upgrades early (compound resource advantage)
2. DOUBLE ALLIANCE: Propose alliance to 2 players, point them at the 3rd
3. FOCUS FIRE: If we can kill someone this turn, always do it
4. ADAPTIVE DEFENSE: Armor based on incoming threat + current HP
5. FATIGUE AGGRESSION: All-in attack after turn 25
"""

import math
from collections import defaultdict
from typing import List, Dict, Any

FATIGUE_TURN = 25
MAX_LEVEL = 5


def res_per_turn(level: int) -> int:
    return math.ceil(20 * (1.5 ** (level - 1)))


def upg_cost(current_level: int) -> int:
    return math.ceil(50 * (1.75 ** (current_level - 1)))


# ─── Cross-Turn Memory ───────────────────────────────────────────────

class GameMemory:
    """Tracks aggression, alliances, and betrayals across turns per game."""

    def __init__(self):
        self._g: Dict[int, Dict] = {}

    def _get(self, gid: int) -> Dict:
        if gid not in self._g:
            self._g[gid] = {
                "agg": defaultdict(int),        # total troops sent at us
                "ally_turns": defaultdict(set),  # turns they allied with us
                "betrayals": defaultdict(int),   # attacked while allied
                "our_allies": set(),
            }
        return self._g[gid]

    def record_attacks_on_us(self, gid, turn, my_id, attacks):
        g = self._get(gid)
        for a in attacks:
            act = a.get("action", {})
            if act.get("targetId") == my_id:
                pid = a.get("playerId")
                g["agg"][pid] += act.get("troopCount", 0)
                if turn - 1 in g["ally_turns"].get(pid, set()):
                    g["betrayals"][pid] += 1

    def record_diplomacy_to_us(self, gid, turn, diplomacy, my_id):
        g = self._get(gid)
        for d in diplomacy:
            if d.get("action", {}).get("allyId") == my_id:
                g["ally_turns"][d["playerId"]].add(turn)

    def agg(self, gid, pid):
        return self._get(gid)["agg"].get(pid, 0)

    def betrayals(self, gid, pid):
        return self._get(gid)["betrayals"].get(pid, 0)

    def set_our_allies(self, gid, ids):
        self._get(gid)["our_allies"] = set(ids)

    def get_our_allies(self, gid):
        return self._get(gid)["our_allies"]

    def cleanup(self):
        if len(self._g) > 500:
            for k in list(self._g.keys())[:-100]:
                del self._g[k]


memory = GameMemory()


# ─── Helper ──────────────────────────────────────────────────────────

def _strength(e: Dict) -> float:
    return res_per_turn(e["level"]) + e["hp"] * 0.5 + e["armor"]


def _alive(enemies: List[Dict]) -> List[Dict]:
    return [e for e in enemies if e["hp"] > 0]


# ─── Negotiate ───────────────────────────────────────────────────────

def negotiate(gid: int, turn: int, player: Dict, enemies: List[Dict],
              combat_actions: List[Dict]) -> List[Dict]:
    """
    Double-alliance strategy: ally with 2 strongest, both target the weakest.
    If under attack: rally non-attackers against the attacker.
    """
    my_id = player["playerId"]
    alive = _alive(enemies)

    # Record who attacked us from previous combat
    attackers_on_us = set()
    for ca in combat_actions:
        act = ca.get("action", {})
        if act.get("targetId") == my_id:
            attackers_on_us.add(ca["playerId"])
            memory._get(gid)["agg"][ca["playerId"]] += act.get("troopCount", 0)

    if len(alive) < 2:
        return []

    proposals = []
    used = set()
    sorted_alive = sorted(alive, key=_strength, reverse=True)
    weakest = min(alive, key=lambda e: e["hp"] + e["armor"])

    # RETALIATION MODE: if attacked, rally others against attacker
    if attackers_on_us:
        attacker_enemies = [e for e in alive if e["playerId"] in attackers_on_us]
        main_attacker = max(attacker_enemies, key=_strength) if attacker_enemies else None
        if main_attacker:
            for c in sorted(
                [e for e in alive if e["playerId"] not in attackers_on_us],
                key=_strength, reverse=True
            )[:2]:
                if c["playerId"] not in used:
                    proposals.append({
                        "allyId": c["playerId"],
                        "attackTargetId": main_attacker["playerId"]
                    })
                    used.add(c["playerId"])

    # DEFAULT: double-alliance against weakest
    if not proposals:
        for c in sorted_alive:
            if c["playerId"] != weakest["playerId"] and c["playerId"] not in used:
                proposals.append({
                    "allyId": c["playerId"],
                    "attackTargetId": weakest["playerId"]
                })
                used.add(c["playerId"])
                if len(proposals) >= 2:
                    break

    memory.set_our_allies(gid, used)
    return proposals


# ─── Combat ──────────────────────────────────────────────────────────

def combat(gid: int, turn: int, player: Dict, enemies: List[Dict],
           diplomacy: List[Dict], previous_attacks: List[Dict]) -> List[Dict]:
    """
    Priority: Upgrade → Armor → Attack (focus fire on best target).
    """
    my_id = player["playerId"]
    resources = player["resources"]
    hp = player["hp"]
    current_armor = player["armor"]
    level = player["level"]
    alive = _alive(enemies)

    if not alive or resources <= 0:
        return []

    # ── INTEL ──
    memory.record_attacks_on_us(gid, turn, my_id, previous_attacks)
    memory.record_diplomacy_to_us(gid, turn, diplomacy, my_id)

    incoming = 0
    attacker_ids = set()
    for pa in previous_attacks:
        act = pa.get("action", {})
        if act.get("targetId") == my_id:
            incoming += act.get("troopCount", 0)
            attacker_ids.add(pa["playerId"])

    our_allies = set()
    coordinated_targets = set()
    for d in diplomacy:
        act = d.get("action", {})
        if act.get("allyId") == my_id:
            our_allies.add(d["playerId"])
            t = act.get("attackTargetId")
            if t:
                coordinated_targets.add(t)

    actions = []
    avail = resources

    # ── 1. UPGRADE ──
    if level < MAX_LEVEL:
        cost = upg_cost(level)
        gain = res_per_turn(level + 1) - res_per_turn(level)
        remaining = max(1, FATIGUE_TURN - turn + 5)
        payback = cost / gain if gain > 0 else 999

        do_upgrade = (
            avail >= cost + 5 and
            payback < remaining * 0.7 and
            not (hp < 35 and incoming > 15)
        )
        # Force upgrade early if affordable
        if turn <= 4 and avail >= cost:
            do_upgrade = True

        if do_upgrade:
            actions.append({"type": "upgrade"})
            avail -= cost

    if avail <= 0:
        return _validate(actions, resources)

    # ── 2. ARMOR ──
    armor_amt = 0
    if incoming > 0:
        # Predict ~70% of last incoming, subtract existing armor
        desired = max(0, int(incoming * 0.7) - current_armor)
        armor_amt = min(desired, int(avail * 0.4))
    elif hp < 50:
        armor_amt = min(15, int(avail * 0.25))
    elif hp < 70 and len(alive) >= 2:
        armor_amt = min(8, int(avail * 0.15))

    if turn >= FATIGUE_TURN:
        armor_amt = min(armor_amt, int(avail * 0.1))

    if armor_amt > 0:
        actions.append({"type": "armor", "amount": armor_amt})
        avail -= armor_amt

    if avail <= 0:
        return _validate(actions, resources)

    # ── 3. ATTACK ──
    def score(e):
        pid = e["playerId"]
        s = 0.0
        eff_hp = e["hp"] + e["armor"]

        # KILL BONUS
        if eff_hp <= avail:
            s += 500
        # Coordinated target
        if pid in coordinated_targets:
            s += 80
        # Retaliation
        if pid in attacker_ids:
            s += 60
        s += memory.agg(gid, pid) * 0.3
        # Betrayal
        s += memory.betrayals(gid, pid) * 100
        # Vulnerability
        s += max(0, 100 - e["hp"])
        # Danger
        s += e["level"] * 15
        # Armor waste
        s -= e["armor"] * 0.8
        # Alliance respect (early/mid game)
        if pid in our_allies and memory.betrayals(gid, pid) == 0:
            if turn < 15:
                s -= 200
            elif turn < 22:
                s -= 50
        return s

    targets = sorted(alive, key=score, reverse=True)
    attacked = set()

    for t in targets:
        if avail <= 0 or len(attacked) >= 2:
            break
        tid = t["playerId"]
        if tid in attacked:
            continue
        # Don't attack respected allies unless they're the only target
        if score(t) < 0 and len(alive) > 1:
            continue

        eff_hp = t["hp"] + t["armor"]

        # Can kill? Use exact amount
        if eff_hp <= avail:
            troops = eff_hp
        elif score(t) > 100:
            troops = int(avail * 0.7) if len(attacked) == 0 else avail
        elif len(targets) == 1 or len(attacked) == 1:
            troops = avail
        else:
            troops = int(avail * 0.6)

        troops = max(1, min(troops, avail))
        actions.append({"type": "attack", "targetId": tid, "troopCount": troops})
        avail -= troops
        attacked.add(tid)

    return _validate(actions, resources)


def _validate(actions: List[Dict], total_resources: int) -> List[Dict]:
    """Ensure no invalid actions that would cause entire response rejection."""
    armor_count = 0
    upgrade_count = 0
    attack_targets = set()
    total_cost = 0
    clean = []

    for a in actions:
        t = a.get("type")
        if t == "armor":
            if armor_count >= 1 or a.get("amount", 0) <= 0:
                continue
            armor_count += 1
            total_cost += a["amount"]
        elif t == "upgrade":
            if upgrade_count >= 1:
                continue
            upgrade_count += 1
            # Cost already deducted in logic
        elif t == "attack":
            tid = a.get("targetId")
            tc = a.get("troopCount", 0)
            if tid in attack_targets or tc <= 0:
                continue
            attack_targets.add(tid)
            total_cost += tc
        else:
            continue
        clean.append(a)

    return clean
