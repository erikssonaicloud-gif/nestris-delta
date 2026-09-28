"""NESTRIS Δ AI helpers — SpaceXAI (xAI API) by default."""

from .spacexai import get_client, get_model, ask_grok
from .piece_oracle import PieceOracle

__all__ = ["get_client", "get_model", "ask_grok", "PieceOracle"]
