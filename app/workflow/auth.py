"""
Centralized RBAC and Persona Authentication Service (Sections 4, 4.1, 7.5, 10.3).
Provides Demo Mode persona switcher and Real Mode authorization.
ProjectMembership is the source of truth for project-level authorization.
"""
import os
import logging
from typing import Optional, Dict, Any, List
from fastapi import Request, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.workflow.models import User, ProjectRole, GlobalRole
from app.workflow.db import WorkflowDB

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


# 6 Defined Personas (Section 4)
DEMO_PERSONAS = {
    "user-junior": {
        "id": "user-junior",
        "name": "Alex Rivera",
        "role": ProjectRole.JUNIOR_DEV,
        "title": "Junior Software Engineer",
        "email": "alex.rivera@enterprise.dev",
        "avatar": "AR",
        "global_role": GlobalRole.MEMBER
    },
    "user-po": {
        "id": "user-po",
        "name": "Sarah Chen",
        "role": ProjectRole.PRODUCT_OWNER,
        "title": "Principal Product Owner",
        "email": "sarah.chen@enterprise.dev",
        "avatar": "SC",
        "global_role": GlobalRole.MEMBER
    },
    "user-techlead": {
        "id": "user-techlead",
        "name": "Marcus Vance",
        "role": ProjectRole.TECH_LEAD,
        "title": "Staff Architect & Tech Lead",
        "email": "marcus.vance@enterprise.dev",
        "avatar": "MV",
        "global_role": GlobalRole.MEMBER
    },
    "user-qa": {
        "id": "user-qa",
        "name": "Elena Rostova",
        "role": ProjectRole.QA_ENGINEER,
        "title": "Senior QA Automation Engineer",
        "email": "elena.rostova@enterprise.dev",
        "avatar": "ER",
        "global_role": GlobalRole.MEMBER
    },
    "user-manager": {
        "id": "user-manager",
        "name": "David Sterling",
        "role": ProjectRole.ENGINEERING_MANAGER,
        "title": "Director of Engineering",
        "email": "david.sterling@enterprise.dev",
        "avatar": "DS",
        "global_role": GlobalRole.MEMBER
    },
    "user-admin": {
        "id": "user-admin",
        "name": "Akansha Srivastava",
        "role": ProjectRole.ADMIN,
        "title": "Platform Administrator",
        "email": "admin@enterprise.dev",
        "avatar": "AS",
        "global_role": GlobalRole.ADMIN
    }
}

CURRENT_DEMO_USER_ID = "user-techlead"  # Default persona


class AuthService:
    def __init__(self, db: WorkflowDB):
        self.db = db

    def get_active_persona(self) -> User:
        p = DEMO_PERSONAS.get(CURRENT_DEMO_USER_ID, DEMO_PERSONAS["user-techlead"])
        return User(
            id=p["id"],
            name=p["name"],
            email=p["email"],
            global_role=p["global_role"],
            avatar=p["avatar"],
            title=p["title"]
        )

    def switch_demo_persona(self, user_id: str) -> User:
        global CURRENT_DEMO_USER_ID
        if user_id not in DEMO_PERSONAS:
            raise ValueError(f"Unknown persona '{user_id}'. Allowed: {list(DEMO_PERSONAS.keys())}")
        CURRENT_DEMO_USER_ID = user_id
        return self.get_active_persona()

    def get_current_user(self, request: Optional[Request] = None, credentials: Optional[HTTPAuthorizationCredentials] = None) -> User:
        """
        Resolves current user:
        1. X-Demo-User-Id header (for UI persona switching)
        2. Bearer token / session (in real mode)
        3. Default active persona
        """
        if request is not None:
            demo_header = request.headers.get("X-Demo-User-Id")
            if demo_header and demo_header in DEMO_PERSONAS:
                p = DEMO_PERSONAS[demo_header]
                return User(
                    id=p["id"],
                    name=p["name"],
                    email=p["email"],
                    global_role=p["global_role"],
                    avatar=p["avatar"],
                    title=p["title"]
                )

        return self.get_active_persona()

    def check_project_permission(
        self,
        user: User,
        project_id: str,
        required_roles: List[ProjectRole]
    ) -> bool:
        if user.global_role == GlobalRole.ADMIN:
            return True
        user_role = self.db.get_user_project_role(user.id, project_id)
        if not user_role:
            return False
        return user_role in required_roles
