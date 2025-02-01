from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()
# Create your models here.
class Post(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    mean_rate = models.FloatField(default=0)
    rate_count = models.IntegerField(default=0)

    class Meta:
        app_label = "posts"




class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ratings")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="ratings")
    rate = models.PositiveSmallIntegerField()  # Should be between 0-5
    created_at = models.DateTimeField(auto_now_add=True)  # Set when first created
    updated_at = models.DateTimeField(auto_now=True)  # Updates every time record is modified


class PostsRatingSummary(models.Model):

    posts_count = models.PositiveIntegerField()
    mean_rate = models.FloatField()
    rate_count = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)  # Set when first created
