class Config:
    # ─── BOT SETTINGS ─────────────────────────────────────────────────────
    BOT_TOKEN = "8877499158:AAG4SkFTu4OPtDw04vkRjGPdXzBKum4EaI8"        # Get from @BotFather
    BOT_NAME  = "SAMRAT FILES BOT"          # Your bot's display name

    # ─── ADMIN SETTINGS ───────────────────────────────────────────────────
    ADMIN_IDS = [
        "7259626275",    # Your Telegram User ID (as string)
    ]

    # ─── OWNER CONTACT ────────────────────────────────────────────────────
    OWNER_USERNAME = "SamratTG"         # Without the @ symbol

    # ─── COIN SETTINGS ────────────────────────────────────────────────────
    REFERRAL_COINS     = 1   # Coins referrer earns per successful referral
    NEW_USER_REF_COINS = 2   # Bonus coins new user gets when joining via referral

    # ─── FORCE SUBSCRIBE CHANNELS ─────────────────────────────────────────
    # Users must join ALL channels below before using the bot
    FORCE_CHANNELS = [
        {"name": "SAMRAT CONFIG OFC",  "username": "SAMRAT_CONFIG_OFC"},
        {"name": "ARAFAT CODEX7",  "username": "ARAFAT_CODEX7"},
        {"name": "ARAFAT FLEX",    "username": "ARAFAT_FLEX"},
    ]
