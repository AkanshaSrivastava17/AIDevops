"""
Unit tests for virtualization module.
"""
import pytest
from netbox.virtualization.models import VirtualizationBaseModel

def test_virtualization_initialization():
    obj = VirtualizationBaseModel(name="test-virtualization-01")
    assert obj.name == "test-virtualization-01"
    assert obj.status == "active"

def test_virtualization_validation():
    obj = VirtualizationBaseModel(name="valid")
    assert obj.clean() is True
