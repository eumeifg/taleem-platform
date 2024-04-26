# -*- coding: UTF-8 -*-
"""
Video feedback views.
"""
import logging

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie

from util.json_request import JsonResponse
from opaque_keys.edx.keys import CourseKey, UsageKey

from .models import VideoRating, VideoLike

log = logging.getLogger(__name__)


@login_required
@ensure_csrf_cookie
def rate_video(request):
    user = request.user
    course_id = request.POST.get('course_id')
    course_key = CourseKey.from_string(course_id)
    video_id = request.POST.get('video_id')
    block_key = UsageKey.from_string(video_id)
    stars = request.POST.get('stars', 1)

    video_rating, created = VideoRating.objects.get_or_create(
        user=user,
        context_key=course_key,
        block_key=block_key,
    )
    video_rating.stars=stars
    video_rating.save()

    avg_rating = VideoRating.avg_rating(course_key, block_key)
    num_reviews = VideoRating.num_reviews(course_key, block_key)

    return JsonResponse({
        'avg_rating': avg_rating,
        'num_reviews': num_reviews,
    })


@login_required
@ensure_csrf_cookie
def like_video(request):
    user = request.user
    course_id = request.POST.get('course_id')
    course_key = CourseKey.from_string(course_id)
    video_id = request.POST.get('video_id')
    block_key = UsageKey.from_string(video_id)
    like = request.POST.get('like', 1)

    video_like, created = VideoLike.objects.get_or_create(
        user=user,
        context_key=course_key,
        block_key=block_key,
    )
    video_like.like=like
    video_like.save()

    likes = VideoLike.total_likes(course_key, block_key)

    return JsonResponse({
        'likes': likes,
    })


@login_required
@ensure_csrf_cookie
def get_feedback(request):
    user = request.user
    course_id = request.POST.get('course_id')
    course_key = CourseKey.from_string(course_id)
    video_id = request.POST.get('video_id')
    block_key = UsageKey.from_string(video_id)

    user_rating = VideoRating.get_user_rating(user.id, course_key, block_key)
    avg_rating = VideoRating.avg_rating(course_key, block_key)
    num_reviews = VideoRating.num_reviews(course_key, block_key)

    user_like = VideoLike.get_user_like(user.id, course_key, block_key)
    likes = VideoLike.total_likes(course_key, block_key)

    return JsonResponse({
        'user_rating': user_rating,
        'avg_rating': avg_rating,
        'num_reviews': num_reviews,
        'user_like': user_like,
        'likes': likes,
    })

