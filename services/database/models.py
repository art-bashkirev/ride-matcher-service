"""PostgreSQL models using TortoiseORM."""

from tortoise import fields
from tortoise.models import Model


class User(Model):
    """User model for storing Telegram user information."""

    id = fields.IntField(pk=True)
    telegram_id = fields.BigIntField(unique=True, index=True)
    username = fields.CharField(max_length=255, null=True)
    first_name = fields.CharField(max_length=255, null=True)
    last_name = fields.CharField(max_length=255, null=True)
    language_code = fields.CharField(max_length=10, null=True)
    is_bot = fields.BooleanField(default=False)
    is_premium = fields.BooleanField(default=False)

    # User preferences
    home_station = fields.CharField(max_length=20, null=True)  # Station code like s1234567
    preferred_timezone = fields.CharField(max_length=50, default="Europe/Moscow")

    # Timestamps
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "users"

    def __str__(self):
        return f"User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})"


class Trip(Model):
    """Trip model for storing user trip history."""

    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="trips", on_delete=fields.CASCADE)

    # Trip details
    from_station = fields.CharField(max_length=20)  # Station code
    to_station = fields.CharField(max_length=20, null=True)  # Station code (optional for schedule queries)
    trip_date = fields.DateField()
    trip_time = fields.TimeField(null=True)

    # Trip metadata
    transport_type = fields.CharField(max_length=20, null=True)  # plane, train, suburban, bus, etc.
    notes = fields.TextField(null=True)

    # Timestamps
    created_at = fields.DatetimeField(auto_now_add=True)
    queried_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "trips"
        indexes = [
            ("user", "created_at"),
            ("user", "from_station"),
            ("trip_date",),
        ]

    def __str__(self):
        return f"Trip(id={self.id}, user={self.user_id}, from={self.from_station}, date={self.trip_date})"


class Station(Model):
    """Station model for storing station information."""

    id = fields.IntField(pk=True)
    code = fields.CharField(max_length=20, unique=True, index=True)  # Station code like s1234567
    title = fields.CharField(max_length=255)
    short_title = fields.CharField(max_length=100, null=True)
    popular_title = fields.CharField(max_length=255, null=True)

    # Station details
    station_type = fields.CharField(max_length=50, null=True)  # airport, train_station, etc.
    transport_type = fields.CharField(max_length=20, null=True)  # plane, train, suburban, bus, etc.

    # Location (optional)
    latitude = fields.DecimalField(max_digits=10, decimal_places=7, null=True)
    longitude = fields.DecimalField(max_digits=10, decimal_places=7, null=True)

    # Metadata
    country_code = fields.CharField(max_length=5, null=True)
    region = fields.CharField(max_length=100, null=True)
    city = fields.CharField(max_length=100, null=True)

    # Timestamps
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "stations"
        indexes = [
            ("title",),
            ("transport_type",),
            ("latitude", "longitude"),
        ]

    def __str__(self):
        return f"Station(code={self.code}, title={self.title})"