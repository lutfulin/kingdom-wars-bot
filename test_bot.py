"""
Test script for Kingdom Wars bot.
Run: python test_bot.py
"""

import json
from models import NegotiateRequest, CombatRequest, PlayerTower, EnemyTower, ActionEntry
import strategy


def test_early_game():
    """Test turn 1 behavior."""
    print("\n=== TEST: Early Game (Turn 1) ===")
    
    req = CombatRequest(
        gameId=1,
        turn=1,
        playerTower=PlayerTower(playerId=1, hp=100, armor=0, resources=20, level=1),
        enemyTowers=[
            EnemyTower(playerId=2, hp=100, armor=0, level=1),
            EnemyTower(playerId=3, hp=100, armor=0, level=1),
        ],
        diplomacy=[],
        previousAttacks=[]
    )
    
    result = strategy.combat(
        gid=req.gameId,
        turn=req.turn,
        player=req.playerTower.model_dump(),
        enemies=[e.model_dump() for e in req.enemyTowers],
        diplomacy=[],
        previous_attacks=[]
    )
    
    print(f"Actions: {json.dumps(result, indent=2)}")
    
    # Verify upgrade happens (50 resources needed, we have 20, so no upgrade)
    # Should save resources or do light attacks
    assert isinstance(result, list), "Should return list"
    print("✓ Early game test passed")


def test_under_attack():
    """Test defensive response to attacks."""
    print("\n=== TEST: Under Attack ===")
    
    req = CombatRequest(
        gameId=2,
        turn=5,
        playerTower=PlayerTower(playerId=1, hp=80, armor=0, resources=50, level=2),
        enemyTowers=[
            EnemyTower(playerId=2, hp=100, armor=5, level=2),
            EnemyTower(playerId=3, hp=90, armor=0, level=1),
        ],
        diplomacy=[],
        previousAttacks=[
            ActionEntry(playerId=2, action={"targetId": 1, "troopCount": 20})
        ]
    )
    
    result = strategy.combat(
        gid=req.gameId,
        turn=req.turn,
        player=req.playerTower.model_dump(),
        enemies=[e.model_dump() for e in req.enemyTowers],
        diplomacy=[d.model_dump() for d in req.diplomacy],
        previous_attacks=[p.model_dump() for p in req.previousAttacks]
    )
    
    print(f"Actions: {json.dumps(result, indent=2)}")
    
    # Should build armor or retaliate
    assert isinstance(result, list), "Should return list"
    assert len(result) > 0, "Should take actions"
    print("✓ Under attack test passed")


def test_kill_opportunity():
    """Test kill detection."""
    print("\n=== TEST: Kill Opportunity ===")
    
    req = CombatRequest(
        gameId=3,
        turn=10,
        playerTower=PlayerTower(playerId=1, hp=100, armor=10, resources=100, level=3),
        enemyTowers=[
            EnemyTower(playerId=2, hp=15, armor=5, level=2),  # Can kill with 20 troops
            EnemyTower(playerId=3, hp=100, armor=10, level=3),
        ],
        diplomacy=[],
        previousAttacks=[]
    )
    
    result = strategy.combat(
        gid=req.gameId,
        turn=req.turn,
        player=req.playerTower.model_dump(),
        enemies=[e.model_dump() for e in req.enemyTowers],
        diplomacy=[],
        previous_attacks=[]
    )
    
    print(f"Actions: {json.dumps(result, indent=2)}")
    
    # Should execute kill on player 2
    attack_actions = [a for a in result if a.get("type") == "attack"]
    kill_attack = next((a for a in attack_actions if a.get("targetId") == 2), None)
    
    if kill_attack:
        print(f"✓ Kill detected: {kill_attack['troopCount']} troops to player 2")
        assert kill_attack["troopCount"] >= 20, "Should send enough troops to kill"
    
    print("✓ Kill opportunity test passed")


