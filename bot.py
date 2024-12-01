import discord
from discord.ext import commands
from config.settings import TOKEN
from config.emojis import EMOJI_ARTWORK

from backend.models.user_model import UserModel
from frontend.cogs.cache import Cache
from frontend.cogs.users import UserManagement
from frontend.cogs.profile import Profile
from frontend.cogs.dungeon import Dungeon
from frontend.cogs.undo import Undo
from frontend.cogs.reaction_role import ReactionRole
from frontend.cogs.role_stats import RoleStats

class RedBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents(
            guilds=True,
            members=True,
            messages=True,
            message_content=True,
            reactions=True
            )
        super().__init__(command_prefix="$", intents=intents)
        self.shared_user_model = UserModel()

    async def setup_hook(self) -> None:
        """Sets up bot cogs and syncs command tree."""
        await self.add_cog(Cache(self))
        await self.add_cog(UserManagement(self, self.shared_user_model))
        await self.add_cog(Profile(self, self.shared_user_model, EMOJI_ARTWORK))
        await self.add_cog(Dungeon(self, self.shared_user_model))
        await self.add_cog(Undo(self, self.shared_user_model))
        await self.add_cog(ReactionRole(self))
        await self.add_cog(RoleStats(self))
        await self.tree.sync()

    async def on_ready(self) -> None:
        """Logs readiness and connection to Discord."""
        print(f"{self.user} is ready and connected to Discord!")

        cache_cog = self.get_cog("Cache")
        if cache_cog:
            await cache_cog.refresh_cache()
            print("Cache has been refreshed on startup.")

        user_cog = self.get_cog("UserManagement")
        if user_cog:
            await user_cog.ensure_profiles_from_database()
            print("User profiles have been ensured on startup.")

def main():
    bot = RedBot()
    bot.run(TOKEN)

if __name__ == "__main__":
    main()
