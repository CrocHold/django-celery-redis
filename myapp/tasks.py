from celery import shared_task
from googleapiclient.discovery import build
import pymongo
from datetime import datetime, timedelta
from config import MONGO_URI, YOUTUBE_API_KEYS
from constants import PUBLISHED_AFTER_MINUTES, MAX_FETCHED, CUTOFF_MINUTES


def build_youtube_service():
    """
    build service and report in case of failure.
    respond with videos, in case of success.

    """

    for api_key in YOUTUBE_API_KEYS:
        search_query = 'official'
        try:
            youtube = build('youtube', 'v3', developerKey=api_key)
            # Get the current time
            current_time = datetime.utcnow()

            published_after = current_time - timedelta(minutes=PUBLISHED_AFTER_MINUTES)

            # Format the result in RFC 3339 format
            published_after = published_after.isoformat()
            published_after = published_after + "Z"
            print(published_after)
            request = youtube.search().list(
            part='snippet',
            type='video',
            order='date',
            maxResults=MAX_FETCHED,
            q=search_query,
            publishedAfter=published_after
            )
            response = request.execute()
            return response
        except Exception as e:
            print(f"Failed to build YouTube service with API key {api_key}: {e}")

    # If all keys fail, handle the error or raise an exception
    raise Exception("All YouTube API keys failed")


@shared_task
def fetch_latest_videos():
    """
    fetch and add latest videos to database.
    """
    
    try:
        response = build_youtube_service()

        client = pymongo.MongoClient(MONGO_URI)
        db = client.assignment
        collection = db.videos

        inserted_count = 0

        for item in response.get('items', []):
            video_id = item['id']['videoId']
            # Check if video already exists before updating
            if not collection.find_one({'video_id': video_id}):
                video_data = {
                    'video_id': video_id,
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'published_datetime': datetime.strptime(
                        item['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%SZ'),
                    'thumbnail_urls': {
                        'default': item['snippet']['thumbnails']['default']['url'],
                        'medium': item['snippet']['thumbnails']['medium']['url'],
                        'high': item['snippet']['thumbnails']['high']['url'],
                    },
                }
                collection.insert_one(video_data)
                inserted_count += 1

        client.close()

        return f"Added {inserted_count} new videos"
    
    except Exception as e:
        print(f"Error with YouTube API keys: {e}")
        return "Failed to fetch videos"


@shared_task
def delete_outdated_videos():
    """
    delete outdated videos from database
    """

    client = pymongo.MongoClient(MONGO_URI)
    db = client.assignment
    collection = db.videos

    cutoff_date = datetime.utcnow() - timedelta(minutes=CUTOFF_MINUTES)

    # Delete outdated videos
    result = collection.delete_many({'published_datetime': {'$lt': cutoff_date}})
    deleted_count = result.deleted_count

    client.close()

    return f"Deleted {deleted_count} outdated videos"