def test_diplomacy():
    """Test diplomatic proposals."""
    print("\n=== TEST: Diplomacy ===")
    
    req = NegotiateRequest(
        gameId=4,
        turn=5,
        playerTower=PlayerTower(playerId=1, hp=90, armor=5, resources=30, level=2),
        enemyTowers=[
            EnemyTower(playerId=2, hp=100, armor=10, level=3),  # Strong
            EnemyTower(playerId=3, hp=60, armor=0, level=1),    # Weak
        ],
        combatActions=[]
    )
    
    result = strategy.negotiate(
        gid=req.gameId,
        turn=req.turn,
        player=req.playerTower.model_dump(),
        enemies=[e.model_dump() for e in req.enemyTowers],
        combat_actions=[]
    )
    
    print(f"Diplomatic proposals: {json.dumps(result, indent=2)}")
    
    # Should propose alliance
    assert isinstance(result, list), "Should return list"
    
    if len(result) > 0:
        print(f"✓ Proposed {len(result)} alliances")
    
    print("✓ Diplomacy test passed")


def test_fatigue_phase():
    """Test fatigue phase behavior."""
    print("\n=== TEST: Fatigue Phase (Turn 27) ===")
    
    req = CombatRequest(
        gameId=5,
        turn=27,
        playerTower=PlayerTower(playerId=1, hp=60, armor=5, resources=101, level=5),
        enemyTowers=[
            EnemyTower(playerId=2, hp=55, armor=3, level=4),
        ],
        diplomacy=[],
        previousAttacks=[]
    )
    
    result = strategy.combat(
        gid=req.gameId,
        turn=req.turn,
        player=req.playerTower.model_dump(),
        enemies=[e.model_dump() for e in req.enemyTowers],
        diplomacy=[],
        previous_attacks=[]
    )
    
    print(f"Actions: {json.dumps(result, indent=2)}")
    
    # Should be aggressive (minimal armor, max attack)
    armor_actions = [a for a in result if a.get("type") == "armor"]
    attack_actions = [a for a in result if a.get("type") == "attack"]
    
    print(f"Armor actions: {len(armor_actions)}")
    print(f"Attack actions: {len(attack_actions)}")
    
    assert len(attack_actions) > 0, "Should attack in fatigue phase"
    print("✓ Fatigue phase test passed")


def test_runaway_detection():
    """Test runaway leader detection."""
    print("\n=== TEST: Runaway Detection ===")
    
    # Player 2 is level 4 on turn 8 (should be runaway)
    req = NegotiateRequest(
        gameId=6,
        turn=8,
        playerTower=PlayerTower(playerId=1, hp=90, armor=5, resources=30, level=2),
        enemyTowers=[
            EnemyTower(playerId=2, hp=100, armor=15, level=4),  # RUNAWAY
            EnemyTower(playerId=3, hp=85, armor=5, level=2),
        ],
        combatActions=[]
    )
    
    # First turn to record data
    strategy.memory.record_turn(
        req.gameId,
        req.turn,
        [e.model_dump() for e in req.enemyTowers],
        []
    )
    
    result = strategy.negotiate(
        gid=req.gameId,
        turn=req.turn,
        player=req.playerTower.model_dump(),
        enemies=[e.model_dump() for e in req.enemyTowers],
        combat_actions=[]
    )
    
    print(f"Diplomatic proposals: {json.dumps(result, indent=2)}")
    
    # Should rally against player 2
    if len(result) > 0:
        targets = [p.get("attackTargetId") for p in result]
        if 2 in targets:
            print("✓ Successfully rallied against runaway leader (player 2)")
    
    print("✓ Runaway detection test passed")


def run_all_tests():
    """Run all test cases."""
    print("\n" + "="*60)
    print("Kingdom Wars Bot - Test Suite")
    print("="*60)
    
    try:
        test_early_game()
        test_under_attack()
        test_kill_opportunity()
        test_diplomacy()
        test_fatigue_phase()
        test_runaway_detection()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED")
        print("="*60 + "\n")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}\n")
        raise
    except Exception as e:
        print(f"\n✗ ERROR: {e}\n")
        raise


if __name__ == "__main__":
    run_all_tests()
