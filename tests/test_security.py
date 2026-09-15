import pytest

from app.config import Settings
from app.core.security import IdentityError, assert_guild, can_modify_user, resolve_role
from app.models.enums import Role


def make_settings(**overrides) -> Settings:
    defaults = dict(
        database_url="postgresql+asyncpg://test",
        vasync_guild_id=1,
        entity_role_id=10,
        researcher_role_id=20,
        staff_role_id=30,
        service_token="secret",
    )
    defaults.update(overrides)
    return Settings(_env_file=None, **defaults)


def test_resolve_role_prefers_highest_role():
    settings = make_settings()
    assert resolve_role({10, 20, 30}, settings) is Role.STAFF
    assert resolve_role({10, 20}, settings) is Role.RESEARCHER
    assert resolve_role({10}, settings) is Role.ENTITY


def test_resolve_role_raises_when_no_recognized_role():
    with pytest.raises(IdentityError):
        resolve_role({999}, make_settings())


def test_assert_guild_raises_on_mismatch():
    settings = make_settings()
    assert_guild(1, settings)  # does not raise
    with pytest.raises(IdentityError):
        assert_guild(2, settings)


def test_staff_can_modify_anyone():
    assert can_modify_user(actor_discord_id=1, actor_role=Role.STAFF, target_discord_id=2)


def test_entity_can_only_modify_self():
    assert can_modify_user(actor_discord_id=1, actor_role=Role.ENTITY, target_discord_id=1)
    assert not can_modify_user(actor_discord_id=1, actor_role=Role.ENTITY, target_discord_id=2)
