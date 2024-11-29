from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import MONGODB_URI

client = AsyncIOMotorClient(
    MONGODB_URI,
    maxPoolSize=10,
    minPoolSize=1,
    serverSelectionTimeoutMS=3000,
    connectTimeoutMS=2000,
)

db = client["Red"]

collections = {
    "users": db["users"],
}

async def setup_indexes():
    """Sets up necessary indexes for each collection to optimize query performance."""
    await collections["users"].create_index("user_id", unique=True)

def get_collection(name: str):
    """Fetches a collection by name."""
    return collections.get(name)
