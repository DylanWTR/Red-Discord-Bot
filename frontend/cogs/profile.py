import discord
from discord import app_commands
from discord.ext import commands
from io import BytesIO
from backend.models.user_model import UserModel
from config.ranks import RANGES_VALUES
from config.emojis import EMOJI_LOGO, EMOJI_COLOR, EMOJI_ARTWORK

class Profile(commands.Cog):
    def __init__(self, bot: commands.Bot, user_model: UserModel):
        self.bot = bot
        self.user_model = user_model
        self.cache_cog = self.bot.get_cog("Cache")

        self.matching_role = None
        self.total_points = "0"
        self.start_dungeons = "0"
        self.early_dungeons = "0"
        self.mid_dungeons = "0"
        self.late_dungeons = "0"
        self.end_dungeons = "0"
        self.rank = "Unranked"
        self.thumbnail = None
        self.image = None

    @app_commands.command(name="profil", description="Affiche le profil d'un utilisateur.")
    async def profile(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        user_document = await self.fetch_user_document(interaction, member)
        if not user_document:
            return

        self.populate_fields(user_document)
        await self.prepare_images(interaction, member)

        embed = await self.create_profile_embed(member)
        await self.send_embed(interaction, embed)

    async def fetch_user_document(self, interaction: discord.Interaction, member: discord.Member):
        """Fetch the user document from the database."""
        user_document = await self.user_model.get_user(member.id)
        if not user_document:
            await interaction.response.send_message(
                f"{member.mention} does not have a profile yet. Please contact an admin.",
                ephemeral=True
            )
        return user_document

    def populate_fields(self, user_document):
        """Populate the embed fields from the user document."""
        stats = user_document.get("stats", {})
        points = stats.get("points", {})
        self.total_points = str(points.get("total", 0))
        self.start_dungeons = int(points.get("1-50", 0))
        self.early_dungeons = int(points.get("51-100", 0))
        self.mid_dungeons = int(points.get("101-150", 0))
        self.late_dungeons = int(points.get("151-200", 0))
        self.end_dungeons = int(points.get("200+", 0))
        self.rank = stats.get("rank", "Unranked")

        completions = stats.get("completions", [])
        self.completions = completions if completions else [0] * 128

    async def prepare_images(self, interaction: discord.Interaction, member: discord.Member):
        """Retrieve and cache thumbnail and rank images."""
        self.matching_role = self.get_matching_role(member)

        self.thumbnail = self.cache_cog.avatar_cache.get(f"{self.matching_role}.png")
        if not self.thumbnail:
            await interaction.response.send_message(
                f"Avatar image for role '{self.matching_role}' not found. Please contact an admin.",
                ephemeral=True
            )
            return

        self.image = self.cache_cog.rank_cache.get(f"{self.rank}.png")
        if not self.image:
            await interaction.response.send_message(
                f"Rank image for rank '{self.rank}' not found. Please contact an admin.",
                ephemeral=True
            )

    def create_progress_bar(self, current_value, max_value):
        """Generate a balanced progress bar with 50% on each side."""
        percentage = (current_value / max_value) * 100

        left_percentage = min(percentage, 50)
        right_percentage = max(0, percentage - 50)

        left_blocks = int(left_percentage / 5)
        right_blocks = int(right_percentage / 5)

        left_bar = f"{'█' * left_blocks}{'░' * (10 - left_blocks)}"
        right_bar = f"{'█' * right_blocks}{'░' * (10 - right_blocks)}"

        return f"{left_bar} | {right_bar} {percentage:.0f}%"

    async def get_downs_in_range(self, start_index: int, end_index: int, member: discord.Member) -> int:
        """Calculate the total downs in a specific range of the completions array."""
        completions = await self.user_model.get_user_completions(member.id)
        return sum(completions[start_index:end_index + 1]) if completions else 0

    async def create_profile_embed(self, member: discord.Member):
        """Create the profile embed with updated field names and completion data."""
        class_logo = EMOJI_LOGO.get(self.matching_role.lower(), "") if self.matching_role else ""
        class_display = f"{class_logo} **{self.matching_role}**" if self.matching_role else "None"

        color_hex = EMOJI_COLOR.get(self.matching_role.lower(), "#3498db")
        embed_color = discord.Color(int(color_hex.strip("#"), 16))

        embed = discord.Embed(
            title=f"{member.display_name}",
            description=f"**Classe:** {class_display}",
            color=embed_color
        )

        embed.add_field(name='\u200B', value="\u200B", inline=False)
        embed.add_field(name="Points: ", value=self.total_points, inline=False)
        embed.add_field(name='\u200B', value="Nombres de Donjon Down :", inline=False)

        embed.add_field(name=f"▁▁▁▁▁▁▁001 à 050 ▁▁▁▁▁▁▁ kill : {await self.get_downs_in_range(0, 16, member)}",value=self.create_progress_bar(self.start_dungeons, RANGES_VALUES["1-50"] * 2),inline=False)
        embed.add_field(name=f"▁▁▁▁▁▁▁051 à 100 ▁▁▁▁▁▁▁ kill : {await self.get_downs_in_range(17, 42, member)}",value=self.create_progress_bar(self.early_dungeons, RANGES_VALUES["51-100"] * 2),inline=False)
        embed.add_field(name=f"▁▁▁▁▁▁▁100 à 150 ▁▁▁▁▁▁▁ kill : {await self.get_downs_in_range(43, 70, member)}",value=self.create_progress_bar(self.mid_dungeons, RANGES_VALUES["101-150"] * 2),inline=False)
        embed.add_field(name=f"▁▁▁▁▁▁▁ 151 à 200 ▁▁▁▁▁▁▁ kill : {await self.get_downs_in_range(71, 106, member)}",value=self.create_progress_bar(self.late_dungeons, RANGES_VALUES["151-200"] * 2),inline=False)
        embed.add_field(name=f"▁▁▁▁▁▁▁▁▁200+ ▁▁▁▁▁▁▁▁ kill : {await self.get_downs_in_range(107, 127, member)}",value=self.create_progress_bar(self.end_dungeons, RANGES_VALUES["200+"] * 2),inline=False)
        embed.add_field(name="Rank", value=self.rank, inline=False)
        return embed

    async def send_embed(self, interaction: discord.Interaction, embed: discord.Embed):
        """Send the embed to the user."""
        thumbnail_file = self.image_to_file(self.thumbnail, "thumbnail.png")
        embed.set_thumbnail(url=f"attachment://thumbnail.png")

        rank_file = self.image_to_file(self.image, "rank.png")
        embed.set_image(url=f"attachment://rank.png")

        await interaction.response.send_message(embed=embed, files=[thumbnail_file, rank_file])

    def get_matching_role(self, member: discord.Member):
        """Find the first role matching a key in `classes` (case-insensitive)."""
        class_keys_lower = {key.lower(): key for key in EMOJI_ARTWORK}
        for role in member.roles:
            role_name_lower = role.name.lower()
            if role_name_lower in class_keys_lower:
                return class_keys_lower[role_name_lower]
        return None

    @staticmethod
    def image_to_file(image, filename):
        """Convert an image to a Discord file."""
        if not image:
            return None
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return discord.File(fp=buffer, filename=filename)
