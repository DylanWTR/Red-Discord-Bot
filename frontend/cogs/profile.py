import discord
from discord.ext import commands
from io import BytesIO
from PIL import Image
from backend.models.user_model import UserModel


class Profile(commands.Cog):
    def __init__(self, bot, user_model: UserModel, classes: dict):
        self.bot = bot
        self.user_model = user_model
        self.classes = classes
        self.cache_cog = self.bot.get_cog("Cache")

    @commands.command(name='profile')
    async def profile(self, ctx, member: discord.Member = None):
        """Display the profile of a user."""
        member = member or ctx.author

        user_document = await self.user_model.get_user(member.id)
        matching_role = self.get_matching_role(member)

        thumbnail_image = self.get_cached_image(ctx, self.cache_cog.avatar_cache, f"{matching_role}.png")
        if not thumbnail_image:
            return

        user_rank = user_document.get("stats", {}).get("rank")
        rank_image = self.get_cached_image(ctx, self.cache_cog.rank_cache, f"{user_rank}.png") if user_rank else None

        stats = user_document.get("stats", {})
        embed = self.create_profile_embed(member, stats, matching_role, user_rank)
        files = self.prepare_files(thumbnail_image, matching_role, rank_image, user_rank)

        await ctx.send(embed=embed, files=files)

    def get_matching_role(self, member: discord.Member):
        """Find the first role matching a key in `classes`."""
        return next((role.name for role in member.roles if role.name in self.classes), None)

    def get_cached_image(self, ctx, cache: dict, key: str):
        """Retrieve and scale an image from the cache."""
        image = cache.get(key)
        if not image:
            ctx.send(f"Image for '{key}' not found in the cache.")
            return None
        return self.scale_image(image)

    def scale_image(self, image: Image.Image, scale: int = 3) -> Image.Image:
        """Scale an image by the specified factor."""
        return image.resize((image.width * scale, image.height * scale), Image.Resampling.LANCZOS)

    def prepare_files(self, thumbnail_image: Image.Image, matching_role: str, rank_image: Image.Image, user_rank: str):
        """Prepare image files for sending with the embed."""
        return [
            self.image_to_file(thumbnail_image, f"{matching_role}.png"),
            self.image_to_file(rank_image, f"{user_rank}.png") if rank_image else None
        ]

    @staticmethod
    def image_to_file(image: Image.Image, filename: str):
        """Convert an image to a Discord file."""
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return discord.File(fp=buffer, filename=filename)

    def create_profile_embed(self, member: discord.Member, stats: dict, matching_role: str, user_rank: str):
        """Create the embed for the profile."""
        completions = stats.get("completions", {})
        completions_text = "\n".join(f"{key} -> {value}" for key, value in completions.items())

        embed = discord.Embed(
            title=f"{member.name}'s Profile",
            description=f"- **{stats.get('points', 0)} points**\n- **Donjons réalisés**\n{completions_text}",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=f"attachment://{matching_role}.png")
        if user_rank:
            embed.set_image(url=f"attachment://{user_rank}.png")
        return embed
