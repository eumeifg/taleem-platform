from django.db import models

# Create your models here.
class H5PExtraction(models.Model):
    ALL_STATUSES = [
    ('in progress', 'In Progress'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
]
    block_id = models.CharField(max_length=255)
    status = models.CharField(max_length=15, choices=ALL_STATUSES,)
    error_message = models.CharField(max_length=255)
    index_page_path = models.CharField(max_length=255)