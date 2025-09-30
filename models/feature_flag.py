"""Feature flag ORM model."""

from tortoise import fields
from tortoise.models import Model


class FeatureFlag(Model):
    """Persistent feature flag stored in Postgres."""

    id = fields.IntField(pk=True)
    key = fields.CharField(max_length=100, unique=True)
    is_enabled = fields.BooleanField(default=False)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "feature_flags"

    def __str__(self) -> str:  # pragma: no cover - debugging helper
        return f"FeatureFlag(key={self.key!r}, enabled={self.is_enabled})"
