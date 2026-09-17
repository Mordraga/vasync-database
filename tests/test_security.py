import pytest

from app.config import Settings
from app.core.security import IdentityError, assert_guild, can_modify_user, pick_role
from app.models.roles import ServerRole


def make_settings(**overrides) -> Settings:
    defaults = dict(
        database_url="postgresql+asyncpg://test",
        vasync_guild_id=1,
        service_token="secret",
    )
    defaults.update(overrides)
    return Settings(_env_file=None, **defaults)


def make_roles() -> list[ServerRole]:
    return [
        ServerRole(id=1, name="entity", discord_role_id=10, is_staff=False),
        ServerRole(id=2, name="researcher", discord_role_id=20, is_staff=False),
        ServerRole(id=3, name="staff", discord_role_id=30, is_staff=True),
    ]


def test_pick_role_prefers_staff():
    roles = make_roles()
    assert pick_role({10, 20, 30}, roles).name == "staff"
    assert pick_role({30}, roles).name == "staff"


def test_pick_role_returns_the_only_match():
    roles = make_roles()
    assert pick_role({10}, roles).name == "entity"
    assert pick_role({20}, roles).name == "researcher"


def test_pick_role_raises_when_no_recognized_role():
    with pytest.raises(IdentityError):
        pick_role({999}, make_roles())


def test_assert_guild_raises_on_mismatch():
    settings = make_settings()
    assert_guild(1, settings)  # does not raise
    with pytest.raises(IdentityError):
        assert_guild(2, settings)


def test_staff_can_modify_anyone():
    assert can_modify_user(actor_discord_id=1, actor_is_staff=True, target_discord_id=2)


def test_entity_can_only_modify_self():
    assert can_modify_user(actor_discord_id=1, actor_is_staff=False, target_discord_id=1)
    assert not can_modify_user(actor_discord_id=1, actor_is_staff=False, target_discord_id=2)
