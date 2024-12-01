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
                f"Pas de donjon trouvé pour '{boss_name}'.", ephemeral=True
            )
            return

        matched_boss = next(key for key in DUNGEONS if key.lower() == closest_match[0])
        dungeon_info = DUNGEONS[matched_boss]

        dungeon_index = dungeon_info.get("index")
        if dungeon_index is None:
            await interaction.response.send_message(
                f"Error: le donjon '{dungeon_info['dungeon']}' n'a pas d'index. Contactes un admin.", ephemeral=True
            )
            return

        user_document = await self.user_model.get_user(interaction.user.id)

        if not user_document:
            await interaction.response.send_message(
                "Tu n'as pas encore de profil. Contactes un admin.", ephemeral=True
            )
            return

        completions = user_document["stats"]["completions"]
        completions[dungeon_index] += 1

        dungeon_level = dungeon_info["lvl"]
        new_points = dungeon_info["points"]

        points_field = (
            "200+" if dungeon_level == 200 and dungeon_info.get("hard") else
            "1-50" if dungeon_level <= 50 else
            "51-100" if dungeon_level <= 100 else
            "101-150" if dungeon_level <= 150 else
            "151-200"
        )

        current_points = user_document["stats"]["points"]
        self.distribute_points(current_points, new_points, points_field)

        current_points["total"] += new_points

        await self.user_model.update_user_stats(
            interaction.user.id,
            {"completions": completions, "points": current_points}
        )

        user_rank = user_document["stats"]["rank"]
        updated_rank = await self.check_rank_up(user_rank, current_points)

        rank_message = ""
        if updated_rank != user_rank:
            await self.user_model.update_user_stats(
                interaction.user.id,
                {"rank": updated_rank}
            )
            rank_message = f"\n🎉 Félicitation! Tu est passé **{updated_rank}**!"

            guild = interaction.guild
            if guild:
                rank_roles = [role_name for role_name in RANKS_TRESHOLDS.keys()]
                member = guild.get_member(interaction.user.id)

                if member:
                    roles_to_remove = [
                        role for role in member.roles if role.name in rank_roles and role.name != updated_rank
                    ]
                    for role in roles_to_remove:
                        await member.remove_roles(role, reason="Ranked up in dungeon game")

                    rank_role = discord.utils.get(guild.roles, name=updated_rank)
                    if rank_role:
                        await member.add_roles(rank_role, reason="Ranked up in dungeon game")
                        rank_message += f"\nTu as reçu le rang **{updated_rank}** !"

        response_message = (
            f"**Donjon complété**: {dungeon_info['dungeon']}\n"
            f"**Boss**: {matched_boss}\n"
            f"**Niveau**: {dungeon_info['lvl']}\n"
            f"**Points gagnés**: {new_points}\n"
            f"{rank_message}"
        )

        await interaction.response.send_message(response_message)

    def distribute_points(self, current_points: dict, new_points: int, target_field: str):
        """Distribute points starting from the lowest range up to the target range, with overflow capped at max range * 2."""
        point_ranges = ["1-50", "51-100", "101-150", "151-200", "200+"]
        target_index = point_ranges.index(target_field)

        for i in range(target_index + 1):
            range_name = point_ranges[i]
            range_max = RANGES_VALUES[range_name]
            double_range_max = range_max * 2

            if current_points[range_name] >= double_range_max:
                continue

            available_space = double_range_max - current_points[range_name]

            if new_points <= available_space:
                current_points[range_name] += new_points
                new_points = 0
                break
            else:
                current_points[range_name] += available_space
                new_points -= available_space

    async def check_rank_up(self, current_rank: str, points: dict) -> str:
        """Check if a user qualifies for the next rank."""
        ranks = list(RANKS_TRESHOLDS.keys())
        current_rank_index = ranks.index(current_rank)

        if current_rank_index == len(ranks) - 1:
            return current_rank

        next_rank = ranks[current_rank_index + 1]
        required_points = RANKS_TRESHOLDS[next_rank]

        cumulative_points = 0
        for range_name, range_max in RANGES_VALUES.items():
            cumulative_points += points.get(range_name, 0)

            if required_points <= range_max or cumulative_points >= required_points:
                if cumulative_points >= required_points:
                    return next_rank
                break

        return current_rank
