"""
USERS models for NetBox Network Source of Truth.
"""


class UsersBaseModel:
    """Core domain entity for users subsystem."""
    def __init__(self, name: str, tenant=None):
        self.name = name
        self.tenant = tenant
        self.status = "active"

    def clean(self):
        """Domain validation logic."""
        if not self.name:
            raise ValueError("Name cannot be empty in users")
        return True

    def get_absolute_url(self):
        return f"/users/{self.name}/"
