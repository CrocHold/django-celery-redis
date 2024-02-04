from django.shortcuts import render
from django.core.cache import cache  # Import Django's cache module
# from rest_framework import generics
from django.db.models import Q
from .models import Video
from django.http import JsonResponse
from django.core.cache import cache
from django.db.models import Q
from pymongo import MongoClient
from bson.json_util import dumps
from config import MONGO_URI
from constants import CACHE_EXPIRATION_SECONDS


def index(request):
    return render(request, "myapp/index.html")



def query(request):
    # Check if the result is already in the cache
    cache_key = f"video_list:{hash(str(request.GET))}"
    cached_result = cache.get(cache_key)

    if cached_result:
        return JsonResponse(cached_result, safe=False)

    # Connect to MongoDB
    client = MongoClient(MONGO_URI)
    db = client['assignment']
    videos_collection = db['videos']

    # Build the filter based on query parameters
    title_filter = request.GET.get('searchQuery', None)
    filter_query = {}
    if title_filter:
        filter_query['title'] = {"$regex": title_filter, "$options": "i"}

    # Sort based on the query parameter
    sort_type = request.GET.get('sortOrder', None)
    if sort_type == 'asc':
        sort_order = 1
    else:
        sort_order = -1

    # Pagination support
    page_number = int(request.GET.get('page', 1))  # Default to page 1 if not provided
    items_per_page = 10
    skip_count = (page_number - 1) * items_per_page

    # Query MongoDB with pagination and convert the result to JSON
    queryset = list(videos_collection.find(filter_query).sort('published_datetime', sort_order).skip(skip_count).limit(items_per_page))
    result_json = dumps(queryset)

    # Store the result in the cache for future use
    cache.set(cache_key, result_json, timeout=CACHE_EXPIRATION_SECONDS)

    return JsonResponse(result_json, safe=False)
