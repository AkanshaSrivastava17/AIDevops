"""
Unit tests for utilities module.
"""
import pytest
from netbox.utilities.models import UtilitiesBaseModel

def test_utilities_initialization():
    obj = UtilitiesBaseModel(name="test-utilities-01")
    assert obj.name == "test-utilities-01"
    assert obj.status == "active"

def test_utilities_validation():
    obj = UtilitiesBaseModel(name="valid")
    assert obj.clean() is True
