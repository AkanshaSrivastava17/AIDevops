"""
Unit tests for users module.
"""
import pytest
from netbox.users.models import UsersBaseModel

def test_users_initialization():
    obj = UsersBaseModel(name="test-users-01")
    assert obj.name == "test-users-01"
    assert obj.status == "active"

def test_users_validation():
    obj = UsersBaseModel(name="valid")
    assert obj.clean() is True
