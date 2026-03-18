"""Seed registry data from config.py dicts.

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-05
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy.orm import Session

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        from db.seed import seed_registry
        counts = seed_registry(session)
        print(f"[0002] Registry seeded: {counts}")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def downgrade() -> None:
    # Truncate all registry tables in dependency order
    bind = op.get_bind()
    bind.execute(op.inline_literal("TRUNCATE registry.coupling_presets CASCADE"))
    bind.execute(op.inline_literal("TRUNCATE registry.pipeline_presets CASCADE"))
    bind.execute(op.inline_literal("TRUNCATE registry.pipeline_steps CASCADE"))
    bind.execute(op.inline_literal("TRUNCATE registry.pipelines CASCADE"))
    bind.execute(op.inline_literal("TRUNCATE registry.couplings CASCADE"))
    bind.execute(op.inline_literal("TRUNCATE registry.presets CASCADE"))
    bind.execute(op.inline_literal("TRUNCATE registry.tools CASCADE"))
    bind.execute(op.inline_literal("TRUNCATE registry.layers CASCADE"))
