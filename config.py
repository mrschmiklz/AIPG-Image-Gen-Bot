import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
API_BASE_URL = os.getenv('API_ENDPOINT')
API_KEY = os.getenv('AI_POWER_GRID_API_KEY')

HEADERS = {
    "accept": "application/json",
    "apikey": API_KEY,
    "Client-Agent": "DiscordBot:1.0:test",
    "Content-Type": "application/json"
}