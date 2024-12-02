import discord
from discord.ext import commands

class ReactionRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rules_channel_id = 1311626083799535648
        self.rules_message_id = 1312379145484767285
        self.initial_role_id = 1312483519267602552
        self.new_role_id = 1312483623349391401
        self.reaction_emoji = '✅'

    async def manage_roles(self, member: discord.Member, action: str):
        """Manage roles for a member based on the specified action."""
        guild = member.guild
        initial_role = guild.get_role(self.initial_role_id)
        new_role = guild.get_role(self.new_role_id)

        if not initial_role or not new_role:
            return

        if action == "add":
            if initial_role in member.roles:
                await member.remove_roles(initial_role, reason="Accepted rules.")
                await member.add_roles(new_role, reason="Accepted rules.")
        elif action == "remove":
            if new_role in member.roles:
                await member.add_roles(initial_role, reason="Reaction removed.")
                await member.remove_roles(new_role, reason="Reaction removed.")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Handle reaction add events."""
        if (payload.message_id == self.rules_message_id
                and payload.channel_id == self.rules_channel_id
                and str(payload.emoji) == self.reaction_emoji):
            guild = self.bot.get_guild(payload.guild_id)
            if not guild:
                return

            member = guild.get_member(payload.user_id)
            if member and not member.bot:
                await self.manage_roles(member, action="add")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """Handle reaction remove events."""
        if (payload.message_id == self.rules_message_id
                and payload.channel_id == self.rules_channel_id
                and str(payload.emoji) == self.reaction_emoji):
            guild = self.bot.get_guild(payload.guild_id)
            if not guild:
                return

            member = guild.get_member(payload.user_id)
            if member and not member.bot:
                await self.manage_roles(member, action="remove")
