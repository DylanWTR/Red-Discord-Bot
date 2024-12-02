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

        completions_array = [0] * 131

        user_data = {
            "user_id": user_id,
            "username": username,
            "stats": {
                "points": {
                    "total": 0,
                    "1-50": 0,
                    "51-100": 0,
                    "101-150": 0,
                    "151-200": 0,
                    "200+": 0,
                },
                "rank": "Unranked",
                "completions": completions_array,
            },
            "undo": {
                "total": 0,
                "1-50": 0,
                "51-100": 0,
                "101-150": 0,
                "151-200": 0,
                "200+": 0,
                "completion_index": 0,
            }
        }

        try:
            await self._users_collection.insert_one(user_data)
            print(f"User: <{username}:{user_id}> added to the database.")
            return True
        except Exception as e:
            print(f"Error creating user <{username}:{user_id}>: {e}")
            return False

    async def update_user_stats(self, user_id: int, stats_update: dict) -> bool:
        """Updates the stats for a user."""
        try:
            stats_fields = {f"stats.{key}": value for key, value in stats_update.items() if key != "undo"}
            root_fields = {key: value for key, value in stats_update.items() if key == "undo"}

            update_query = {"$set": {**stats_fields, **root_fields}}

            result = await self._users_collection.update_one(
                {"user_id": user_id},
                update_query
            )

            if result.modified_count > 0:
                print(f"Updated stats for user {user_id}")
                return True
            else:
                print(f"No stats updated for user {user_id}.")
                return False
        except Exception as e:
            print(f"Error updating stats for user {user_id}: {e}")
            return False

    async def get_user_completions(self, user_id: int) -> list[int]:
        """
        Retrieve the 'completions' array for a specific user.
        If the user or completions data is missing, return an array of 128 zeros.
        """
        try:
            user_document = await self.get_user(user_id)
            if not user_document:
                print(f"User with ID {user_id} not found.")
                return [0] * 128

            completions = user_document.get("stats", {}).get("completions", [])
            if not completions:
                print(f"No completions data found for user with ID {user_id}.")
                return [0] * 128

            return completions
        except Exception as e:
            print(f"Error retrieving completions for user {user_id}: {e}")
            return [0] * 128
