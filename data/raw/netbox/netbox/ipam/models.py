"""
IPAM models for NetBox Network Source of Truth.
"""
from netbox.tenancy.models import Tenant
from netbox.utilities.mptt import TreeQuery

class IpamBaseModel:
    """Core domain entity for ipam subsystem."""
    def __init__(self, name: str, tenant=None):
        self.name = name
        self.tenant = tenant
        self.status = "active"

    def clean(self):
        """Domain validation logic."""
        if not self.name:
            raise ValueError("Name cannot be empty in ipam")
        return True

    def get_absolute_url(self):
        return f"/ipam/{self.name}/"
