"""
Created/Updated: 2026-09-24 20:32 GMT+7
Main Function: Exports the local Knowledge asset storage adapter.
"""

"""Knowledge binary storage adapters."""

from app.infrastructure.storage.local import LocalFileStorage

__all__ = ["LocalFileStorage"]
