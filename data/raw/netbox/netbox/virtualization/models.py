"""
VIRTUALIZATION models for NetBox Network Source of Truth.
"""
from netbox.dcim.models import Device, Site
from netbox.tenancy.models import Tenant

class VirtualizationBaseModel:
    """Core domain entity for virtualization subsystem."""
    def __init__(self, name: str, tenant=None):
        self.name = name
        self.tenant = tenant
        self.status = "active"

    def clean(self):
        """Domain validation logic."""
        if not self.name:
            raise ValueError("Name cannot be empty in virtualization")
        return True

    def get_absolute_url(self):
        return f"/virtualization/{self.name}/"
