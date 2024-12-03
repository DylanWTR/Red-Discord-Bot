import discord
from discord import app_commands
from discord.ext import commands
from difflib import get_close_matches
from config.dungeons import DUNGEONS
from config.ranks import RANKS_TRESHOLDS, RANGES_VALUES, RANGE_MAP, RANKS_ROLES
from backend.models.user_model import UserModel
from typing import Optional

class Dungeon(commands.Cog):
    def __init__(self, bot: commands.Bot, user_model: UserModel):
        self.bot = bot
        self.user_model = user_model

    @app_commands.command(name="down", description="Valide un donjon et met à jour les stats des participants.")
    async def down(
        self,
        interaction: discord.Interaction,
        boss_name: str,
        extra_1: Optional[discord.Member] = None,
        extra_2: Optional[discord.Member] = None,
        extra_3: Optional[discord.Member] = None,
        extra_4: Optional[discord.Member] = None,
        extra_5: Optional[discord.Member] = None,
        extra_6: Optional[discord.Member] = None,
        extra_7: Optional[discord.Member] = None
    ):
        """Slash command to process a dungeon for multiple participants."""
        dungeon_data = self.get_dungeon_info(boss_name)
        if not dungeon_data:
            await interaction.response.send_message(
                f"Pas de donjon trouvé pour '{boss_name}'.", ephemeral=True
            )
            return

        dungeon_info, dungeon_key = dungeon_data
        users_to_update = self.prepare_users(interaction, extra_1, extra_2, extra_3, extra_4, extra_5, extra_6, extra_7)
        if not await self.validate_users(users_to_update, interaction):
            return

        participant_mentions = ", ".join(user.mention for user in users_to_update)
        response_message = self.format_dungeon_info(dungeon_info, dungeon_key)
        response_message += f"**Participants**: {participant_mentions}\n\n"

        rank_up_messages = []
        undo_participants = {}

        for user in users_to_update:
            undo_data, rank_up_message = await self.process_user(user, dungeon_info, interaction)
            if undo_data:
                undo_participants[str(user.id)] = undo_data
            if rank_up_message:
                rank_up_messages.append(rank_up_message)

        if rank_up_messages:
            response_message += "\n".join(rank_up_messages)

        await self.user_model.update_user_stats(
            interaction.user.id,
            {"undo": {"participants": undo_participants}}
        )

        await interaction.response.send_message(response_message)

    def get_dungeon_info(self, boss_name: str) -> Optional[tuple[dict, str]]:
        """Find and return dungeon info based on the boss name."""
        boss_name_lower = boss_name.lower()
        closest_match = get_close_matches(
            boss_name_lower,
            [key.lower() for key in DUNGEONS],
            n=1,
            cutoff=0.5
        )
        if not closest_match:
            return None
        matched_boss = next(key for key in DUNGEONS if key.lower() == closest_match[0])
        return DUNGEONS.get(matched_boss), matched_boss

    def prepare_users(self, interaction: discord.Interaction, *extras: Optional[discord.Member]) -> list[discord.Member]:
        """Prepare a list of unique users to process."""
        users_to_update = [interaction.user]
        users_to_update.extend(user for user in extras if user is not None)
        return list(set(users_to_update))

    async def validate_users(self, users: list[discord.Member], interaction: discord.Interaction) -> bool:
        """Validate all users and ensure they have a profile."""
        for user in users:
            user_document = await self.user_model.get_user(user.id)
            if not user_document:
                await interaction.response.send_message(
                    f"{user.display_name} n'a pas de profil. Commande annulée.",
                    ephemeral=True
                )
                return False
        return True

    def format_dungeon_info(self, dungeon_info: dict, dungeon_key: str) -> str:
        """Format dungeon information for the response."""
        boss_name = dungeon_info.get("boss", dungeon_key)
        return (
            f"**Donjon**: {dungeon_info['dungeon']}\n"
            f"**Boss**: {boss_name}\n"
            f"**Niveau**: {dungeon_info['lvl']}\n"
            f"**Points gagnés**: {dungeon_info['points']}\n\n"
        )

    async def process_user(self, user: discord.Member, dungeon_info: dict, interaction: discord.Interaction) -> tuple[dict, Optional[str]]:
        """Process a single user: update stats, handle rank-ups, and prepare undo data."""
        user_document = await self.user_model.get_user(user.id)
        dungeon_index = dungeon_info.get("index")
        if dungeon_index is None:
            await interaction.response.send_message(
                f"Error: le donjon '{dungeon_info['dungeon']}' n'a pas d'index. Contactes un admin.", ephemeral=True
            )
            return {}, None

        completions = user_document["stats"]["completions"]
        completions[dungeon_index] += 1

        dungeon_level = dungeon_info["lvl"]
        is_hard = dungeon_info.get("hard", False)
        new_points = dungeon_info["points"]
        points_field = self.get_points_field(dungeon_level, is_hard)

        current_points = user_document["stats"]["points"]
        undo_data = {
            "total": 0,
            "1-50": 0,
            "51-100": 0,
            "101-150": 0,
            "151-200": 0,
            "200+": 0,
            "completion_index": dungeon_index,
            "previous_rank": user_document["stats"]["rank"]
        }

        self.distribute_points_with_undo(current_points, new_points, points_field, undo_data)
        current_points["total"] += new_points
        undo_data["total"] = new_points

        await self.user_model.update_user_stats(
            user.id,
            {"completions": completions, "points": current_points}
        )

        user_rank = user_document["stats"]["rank"]
        updated_rank = await self.check_rank_up(user_rank, current_points, user)

        if updated_rank != user_rank:
            await self.user_model.update_user_stats(
                user.id,
                {"rank": updated_rank}
            )
            return undo_data, f"Félicitations {user.mention} ! Tu es passé au rang **{updated_rank}** !"

        return undo_data, None

    def get_points_field(self, dungeon_level: int, is_hard: bool) -> str:
        """Determine the points field based on dungeon level and difficulty."""
        if dungeon_level == 200 and is_hard:
            return "200+"
        return (
            "1-50" if dungeon_level <= 50 else
            "51-100" if dungeon_level <= 100 else
            "101-150" if dungeon_level <= 150 else
            "151-200"
        )

    async def check_rank_up(self, current_rank: str, points: dict, member: discord.Member) -> str:
        """Check if a user qualifies for the next rank, update their roles, and return the new rank."""
        ranks = list(RANKS_TRESHOLDS.keys())
        current_rank_index = ranks.index(current_rank)

        if current_rank_index == len(ranks) - 1:
            return current_rank

        next_rank = ranks[current_rank_index + 1]
        range_name = RANGE_MAP[next_rank]
        threshold = RANKS_TRESHOLDS[next_rank]
        points_in_range = points.get(range_name, 0)

        if points_in_range >= threshold:
            guild = member.guild
            rank_roles = [guild.get_role(role_id) for role_id in RANKS_ROLES.values()]
            new_role = guild.get_role(RANKS_ROLES[next_rank])

            if not new_role:
                raise ValueError(f"Role for rank {next_rank} does not exist in the guild.")

            for role in rank_roles:
                if role and role in member.roles:
                    await member.remove_roles(role)

            await member.add_roles(new_role)

            return next_rank

        return current_rank

    def distribute_points_with_undo(self, current_points: dict, new_points: int, target_field: str, undo_data: dict):
        """Distribute points with undo tracking."""
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
                undo_data[range_name] += new_points
                break
            else:
                current_points[range_name] += available_space
                undo_data[range_name] += available_space
                new_points -= available_space
