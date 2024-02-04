from django.db import models

class Video(models.Model):
    video_id = models.CharField(max_length=255, unique=True)
    title = models.TextField()
    description = models.TextField()
    published_datetime = models.DateTimeField()
    thumbnail_urls = models.JSONField()

    def __str__(self):
        return self.title