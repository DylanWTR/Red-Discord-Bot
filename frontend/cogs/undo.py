import discord
from discord import app_commands
from discord.ext import commands
from config.dungeons import DUNGEONS
from config.ranks import RANKS_ROLES
from backend.models.user_model import UserModel

class Undo(commands.Cog):
    def __init__(self, bot: commands.Bot, user_model: UserModel):
        self.bot = bot
        self.user_model = user_model

    @app_commands.command(name="undo", description="Annule la dernière commande /down pour tous les participants.")
    async def undo(self, interaction: discord.Interaction):
        """Slash command to undo the last /down action for all participants."""
        user_document = await self.user_model.get_user(interaction.user.id)
        if not user_document:
            await interaction.response.send_message(
                "Vous n'avez pas de profil. Commande annulée."
            )
            return

        undo_data = user_document.get("undo", {}).get("participants", {})
        if not undo_data:
            await interaction.response.send_message(
                "Aucune action récente à annuler."
            )
            return

        response_message = "⏪ **Annulation de la dernière commande `/down` pour tous les participants**\n\n"

        for user_id, user_undo_data in undo_data.items():
            member = interaction.guild.get_member(int(user_id))
            if not member:
                response_message += f"- Impossible de trouver le membre avec l'ID {user_id} dans ce serveur.\n"
                continue

            user_document = await self.user_model.get_user(member.id)
            if not user_document:
                response_message += f"- {member.mention} n'a pas de profil valide.\n"
                continue

            completion_index = user_undo_data["completion_index"]
            user_document["stats"]["completions"][completion_index] -= 1

            current_points = user_document["stats"]["points"]
            for field in ["1-50", "51-100", "101-150", "151-200", "200+"]:
                current_points[field] -= user_undo_data[field]
            current_points["total"] -= user_undo_data["total"]

            current_rank = user_document["stats"]["rank"]
            previous_rank = user_undo_data.get("previous_rank", current_rank)

            if previous_rank != current_rank:
                current_role = interaction.guild.get_role(RANKS_ROLES.get(current_rank))
                previous_role = interaction.guild.get_role(RANKS_ROLES.get(previous_rank))

                if current_role and current_role in member.roles:
                    await member.remove_roles(current_role)
                if previous_role:
                    await member.add_roles(previous_role)

                await self.user_model.update_user_stats(member.id, {"rank": previous_rank})

            await self.user_model.update_user_stats(
                member.id,
                {
                    "completions": user_document["stats"]["completions"],
                    "points": current_points
                }
            )

            response_message += f"- Annulation réussie pour {member.mention}.\n"

        await self.user_model.update_user_stats(
            interaction.user.id,
            {"undo": {"participants": {}}}
        )

        await interaction.response.send_message(response_message)
