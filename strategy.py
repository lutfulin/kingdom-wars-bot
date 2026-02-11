"""
Kingdom Wars AI Strategy: "Adaptive Predator v3.0" (Final Apex)

Core Principles:
1. AGGRESSIVE GROWTH: Force upgrades Level 1->4 (compound interest).
2. TACTICAL DIPLOMACY: Double alliances, bluffing, and leader-rallying.
3. ADAPTIVE THREAT: Predicted damage based on top 2 active threats.
4. ROI ECONOMY: Only upgrade in mid-game if it pays back before fatigue/death.
5. FOCUS FIRE: Kill shot priority > Coordinated targets > Revenge.
"""

import math
from collections import defaultdict
from typing import List, Dict, Any, Set

FATIGUE_TURN = 25
MAX_LEVEL = 5


def res_per_turn(level: int) -> int:
    """Accurate game resources per level."""
    return int(round(20 * (1.5 ** (level - 1))))


def upg_cost(current_level: int) -> int:
    """Accurate upgrade costs per level."""
    return math.ceil(50 * (1.75 ** (current_level - 1)))


def fatigue_damage(turn: int) -> int:
    """Fatigue starts at 5 and grows by 5 each turn."""
    if turn <= FATIGUE_TURN: return 0
    return 5 * (turn - FATIGUE_TURN)


# ─── Intelligence System ─────────────────────────────────────────────

class GameMemory:
    """Elite cross-turn memory with activity tracking."""

    def __init__(self):
        self._g: Dict[int, Dict[str, Any]] = {}

    def _get(self, gid: int) -> Dict[str, Any]:
        if gid not in self._g:
            self._g[gid] = {
                "agg": defaultdict(int),          # total troops sent at us
                "ally_turns": defaultdict(set),   # turns they allied with us
                "betrayals": defaultdict(int),    # attacked while allied
                "our_allies": set(),              # who we proposed peace to
                "active_turns": defaultdict(int), # last turn they attacked
            }
        return self._g[gid]

    def record_intel(self, gid: int, turn: int, my_id: int, prev_attacks: List[Dict]):
        g = self._get(gid)
        for pa in prev_attacks:
            act = pa.get("action", {}) or {}
            pid = int(pa["playerId"])
            target = act.get("targetId")
            troops = int(act.get("troopCount", 0) or 0)

            if troops > 0:
                g["active_turns"][pid] = turn
                if target == my_id:
                    g["agg"][pid] += troops
                    if (turn - 1) in g["ally_turns"].get(pid, set()):
                        g["betrayals"][pid] += 1
                        print(f"[INTEL] BETRAYAL detected! Player {pid} attacked us.")

    def record_diplomacy(self, gid: int, turn: int, diplomacy: List[Dict], my_id: int):
        g = self._get(gid)
        for d in diplomacy:
            act = d.get("action", {}) or {}
            if act.get("allyId") == my_id:
                g["ally_turns"][d["playerId"]].add(turn)

    def is_active(self, gid, pid, turn) -> bool:
        last = self._get(gid)["active_turns"].get(pid, 0)
        return (turn - last) <= 3

    def get_trust(self, gid, pid) -> float:
        g = self._get(gid)
        if g["betrayals"].get(pid, 0) > 0: return 0.0
        if pid in g["ally_turns"]: return 0.8
        return 0.5

    def set_our_allies(self, gid, ids): self._get(gid)["our_allies"] = set(ids)
    def get_our_allies(self, gid): return self._get(gid)["our_allies"]
    def cleanup(self):
        if len(self._g) > 500:
            for k in list(self._g.keys())[:-100]: del self._g[k]

memory = GameMemory()


# ─── Strategy Engine ─────────────────────────────────────────────────

def negotiate(gid: int, turn: int, player: Dict, enemies: List[Dict],
              combat_actions: List[Dict]) -> List[Dict]:
    """
    Intelligent Hybrid Diplomacy.
    - Rally against runaway leaders.
    - Divide & Conquer if we are leading.
    - Double Alliance with strongest reliable partners.
    """
    my_id = int(player["playerId"])
    alive = [e for e in enemies if int(e.get("hp", 0)) > 0]
    memory.record_intel(gid, turn, my_id, combat_actions)
    
    if len(alive) < 2: return []

    def strength(e): return res_per_turn(int(e["level"])) + int(e["hp"])*0.5
    sorted_enemies = sorted(alive, key=strength, reverse=True)
    leader = sorted_enemies[0]
    weakest = sorted_enemies[-1]
    
    # 1) BLUFFING/STALLING: If someone is way stronger than us, ally with them
    # to keep them from hitting us while we catch up.
    is_leader = strength(player) > strength(leader)
    
    proposals = []
    if not is_leader and strength(leader) > strength(player) * 1.5:
        # We are underdogs - ally with the leader as a "shield"
        proposals.append({"allyId": leader["playerId"], "attackTargetId": weakest["playerId"]})
        print(f"[DIPLO] Bluffing alliance with leader {leader['playerId']}")

    # 2) RALLY: If not lead, rally non-leading players against the leader
    if not is_leader and not proposals:
        for e in sorted_enemies[1:3]: # 2nd and 3rd strongest
            proposals.append({"allyId": e["playerId"], "attackTargetId": leader["playerId"]})
            print(f"[DIPLO] Rallying {e['playerId']} against leader {leader['playerId']}")

    # 3) DEFAULT: Double alliance against weakest
    if not proposals:
        for e in sorted_enemies[:2]:
            if e["playerId"] != weakest["playerId"]:
                proposals.append({"allyId": e["playerId"], "attackTargetId": weakest["playerId"]})

    # Dedup and limit
    dedup = {p["allyId"]: p for p in proposals}
    result = list(dedup.values())[:2]
    memory.set_our_allies(gid, [p["allyId"] for p in result])
    return result


