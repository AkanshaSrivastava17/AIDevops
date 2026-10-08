"""
Unit tests for extras module.
"""
import pytest
from netbox.extras.models import ExtrasBaseModel

def test_extras_initialization():
    obj = ExtrasBaseModel(name="test-extras-01")
    assert obj.name == "test-extras-01"
    assert obj.status == "active"

def test_extras_validation():
    obj = ExtrasBaseModel(name="valid")
    assert obj.clean() is True
