"""
TENANCY models for NetBox Network Source of Truth.
"""


class TenancyBaseModel:
    """Core domain entity for tenancy subsystem."""
    def __init__(self, name: str, tenant=None):
        self.name = name
        self.tenant = tenant
        self.status = "active"

    def clean(self):
        """Domain validation logic."""
        if not self.name:
            raise ValueError("Name cannot be empty in tenancy")
        return True

    def get_absolute_url(self):
        return f"/tenancy/{self.name}/"
