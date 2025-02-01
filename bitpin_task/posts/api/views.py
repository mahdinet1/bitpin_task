from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import ListModelMixin, CreateModelMixin
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.mixins import UpdateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework import permissions
from bitpin_task.posts.tasks import queue_rating_update
from .serializers import PostSerializer, RateSerializer
from bitpin_task.posts.models import Post, Rating


class PostViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin,CreateModelMixin, GenericViewSet):
    serializer_class = PostSerializer
    queryset = Post.objects.all()
    lookup_field = "pk"

    def get_permissions(self):
        return [AllowAny()]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class RateViewSet(ModelViewSet):
    serializer_class = RateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        post_id = self.request.query_params.get("post_id")
        queryset = Rating.objects.filter(user=self.request.user)
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)


        post_id = request.data.get("post_id")
        post = get_object_or_404(Post, id=post_id)



        rating, created = Rating.objects.update_or_create(
            user=request.user,
            post=post,
            defaults={"rate": request.data.get("rate")}
        )

        # TODO - add to queue for change the post mean rate
        queue_rating_update.delay(post_id, request.user.id, request.data.get("rate"))

        serializer = self.get_serializer(rating)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=status_code)

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed("DELETE is not allowed on this endpoint.")
