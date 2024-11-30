import discord
from discord.ext import commands
from backend.models.user_model import UserModel

class UserManagement(commands.Cog):
    def __init__(self, bot: commands.Bot, user_model: UserModel):
        self.bot = bot
        self.user_model = user_model

    async def ensure_user_profile(self, user_id: int, username: str):
        """Checks if a user profile exists; if not, creates one."""
        if not await self.user_model.get_user(user_id):
            await self.user_model.create_user(user_id=user_id, username=username)

    async def ensure_profiles_from_database(self):
        """Ensures profiles exist for all members in the database."""
        all_members = []
        for guild in self.bot.guilds:
            for member in guild.members:
                if member.bot:
                    continue
                all_members.append(member)

        existing_users = await self.user_model.get_all_users()
        existing_user_ids = {user["user_id"] for user in existing_users}

        for member in all_members:
            if member.id not in existing_user_ids:
                await self.user_model.create_user(user_id=member.id, username=member.name)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Creates a profile and adds 'Check-Up' role when a user joins the server."""
        if member.bot:
            return

        await self.ensure_user_profile(member.id, member.name)

        check_up_role_name = "Check-Up"
        check_up_role = discord.utils.get(member.guild.roles, name=check_up_role_name)
        if check_up_role:
            try:
                await member.add_roles(check_up_role)
                print(f"Assigned 'Check-Up' role to {member.name}.")
            except discord.Forbidden:
                print(f"Missing permissions to assign roles to {member.name}.")
            except discord.HTTPException as e:
                print(f"Failed to assign 'Check-Up' role to {member.name}: {e}")
        else:
            print(f"Role '{check_up_role_name}' not found in the server.")
