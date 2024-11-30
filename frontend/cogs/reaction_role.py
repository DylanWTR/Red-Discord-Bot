import discord
from discord.ext import commands
from config.settings import REACTION_ROLE_CHANNEL_ID, REACTION_ROLE_EMOJI_ID

class ReactionRole(commands.Cog):
    """Cog to manage reaction-based role assignment."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Handles reaction events to update roles."""
        if payload.channel_id != REACTION_ROLE_CHANNEL_ID:
            return
        if str(payload.emoji) != REACTION_ROLE_EMOJI_ID:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        member = guild.get_member(payload.user_id)
        if not member or member.bot:
            return

        check_up_role_name = "Check-Up"
        invite_role_name = "Invité"

        check_up_role = discord.utils.get(guild.roles, name=check_up_role_name)
        invite_role = discord.utils.get(guild.roles, name=invite_role_name)

        try:
            if check_up_role in member.roles:
                await member.remove_roles(check_up_role)
                print(f"Removed '{check_up_role_name}' role from {member.name}.")

            if invite_role:
                await member.add_roles(invite_role)
                print(f"Added '{invite_role_name}' role to {member.name}.")
            else:
                print(f"Role '{invite_role_name}' not found in the server.")
        except discord.Forbidden:
            print(f"Missing permissions to update roles for {member.name}.")
        except discord.HTTPException as e:
            print(f"Failed to update roles for {member.name}: {e}")
