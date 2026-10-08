"""
Unit tests for wireless module.
"""
import pytest
from netbox.wireless.models import WirelessBaseModel

def test_wireless_initialization():
    obj = WirelessBaseModel(name="test-wireless-01")
    assert obj.name == "test-wireless-01"
    assert obj.status == "active"

def test_wireless_validation():
    obj = WirelessBaseModel(name="valid")
    assert obj.clean() is True
