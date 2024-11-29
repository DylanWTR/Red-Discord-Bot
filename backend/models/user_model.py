from backend.db import get_collection

class UserModel:
    def __init__(self):
        self._users_collection = get_collection("users")

    # GETTERS

    async def get_user(self, user_id: int) -> dict:
        """Retrieve a user's data asynchronously."""
        return await self._users_collection.find_one({"user_id": user_id})

    async def get_all_users(self) -> list[dict]:
        """Retrieve all users from the database."""
        try:
            users = await self._users_collection.find().to_list(length=None)
            return users
        except Exception as e:
            print(f"Error retrieving all users: {e}")
            return []

    # OTHERS

    async def create_user(self, user_id: int, username: str) -> bool:
        """Creates a new user profile if they don't exist."""
        if await self._users_collection.find_one({"user_id": user_id}):
            print(f"User {user_id} already exists.")
            return False

        user_data = {
            "user_id": user_id,
            "username": username,
            "stats": {
                "points": 0,
                "rank": "",
                "completions": {
                    "1-50": 0,
                    "51-100": 0,
                    "101-150": 0,
                    "151-199": 0,
                    "200": 0
                }
            }
        }

        try:
            await self._users_collection.insert_one(user_data)
            print(f"User: <{username}:{user_id}> added to the database.")
            return True
        except Exception as e:
            print(f"Error creating user <{username}:{user_id}>: {e}")
            return False
