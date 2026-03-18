"""SQLAlchemy declarative base with per-schema metadata."""

from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass
