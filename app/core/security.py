"""Identity + permission enforcement (spec section 5: this service is the
single source of truth for both, since it is the only piece both the bot
and dashboard talk to).

Callers (the bot after checking an interaction's member roles, the
dashboard after its own Discord OAuth) attach the caller's identity as
request headers. This module turns those headers into a Role and decides
what that role is allowed to do - it never talks to Discord itself.
"""

from app.config import Settings
from app.models.enums import Role


class IdentityError(Exception):
    pass


def resolve_role(role_ids: set[int], settings: Settings) -> Role:
    """Highest role wins: staff > researcher > entity."""
    if settings.staff_role_id in role_ids:
        return Role.STAFF
    if settings.researcher_role_id in role_ids:
        return Role.RESEARCHER
    if settings.entity_role_id in role_ids:
        return Role.ENTITY
    raise IdentityError("caller has none of the recognized VAsync roles")


def assert_guild(guild_id: int, settings: Settings) -> None:
    if guild_id != settings.vasync_guild_id:
        raise IdentityError("caller is not in the VAsync guild")


def can_modify_user(actor_discord_id: int, actor_role: Role, target_discord_id: int) -> bool:
    """Entities/Researchers may only edit their own availability; staff can
    edit anyone's (spec section 5)."""
    if actor_role is Role.STAFF:
        return True
    return actor_discord_id == target_discord_id
