"""
Unit tests for tenancy module.
"""
import pytest
from netbox.tenancy.models import TenancyBaseModel

def test_tenancy_initialization():
    obj = TenancyBaseModel(name="test-tenancy-01")
    assert obj.name == "test-tenancy-01"
    assert obj.status == "active"

def test_tenancy_validation():
    obj = TenancyBaseModel(name="valid")
    assert obj.clean() is True
