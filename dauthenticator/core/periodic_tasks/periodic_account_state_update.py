import json
import config
from django_celery_beat.models import IntervalSchedule, PeriodicTask


class UpdateAccountStateTasks:
    """
    A class to manage periodic tasks related to account state

    ...
    Attributes
    ----------

    Methods
    -------

    """

    def __init__(self):
        """
        UpdateAccountStateTasks class constructor

        """
        pass

    def update_account_state_tasks(self):
        """
        to create crelery periodic task for each child account category

        Parameters
        ----------
        None

        Returns
        ------
        None
        """
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.HOURS,
        )
        print("task created------")
        PeriodicTask.objects.get_or_create(
            interval=schedule,  # we created this above.
            enabled=True,
            name="account_state_update",
            task="config.tasks.account_state_update",
        )
    def update_facebook_cookies_tasks(self):
        """
        to create crelery periodic task for each child account category

        Parameters
        ----------
        None

        Returns
        ------
        None
        """
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=60,
            period=IntervalSchedule.DAYS,
        )
        print("task created------")
        PeriodicTask.objects.get_or_create(
            interval=schedule,  # we created this above.
            enabled=True,
            name="facebook_cookies_update",
            task="config.tasks.facebook_cookies_update",
        )