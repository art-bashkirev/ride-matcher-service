"""Intent-aware /goto command registration."""

from .ride_intent import build_ride_conversation


# For registry
slug = "goto"
function = build_ride_conversation(reverse=False)
