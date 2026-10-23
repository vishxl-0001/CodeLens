"""User registration and validation service module.

This module provides clean, tested utilities for processing user accounts.
"""

from typing import Dict, Any, Optional
import hashlib
import re


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validate_email_address(email: str) -> bool:
    """Validate whether an email string matches standard email formatting.

    Args:
        email: The raw email string.

    Returns:
        True if the email is valid, False otherwise.
    """
    if not email:
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def hash_token(raw_token: str, salt: str) -> str:
    """Hash an authentication token using SHA-256 with a salt.

    Args:
        raw_token: The plaintext token.
        salt: Salt to prepend before hashing.

    Returns:
        A hexadecimal SHA-256 digest string.
    """
    combined = f"{salt}:{raw_token}".encode("utf-8")
    return hashlib.sha256(combined).hexdigest()


class UserManager:
    """Service to handle user registration and state management."""

    def __init__(self, realm_name: str) -> None:
        """Initialize the manager with a specific realm.

        Args:
            realm_name: Name of the authentication realm.
        """
        self.realm_name = realm_name
        self.users: Dict[str, Dict[str, Any]] = {}

    def register_user(self, username: str, email: str, role: Optional[str] = None) -> bool:
        """Register a new user in the system.

        Args:
            username: The unique user handle.
            email: Primary email address.
            role: Optional user role, defaults to 'member'.

        Returns:
            True if registration was successful, False if user exists.
        """
        if username in self.users:
            return False

        assigned_role = role if role is not None else "member"
        self.users[username] = {
            "username": username,
            "email": email,
            "role": assigned_role,
        }
        return True
