# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery_app import app as celery_app
from .tasks import (
    account_state_update,
)

__all__ = (
    "celery_app",
    "account_state_update",
)