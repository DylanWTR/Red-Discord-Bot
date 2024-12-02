from discord.ext import commands
from PIL import Image
import os

class Cache(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.avatar_cache = {}
        self.rank_cache = {}

    async def refresh_cache(self):
        """Refreshes the cache by loading PNGs from assets/avatar/ and assets/rank/."""
        await self._load_images_to_cache("assets/avatar/", self.avatar_cache)
        await self._load_images_to_cache("assets/rank/", self.rank_cache)

    async def _load_images_to_cache(self, directory: str, cache: dict):
        """Helper method to load images from a directory into a cache."""
        if not os.path.exists(directory):
            print(f"Directory {directory} does not exist.")
            return

        for file_name in os.listdir(directory):
            if file_name.endswith(".png"):
                file_path = os.path.join(directory, file_name)
                try:
                    with Image.open(file_path) as img:
                        cache[file_name] = img.copy()
                        print(f"Loaded {file_name} from {directory}.")
                except Exception as e:
                    print(f"Failed to load {file_name} from {directory}: {e}")