def combat(gid: int, turn: int, player: Dict, enemies: List[Dict],
           diplomacy: List[Dict], previous_attacks: List[Dict]) -> List[Dict]:
    """
    Adaptive Predator Combat Engine.
    """
    my_id = int(player["playerId"])
    res = int(player["resources"])
    hp = int(player["hp"])
    arm = int(player["armor"])
    lvl = int(player["level"])
    alive = [e for e in enemies if int(e.get("hp", 0)) > 0]
    alive_ids = {int(e["playerId"]) for e in alive}

    if not alive or res <= 0: return []

    memory.record_intel(gid, turn, my_id, previous_attacks)
    memory.record_diplomacy(gid, turn, diplomacy, my_id)

    # 1. Threat Prediction (Top 2 Active)
    threats = []
    for e in alive:
        pid = int(e["playerId"])
        income = res_per_turn(int(e["level"]))
        est_res = income * 2.0 # Heuristic human stash
        t = est_res * 0.6 * (1.0 + int(e["level"])*0.1)
        if not memory.is_active(gid, pid, turn): t *= 0.2
        if any(d.get("action", {}).get("attackTargetId") == my_id for d in diplomacy if d["playerId"] == pid):
            t *= 1.8 # Declared hostile
        threats.append(t)
    
    threats.sort(reverse=True)
    predicted_dmg = sum(threats[:2]) * 1.1

    actions = []
    avail = res

    # 2. Economic Upgrade (Early Rush -> ROI Midgame)
    if lvl < MAX_LEVEL:
        cost = upg_cost(lvl)
        can_afford = avail >= cost + 5
        
        # Priority 1: Early rush (Turns 1-6)
        should_upg = (turn <= 5 and avail >= cost)
        
        # Priority 2: Mid-game ROI
        if not should_upg and turn < 18:
            gain = res_per_turn(lvl + 1) - res_per_turn(lvl)
            payback = cost / gain
            remaining = max(1, FATIGUE_TURN - turn + 5)
            if payback < remaining * 0.7 and (hp + arm - predicted_dmg) > 25:
                should_upg = True
        
        if should_upg and avail >= cost:
            actions.append({"type": "upgrade"})
            avail -= cost
            print(f"[STRATEGY] Upgrading to L{lvl+1}. Turn {turn}")

    # 3. Defensive Armor
    fatigue = fatigue_damage(turn)
    total_threat = predicted_dmg + fatigue
    hp_after = hp + arm - total_threat

    if hp_after < 40 and avail > 0:
        deficit = 50 - hp_after
        armor_bid = min(avail, max(0, int(deficit)))
        if armor_bid > 0:
            actions.append({"type": "armor", "amount": armor_bid})
            avail -= armor_bid

    # 4. Attack (Focus Fire)
    coordinated = set()
    for d in diplomacy:
        if d.get("action", {}).get("allyId") == my_id:
            target = d["action"].get("attackTargetId")
            if target: coordinated.add(int(target))

    our_allies = memory.get_our_allies(gid)

    def target_score(e):
        pid = int(e["playerId"])
        eff_hp = int(e["hp"]) + int(e["armor"])
        s = 0.0
        if eff_hp <= avail: s += 5000 # KILL SHOT
        if pid in coordinated: s += 500
        if pid in our_allies: s -= 1000 # Respect alliance
        if not memory.is_active(gid, pid, turn): s -= 800 # AFK Trap
        s += int(e["level"]) * 50
        s += memory._get(gid)["agg"][pid] * 0.5
        return s

    targets = sorted(alive, key=target_score, reverse=True)
    attacked = set()
    for t in targets:
        if avail <= 0 or len(attacked) >= 2: break
        tid = int(t["playerId"])
        priority = target_score(t)
        
        # REMOVED: restrictive skip.
        # Now we only skip if it's a very strong ally AND we have other targets.
        if priority < -1500 and len(alive) > 1: continue

        eff_hp = int(t["hp"]) + int(t["armor"])
        if eff_hp <= avail:
            troops = eff_hp
        elif priority > 1000:
            troops = int(avail * 0.8)
        else:
            troops = avail if len(attacked) == 0 else avail
            
        troops = max(1, min(int(troops), avail))
        print(f"[STRATEGY] Attacking {tid} with {troops} troops (Score: {priority})")
        actions.append({"type": "attack", "targetId": tid, "troopCount": troops})
        avail -= troops
        attacked.add(tid)

    return _validate(actions, res, lvl, alive_ids)


def _validate(actions: List[Dict], total_res: int, level: int, alive_ids: Set[int]) -> List[Dict]:
    armor_done, upg_done, spent, targets = False, False, 0, set()
    clean = []
    for a in actions:
        t = a.get("type")
        if t == "armor" and not armor_done:
            amt = int(a.get("amount", 0))
            if amt > 0 and spent + amt <= total_res:
                spent += amt; armor_done = True
                clean.append({"type": "armor", "amount": amt})
        elif t == "upgrade" and not upg_done:
            cost = upg_cost(level)
            if spent + cost <= total_res:
                spent += cost; upg_done = True
                clean.append({"type": "upgrade"})
        elif t == "attack":
            tid = int(a.get("targetId"))
            troops = int(a.get("troopCount", 0))
            if tid in alive_ids and tid not in targets and troops > 0 and spent + troops <= total_res:
                spent += troops; targets.add(tid)
                clean.append({"type": "attack", "targetId": tid, "troopCount": troops})
    return clean
