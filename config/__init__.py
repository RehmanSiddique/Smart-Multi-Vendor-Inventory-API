# Apply patches before Django starts
try:
    from . import patches
except ImportError:
    pass

from .celery import app as celery_app

__all__ = ('celery_app',)