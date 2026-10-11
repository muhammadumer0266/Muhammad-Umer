import hashlib

from django.conf import settings


def salted_hash(value: str) -> str:
    """One-way, site-salted hash for IPs/user agents: lets us rate-limit and
    spot abuse without ever storing the raw value."""
    if not value:
        return ""
    return hashlib.sha256(f"{settings.SECRET_KEY}:{value}".encode()).hexdigest()
