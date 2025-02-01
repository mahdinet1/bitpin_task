from django.conf import settings
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter

from bitpin_task.posts.api.views import PostViewSet, RateViewSet
from bitpin_task.users.api.views import UserViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

router.register("users", UserViewSet)
router.register("post", PostViewSet)
router.register("rate", RateViewSet,basename="rate")

app_name = "api"
urlpatterns = router.urls
