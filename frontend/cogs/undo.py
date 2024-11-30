import discord
from discord import app_commands
from discord.ext import commands
from config.ranks import RANKS_TRESHOLDS
from backend.models.user_model import UserModel

class Undo(commands.Cog):
    def __init__(self, bot: commands.Bot, user_model: UserModel):
        self.bot = bot
        self.user_model = user_model

    @app_commands.command(name="undo", description="Undo the last dungeon completion action.")
    async def undo(self, interaction: discord.Interaction):
        """Slash command to undo the last dungeon completion."""
        user_document = await self.user_model.get_user(interaction.user.id)

        if not user_document:
            await interaction.response.send_message(
                "Tu n'as pas encore de profil. Contactes un admin.", ephemeral=True
            )
            return

        undo_data = user_document.get("undo", None)
        if not undo_data or all(value == 0 for key, value in undo_data.items() if key != "rankup") and not undo_data["rankup"]:
            await interaction.response.send_message(
                "Il n'y a rien à annuler.", ephemeral=True
            )
            return

        stats = user_document["stats"]
        current_points = stats["points"]

        for points_field in ["1-50", "51-100", "101-150", "151-200", "200+"]:
            current_points[points_field] -= undo_data.get(points_field, 0)
            if current_points[points_field] < 0:
                current_points[points_field] = 0

        current_points["total"] -= sum(undo_data.get(points_field, 0) for points_field in ["1-50", "51-100", "101-150", "151-200", "200+"])
        if current_points["total"] < 0:
            current_points["total"] = 0

        current_rank = stats["rank"]
        if undo_data.get("rankup", False):
            rank_thresholds = list(RANKS_TRESHOLDS.keys())
            current_rank_index = rank_thresholds.index(current_rank)
            if current_rank_index > 0:
                new_rank = rank_thresholds[current_rank_index - 1]
                stats["rank"] = new_rank
            else:
                stats["rank"] = current_rank

        undo_reset = {
            "1-50": 0,
            "51-100": 0,
            "101-150": 0,
            "151-200": 0,
            "200+": 0,
            "rankup": False
        }
        await self.user_model.update_user_stats(interaction.user.id, {"points": current_points, "rank": stats["rank"]})
        await self.user_model.update_undo(interaction.user.id, undo_reset)

        response_message = (
            f"✅ Ton dernier achèvement de donjon à été annulé.\n"
            f"**Rang**: {stats['rank']}\n"
            f"**Points totaux**: {current_points['total']}"
        )

        await interaction.response.send_message(response_message)
