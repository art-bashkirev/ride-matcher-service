"""Intent-aware /goback command registration."""

from .ride_intent import build_ride_conversation


# For registry
slug = "goback"
function = build_ride_conversation(reverse=True)
