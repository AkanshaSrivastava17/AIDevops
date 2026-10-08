"""
Unit tests for dcim module.
"""
import pytest
from netbox.dcim.models import DcimBaseModel

def test_dcim_initialization():
    obj = DcimBaseModel(name="test-dcim-01")
    assert obj.name == "test-dcim-01"
    assert obj.status == "active"

def test_dcim_validation():
    obj = DcimBaseModel(name="valid")
    assert obj.clean() is True
