"""
Unit tests for circuits module.
"""
import pytest
from netbox.circuits.models import CircuitsBaseModel

def test_circuits_initialization():
    obj = CircuitsBaseModel(name="test-circuits-01")
    assert obj.name == "test-circuits-01"
    assert obj.status == "active"

def test_circuits_validation():
    obj = CircuitsBaseModel(name="valid")
    assert obj.clean() is True
