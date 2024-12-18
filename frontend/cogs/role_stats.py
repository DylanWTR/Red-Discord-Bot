import discord
from discord.ext import commands, tasks
from config.settings import STATS_CHANNEL_ID, STATS_MESSAGE_ID
from config.emojis import EMOJI_LOGO


class RoleStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_stats.start()

    def cog_unload(self):
        self.update_stats.cancel()

    @tasks.loop(minutes=10)
    async def update_stats(self):
        channel = self.bot.get_channel(STATS_CHANNEL_ID)
        if not channel:
            print("Le canal n'a pas été trouvé.")
            return

        embed = discord.Embed(
            title="Grimoire des Classes",
            description="",
            color=0xbc0001
        )
        embed.set_thumbnail(url="https://i.imgur.com/MjkLQMa.png")
        embed.set_image(url="https://i.imgur.com/FmE3f3m.jpeg")
        embed.set_footer(text="Red", icon_url="https://i.imgur.com/yRoCSrD.png")

        emoji_logo_lower = {k.lower(): v for k, v in EMOJI_LOGO.items()}

        for role_name in EMOJI_LOGO.keys():
            role_name_lower = role_name.lower()
            emoji = emoji_logo_lower.get(role_name_lower, '')

            role = next(
                (r for r in channel.guild.roles if r.name.lower() == role_name_lower),
                None
            )
            if role:
                members_count = len(role.members)
                embed.description += f"{emoji} **{role.name}**: {members_count}\n"
            else:
                embed.description += f"{emoji} **{role_name}**: Rôle non trouvé\n"

        global STATS_MESSAGE_ID

        if STATS_MESSAGE_ID:
            try:
                message = await channel.fetch_message(STATS_MESSAGE_ID)
                await message.edit(embed=embed)
            except discord.NotFound:
                STATS_MESSAGE_ID = 0
                print("Message non trouvé. Réinitialisation de STATS_MESSAGE_ID.")
        if not STATS_MESSAGE_ID:
            try:
                message = await channel.send(embed=embed)
                STATS_MESSAGE_ID = message.id
                print("Nouvel embed créé et STATS_MESSAGE_ID mis à jour.")
            except Exception as e:
                print(f"Échec de la création du nouvel embed : {e}")

    @update_stats.before_loop
    async def before_update_stats(self):
        await self.bot.wait_until_ready()
