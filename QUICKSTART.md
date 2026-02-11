# ⚡ Quick Start Guide

Get your Kingdom Wars bot running in 2 minutes!

## 🚀 Local Setup (Development)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the bot
python server.py
```

Server starts on `http://localhost:8000`

---

## 🐋 Docker Setup (Production)

```bash
# 1. Build image
docker build -t apex-predator .

# 2. Run container
docker run -d -p 8000:8000 --name kw-bot apex-predator

# 3. Check logs
docker logs -f kw-bot

# 4. Stop bot
docker stop kw-bot
```

---

## ✅ Verify Installation

```bash
# Health check
curl http://localhost:8000/healthz
# Expected: {"status":"OK"}

# Bot info
curl http://localhost:8000/info
# Expected: {"name":"Apex Predator","strategy":"AI-trapped-strategy","version":"2.0"}
```

---

## 🧪 Run Tests

```bash
python test_bot.py
```

All tests should pass ✓

---

## 📝 Game Server Configuration

Point your Kingdom Wars game server to:
```
http://your-server-ip:8000
```

Required endpoints:
- `GET /healthz` - Health check
- `GET /info` - Bot metadata
- `POST /negotiate` - Diplomacy phase
- `POST /combat` - Action phase

---

## 🔧 Configuration

### Change Team Name
Edit `server.py`:
```python
TEAM_NAME = "Your Team Name Here"
```

### Adjust Workers (for high traffic)
Edit `server.py`:
```python
uvicorn.run("server:app", workers=4)  # Default: 2
```

### Change Port
```bash
# Method 1: Edit server.py
uvicorn.run("server:app", port=9000)

# Method 2: Docker
docker run -p 9000:8000 apex-predator
```

---

## 📊 Monitor Performance

```bash
# View real-time logs
tail -f /var/log/kw-bot.log

# Docker logs
docker logs -f kw-bot

# Check for errors
grep ERROR /var/log/kw-bot.log
```

---

## 🐛 Troubleshooting

### Bot not responding?
```bash
# Check if running
curl http://localhost:8000/healthz

# Restart
docker restart kw-bot
```

### Port already in use?
```bash
# Find process
lsof -i :8000

# Kill it
kill -9 <PID>
```

### Out of memory?
```bash
# Check memory
docker stats kw-bot

# Restart with limit
docker run -m 512m -p 8000:8000 apex-predator
```

---

## 📁 Project Files

```
.
├── server.py              # FastAPI server (start here)
├── strategy.py            # Bot intelligence
├── models.py              # Data models
├── requirements.txt       # Dependencies
├── Dockerfile            # Container config
├── test_bot.py           # Test suite
├── README.md             # Full documentation
└── STRATEGY_ANALYSIS.md  # Strategy deep-dive
```

---

## 🎮 Play Against AI

Want to test locally? Create a simple game simulator:

```python
# simulator.py
import requests
import json

def simulate_turn():
    # Negotiate
    neg_result = requests.post("http://localhost:8000/negotiate", json={
        "gameId": 1,
        "turn": 1,
        "playerTower": {"playerId": 1, "hp": 100, "armor": 0, "resources": 20, "level": 1},
        "enemyTowers": [{"playerId": 2, "hp": 100, "armor": 0, "level": 1}],
        "combatActions": []
    })
    print("Diplomacy:", neg_result.json())
    
    # Combat
    combat_result = requests.post("http://localhost:8000/combat", json={
        "gameId": 1,
        "turn": 1,
        "playerTower": {"playerId": 1, "hp": 100, "armor": 0, "resources": 20, "level": 1},
        "enemyTowers": [{"playerId": 2, "hp": 100, "armor": 0, "level": 1}],
        "diplomacy": [],
        "previousAttacks": []
    })
    print("Actions:", combat_result.json())

simulate_turn()
```

---

## 🏆 Ready to Deploy!

Your bot is now ready for tournament play.

**Performance Checklist:**
- ✅ Health endpoint responds
- ✅ All tests pass
- ✅ Logs show `[KW-BOT] Mega ogudor`
- ✅ Response time < 100ms
- ✅ No crashes under load

**Next Steps:**
1. Deploy to cloud (AWS/GCP/Azure)
2. Point game server to your bot
3. Monitor first few games
4. Adjust strategy if needed

---

## 💡 Pro Tips

1. **Load Testing**: Use `ab` or `wrk` to test throughput
   ```bash
   ab -n 1000 -c 10 http://localhost:8000/healthz
   ```

2. **Logging**: Check logs after each game to see decision-making
   ```bash
   grep "NEGOTIATE\|COMBAT" /var/log/kw-bot.log
   ```

3. **Memory**: Bot auto-cleans after 500 games, but restart weekly

4. **Scaling**: Use multiple workers for 100+ req/sec load

---

## 📞 Need Help?

Check these resources:
- `README.md` - Full documentation
- `STRATEGY_ANALYSIS.md` - Strategy explanation
- `test_bot.py` - Example usage
- Game rules in original document

---

**Happy Gaming! 🎮**

May your towers stand tall and your enemies fall swiftly! 🏰⚔️
