# TODO: Don't shadow module names; it makes debugging difficult.
from .web import web
from .legal import legal
from .env import env
from .config.config import config

__all__ = ["web", "legal", "env", "config"]