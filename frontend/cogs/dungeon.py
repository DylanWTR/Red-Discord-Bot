import discord
from discord import app_commands
from discord.ext import commands
from difflib import get_close_matches
from config.dungeons import DUNGEONS
from config.ranks import RANKS_TRESHOLDS, RANGES_VALUES
from backend.models.user_model import UserModel

class Dungeon(commands.Cog):
    def __init__(self, bot: commands.Bot, user_model: UserModel):
        self.bot = bot
        self.user_model = user_model

    @app_commands.command(name="down", description="Find and display dungeon info and update completion stats.")
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

        undo_data = {
            "1-50": 0,
            "51-100": 0,
            "101-150": 0,
            "151-200": 0,
            "200+": 0,
            "rankup": False
        }
        await self.user_model.update_undo(interaction.user.id, undo_data)

        completions = user_document["stats"]["completions"]
        completions[dungeon_index] += 1

        dungeon_level = dungeon_info["lvl"]

        points_field = (
            "200+" if dungeon_level == 200 and dungeon_info.get("hard") else
            "1-50" if dungeon_level <= 50 else
            "51-100" if dungeon_level <= 100 else
            "101-150" if dungeon_level <= 150 else
            "151-200"
        )

        current_points = user_document["stats"]["points"]
        new_points = dungeon_info["points"]

        if points_field not in RANGES_VALUES:
            await interaction.response.send_message(
                f"Error: Range '{points_field}' not found in configuration.",
                ephemeral=True
            )
            return

        range_max = RANGES_VALUES[points_field]
        double_range_max = range_max * 2

        if current_points[points_field] > double_range_max:
            current_points[points_field] = double_range_max
            await self.user_model.update_user_stats(
                interaction.user.id,
                {"points": current_points}
            )
            await interaction.response.send_message(
                f"Your points in range **{points_field}** have been capped at 100%.",
                ephemeral=True
            )
            return

        current_points[points_field] += new_points
        if current_points[points_field] > double_range_max:
            current_points[points_field] = double_range_max

        current_points["total"] += new_points

        await self.user_model.update_user_stats(
            interaction.user.id,
            {"completions": completions, "points": current_points}
        )

        user_rank = user_document["stats"]["rank"]
        updated_rank = await self.check_rank_up(user_rank, current_points)

        rank_message = ""
        rank_up = False
        if updated_rank != user_rank:
            await self.user_model.update_user_stats(
                interaction.user.id,
                {"rank": updated_rank}
            )
            rank_up = True
            rank_message = f"\n🎉 Congratulations! You've ranked up to **{updated_rank}**!"

        undo_data = {
            "1-50": new_points if points_field == "1-50" else 0,
            "51-100": new_points if points_field == "51-100" else 0,
            "101-150": new_points if points_field == "101-150" else 0,
            "151-200": new_points if points_field == "151-200" else 0,
            "200+": new_points if points_field == "200+" else 0,
            "rankup": rank_up
        }
        await self.user_model.update_undo(interaction.user.id, undo_data)

        response_message = (
            f"**Dungeon Completed**: {dungeon_info['dungeon']}\n"
            f"**Boss**: {matched_boss}\n"
            f"**Level**: {dungeon_info['lvl']}\n"
            f"**Points Earned**: {new_points}\n"
            f"{rank_message}"
        )

        await interaction.response.send_message(response_message)

    async def check_rank_up(self, current_rank: str, points: dict) -> str:
        """Check if a user qualifies for the next rank."""
        ranks = list(RANKS_TRESHOLDS.keys())

        current_rank_index = ranks.index(current_rank)

        if current_rank_index == len(ranks) - 1:
            return current_rank

        next_rank = ranks[current_rank_index + 1]
        required_points = RANKS_TRESHOLDS[next_rank]

        cumulative_points = 0
        for range_name in RANGES_VALUES:
            cumulative_points += points.get(range_name, 0)
            if cumulative_points >= required_points:
                return next_rank

        return current_rank
