# 🗂️ File Store Bot — Setup Guide

## ✅ Features
- 🗂️ Buy Files with coins (Text, Document, Link)
- 🪙 Coin System
- 🔗 Referral System (earn coins per referral)
- 🏆 Leaderboard
- 🎁 Redeem Code System
- 📞 Contact Owner
- 👑 Admin Panel:
  - ➕ Add / 🗑️ Remove Files
  - 🎫 Create Redeem Codes
  - 💰 Give Coins to users
  - 👥 View all users
  - 📢 Broadcast to all users
  - 📊 Bot Statistics

---

## 🚀 Setup in 3 Steps

### Step 1 — Install requirements
```bash
pip install -r requirements.txt
```

### Step 2 — Edit config.py
```python
BOT_TOKEN      = "Your BotFather token"
BOT_NAME       = "Your Bot Name"
ADMIN_IDS      = ["Your Telegram User ID"]
OWNER_USERNAME = "your_telegram_username"
REFERRAL_COINS = 5
```

### Step 3 — Run the bot
```bash
python bot.py
```

---

## 👑 Admin Panel Buttons

| Button | Function |
|--------|----------|
| ➕ Add File | Add a new file (name, price, content) |
| 🗑️ Remove File | Delete a file |
| 🎫 Create Redeem Code | Generate a code with coin reward |
| 💰 Give Coins | Send coins to any user |
| 📢 Broadcast | Message all users at once |
| 📊 Bot Stats | View usage statistics |
| 👥 All Users | See full user list with balances |

---

## 📝 How to Add a File

1. Open the bot as admin
2. Tap **➕ Add File**
3. Enter the **name**
4. Enter the **price** in coins
5. Send the content:
   - **Text / Link** → Type or paste it
   - **Document / File** → Upload it directly

---

## 🪙 How Users Earn Coins
- 🔗 Share referral link → earn coins per new user
- 🎁 Use a redeem code → earn the code's coin reward
- Admin manually gives coins via 💰 Give Coins

---

## 💡 Tips
- Add multiple admins in config.py:
  ```python
  ADMIN_IDS = ["123456789", "987654321"]
  ```
- Find your Telegram ID: message @userinfobot
- Get a bot token: message @BotFather → /newbot
