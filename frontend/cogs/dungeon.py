import discord
from discord import app_commands
from discord.ext import commands
from difflib import get_close_matches
from config.dungeons import DUNGEONS
from backend.models.user_model import UserModel


class Dungeon(commands.Cog):
    def __init__(self, bot: commands.Bot, user_model: UserModel):
        self.bot = bot
        self.user_model = user_model

    @app_commands.command(name="down", description="Find and display dungeon info based on the boss name.")
    async def down(self, interaction: discord.Interaction, boss_name: str):
        """Slash command to autocorrect and display dungeon info and update completion stats."""
        boss_name_lower = boss_name.lower()

        closest_match = get_close_matches(
            boss_name_lower,
            [key.lower() for key in DUNGEONS],
            n=1,
            cutoff=0.5
        )

        if not closest_match:
            await interaction.response.send_message(
                f"No dungeon found for '{boss_name}'.", ephemeral=True
            )
            return

        matched_boss = next(key for key in DUNGEONS if key.lower() == closest_match[0])
        dungeon_info = DUNGEONS[matched_boss]

        dungeon_index = dungeon_info.get("index")
        if dungeon_index is None:
            await interaction.response.send_message(
                f"Error: Dungeon '{dungeon_info['dungeon']}' is missing an index.", ephemeral=True
            )
            return

        user_document = await self.user_model.get_user(interaction.user.id)

        if not user_document:
            await interaction.response.send_message(
                "You don't have a profile yet. Please create one first.", ephemeral=True
            )
            return

        completions = user_document["stats"]["completions"]
        completions[dungeon_index] += 1

        dungeon_level = dungeon_info["lvl"]
        points_field = (
            "1-50" if dungeon_level <= 50 else
            "51-100" if dungeon_level <= 100 else
            "101-150" if dungeon_level <= 150 else
            "151-200" if dungeon_level <= 200 else
            "200+"
        )

        current_points = user_document["stats"]["points"]
        new_points = dungeon_info["points"]
        current_points[points_field] += new_points
        current_points["total"] += new_points

        await self.user_model.update_user_stats(
            interaction.user.id,
            {"completions": completions, "points": current_points}
        )

        await interaction.response.send_message(
            f"**Dungeon Completed**: {dungeon_info['dungeon']}\n"
            f"**Boss**: {matched_boss}\n"
            f"**Level**: {dungeon_info['lvl']}\n"
            f"**Points Earned**: {new_points}\n\n"
        )
