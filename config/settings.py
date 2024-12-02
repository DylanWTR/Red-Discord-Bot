from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
MONGODB_URI = os.getenv("MONGODB_URI")

STATS_CHANNEL_ID = 1312511402384162878
STATS_MESSAGE_ID = 1312515649905361011