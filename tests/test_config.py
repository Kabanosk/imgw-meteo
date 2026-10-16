"""Pydantic config validation and immutability."""

import pytest
from pydantic import ValidationError

from imgw_meteo.config import ClientConfig, Refresh, StandardizationConfig


def test_defaults():
    cfg = ClientConfig()
    assert cfg.offline is False
    assert cfg.refresh is Refresh.IF_STALE
    assert cfg.timeout == 30.0


def test_refresh_accepts_valid_string():
    assert ClientConfig(refresh="always").refresh is Refresh.ALWAYS


def test_refresh_rejects_invalid():
    with pytest.raises(ValidationError):
        ClientConfig(refresh="sometimes")


def test_timeout_must_be_positive():
    with pytest.raises(ValidationError):
        ClientConfig(timeout=0)


def test_configs_are_frozen():
    with pytest.raises(ValidationError):
        StandardizationConfig().status_to_nan = False


def test_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        StandardizationConfig(unknown_option=True)
