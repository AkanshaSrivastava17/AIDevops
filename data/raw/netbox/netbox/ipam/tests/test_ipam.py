"""
Unit tests for ipam module.
"""
import pytest
from netbox.ipam.models import IpamBaseModel

def test_ipam_initialization():
    obj = IpamBaseModel(name="test-ipam-01")
    assert obj.name == "test-ipam-01"
    assert obj.status == "active"

def test_ipam_validation():
    obj = IpamBaseModel(name="valid")
    assert obj.clean() is True
