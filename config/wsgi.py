"""
WSGI config for dauthenticator project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.

"""
import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application

#from dauthenticator.core.periodic_tasks.periodic_account_state_update import UpdateAccountStateTasks
# This allows easy placement of apps within the interior
# dauthenticator directory.
ROOT_DIR = Path(__file__).resolve(strict=True).parent.parent
sys.path.append(str(ROOT_DIR / "dauthenticator"))
# We defer to a DJANGO_SETTINGS_MODULE already in the environment. This breaks
# if running multiple sites in the same mod_wsgi process. To fix this, use
# mod_wsgi daemon mode with each site in its own daemon process, or use
# os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.production"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
application = get_wsgi_application()
from dauthenticator.core.periodic_tasks.periodic_account_state_update import UpdateAccountStateTasks

# Apply WSGI middleware here.
# from helloworld.wsgi import HelloWorldApplication
# application = HelloWorldApplication(application)
# creation of periodic events
# periodic_task = UpdateAccountStateTasks()
# periodic_task.update_account_state_tasks()
periodic_task = UpdateAccountStateTasks()
periodic_task.update_facebook_cookies_tasks()
