from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from dauthenticator.users.api.views import UserViewSet
from dauthenticator.core.api.views import AccountAuthentificationViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("users", UserViewSet)
router.register("ip_accounts", AccountAuthentificationViewSet)

app_name = "api"
urlpatterns = router.urls
