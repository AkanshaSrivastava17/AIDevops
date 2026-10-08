"""
WIRELESS models for NetBox Network Source of Truth.
"""
from netbox.dcim.models import Interface
from netbox.utilities.mac import clean_mac

class WirelessBaseModel:
    """Core domain entity for wireless subsystem."""
    def __init__(self, name: str, tenant=None):
        self.name = name
        self.tenant = tenant
        self.status = "active"

    def clean(self):
        """Domain validation logic."""
        if not self.name:
            raise ValueError("Name cannot be empty in wireless")
        return True

    def get_absolute_url(self):
        return f"/wireless/{self.name}/"
