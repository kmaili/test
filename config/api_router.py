from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from dauthenticator.users.api.views import UserViewSet
from dauthenticator.core.api.views import AccountAuthentificationViewSet, DriverViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("users", UserViewSet)
router.register("ip_accounts", AccountAuthentificationViewSet, basename="ip_accounts")
router.register('drivers', DriverViewSet, basename="drivers")

app_name = "api"
urlpatterns = router.urls
