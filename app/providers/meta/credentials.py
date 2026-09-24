from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MetaCredentialContext:
    """Minimal provider-facing Meta credential context.

    The access token is created by CredentialResolver infrastructure and must
    never be persisted, logged, or placed into Knowledge metadata.
    """

    access_token: str
