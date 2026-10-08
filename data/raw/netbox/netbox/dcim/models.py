"""
DCIM models for NetBox Network Source of Truth.
"""
from netbox.ipam.models import IPAddress
from netbox.tenancy.models import Tenant

class DcimBaseModel:
    """Core domain entity for dcim subsystem."""
    def __init__(self, name: str, tenant=None):
        self.name = name
        self.tenant = tenant
        self.status = "active"

    def clean(self):
        """Domain validation logic."""
        if not self.name:
            raise ValueError("Name cannot be empty in dcim")
        return True

    def get_absolute_url(self):
        return f"/dcim/{self.name}/"
