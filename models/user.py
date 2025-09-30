from tortoise import fields
from tortoise.models import Model


class User(Model):
    """User model for storing Telegram user preferences."""

    id = fields.IntField(pk=True)
    telegram_id = fields.BigIntField(unique=True, index=True)
    username = fields.CharField(max_length=255, null=True)
    first_name = fields.CharField(max_length=255, null=True)
    last_name = fields.CharField(max_length=255, null=True)

    # Station preferences
    base_station_code = fields.CharField(max_length=50, null=True)  # Yandex station code
    base_station_title = fields.CharField(max_length=255, null=True)
    destination_code = fields.CharField(max_length=50, null=True)  # Yandex station code
    destination_title = fields.CharField(max_length=255, null=True)

    # Admin privileges
    is_admin = fields.BooleanField(default=False)

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "users"

    def __str__(self):
        return f"User(telegram_id={self.telegram_id}, base={self.base_station_title}, dest={self.destination_title})"