from rest_framework import serializers

from bitpin_task.posts.models import Post, Rating


class PostSerializer(serializers.ModelSerializer[Post]):
    user_rate = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ["title", "description", "mean_rate", "rate_count", "user_rate"]

        extra_kwargs = {
            "url": {"view_name": "api:post-detail", "lookup_field": "pk"},
        }

    def get_user_rate(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            rating = Rating.objects.filter(user=user, post=obj).first()
            return rating.rate if rating else None
        return None


class RateSerializer(serializers.ModelSerializer):
    post_id = serializers.PrimaryKeyRelatedField(
        queryset=Post.objects.all(), source="post"
    )

    class Meta:
        model = Rating
        fields = ['post_id', 'rate']

        extra_kwargs = {
            # 'rate': {'read_only': True}
        }

    def validate(self, attrs):

        if not 'rate' in attrs:
            raise serializers.ValidationError("Rate field is required")

        attrs["rate"] = self.validate_rate(attrs["rate"])
        return attrs

    def validate_rate(self, value):

        if value < 1 or value > 5:
            raise serializers.ValidationError('Rating has to be between 1 and 5.')
        return value
