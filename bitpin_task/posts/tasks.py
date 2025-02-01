from celery import shared_task
from django.core.cache import cache
from datetime import datetime, timedelta
from .models import Post, Rating, PostsRatingSummary
from django.db.models import Avg, Sum

SPIKE_TIME_LIMIT = 60 * 60 * 1
SPIKE_RATE_LIMIT = 10000


@shared_task
def queue_rating_update(post_id, user_id, new_rate):
    cache_key = f"post_ratings:{post_id}"
    last_updated = cache.get(f'last_updated:{post_id}')
    post_rate_count_key = f"post_rate_count:{post_id}"
    prev_num = cache.get(post_rate_count_key, 0)
    new_num = prev_num + 1


    rate = Rating.objects.filter(post_id=post_id, user_id=user_id).first()
    ratings = cache.get(cache_key, {})
    if not rate and user_id not in ratings:
        cache.set(post_rate_count_key, new_num + 1, )




    now = datetime.timestamp(datetime.now())
    start_time = cache.get(last_updated, None)
    if start_time is None:
        cache.set(last_updated, now)
    elif (now - start_time) > SPIKE_TIME_LIMIT:
        cache.set(last_updated, now)

    if start_time is not None and (now - start_time) < SPIKE_TIME_LIMIT and new_num > SPIKE_RATE_LIMIT:
        print(f"there is a spike in rating for post: {post_id}")
        return

    ratings[user_id] = new_rate

    cache.set(cache_key, ratings, )

    print("saved to cache", cache.keys("post_ratings:*"))


@shared_task
def process_daily_ratings():
    print("process_daily_ratings starts")

    summary = PostsRatingSummary.objects.last()
    global_mean = summary.mean_rate if summary else 3.0
    global_count = summary.rate_count if summary else 0

    post_keys = [key for key in cache.keys("post_ratings:*")]
    post_count_keys = cache.keys("post_rate_count:*")
    post_timer_keys = cache.keys("last_updated:*")

    for cache_key in post_keys:
        post_id = int(cache_key.split(":")[-1])
        ratings = cache.get(cache_key, {})

        if not ratings:
            continue

        prev_rates = Rating.objects.filter(post=post_id)
        post = Post.objects.get(id=post_id)

        sum_ratings = sum(ratings.values()) + prev_rates.aggregate(Sum('rate'))['rate__sum']
        rate_count = len(ratings) + prev_rates.count()

        # Apply Bayesian Mean Formula
        bayesian_mean = (global_count * global_mean + sum_ratings) / (global_count + rate_count)

        # here we update mean with only users that are not in rate spike but we show users the real rate count
        Post.objects.filter(id=post_id).update(mean_rate=bayesian_mean,
                                               rate_count=cache.get(f"post_rate_count:{post_id}", 0) +  post.rate_count)

        cache.delete(cache_key)

    cache.delete_many(post_count_keys)
    cache.delete_many(post_timer_keys)

    total_posts = Post.objects.count()
    total_ratings = Rating.objects.count()
    global_mean = Rating.objects.aggregate(Avg('rate'))['rate__avg']
    global_count = total_ratings if total_ratings else 0

    PostsRatingSummary.objects.update_or_create(
        defaults={"posts_count": total_posts, "mean_rate": global_mean, "rate_count": global_count},
    )
    return f"Processed {len(post_keys)} posts."
