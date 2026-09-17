"""Identity + permission enforcement (spec section 5: this service is the
single source of truth for both, since it is the only piece both the bot
and dashboard talk to).

Callers (the bot after checking an interaction's member roles, the
dashboard after its own Discord OAuth) attach the caller's identity as
request headers. This module turns those headers into a role and decides
what that role is allowed to do - it never talks to Discord itself.

Which Discord role IDs count as which VAsync role is server_roles table
data (see app.repositories.roles_repository), not code - staff add new
roles via POST /roles instead of a new env var and a redeploy.
"""

from app.config import Settings
from app.models.roles import ServerRole


class IdentityError(Exception):
    pass


def pick_role(role_ids: set[int], configured_roles: list[ServerRole]) -> ServerRole:
    """Highest role wins: any staff-flagged role beats a non-staff one."""
    matches = [role for role in configured_roles if role.discord_role_id in role_ids]
    if not matches:
        raise IdentityError("caller has none of the recognized VAsync roles")
    matches.sort(key=lambda role: role.is_staff, reverse=True)
    return matches[0]


def assert_guild(guild_id: int, settings: Settings) -> None:
    if guild_id != settings.vasync_guild_id:
        raise IdentityError("caller is not in the VAsync guild")


def can_modify_user(actor_discord_id: int, actor_is_staff: bool, target_discord_id: int) -> bool:
    """Non-staff may only edit their own availability; staff can edit
    anyone's (spec section 5)."""
    if actor_is_staff:
        return True
    return actor_discord_id == target_discord_id
