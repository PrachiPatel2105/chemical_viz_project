from django.db import models
from django.contrib.auth.models import User
from django.db.models import JSONField
from django.db.models.query import QuerySet

class UploadedDataset(models.Model):
    """
    Model to store metadata about an uploaded dataset file for a user.
    Includes logic to enforce a history limit (last 5 records).
    """
    # Link to the user who uploaded the file
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='datasets')
    
    # Name of the dataset (e.g., the original filename)
    name = models.CharField(max_length=255)
    
    # Timestamp when the record was created
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Summary of the data, stored as JSON (e.g., column names, data types, value ranges)
    # Using Django's built-in JSONField which works with SQLite
    summary_data = JSONField(default=dict)
    
    # Path/reference to the actual stored file (e.g., CSV, Excel)
    file_path = models.CharField(max_length=512) 

    class Meta:
        # **--- CRITICAL FIX: Explicitly setting app_label resolves Windows path issues ---**
        app_label = 'data_api'
        ordering = ['-timestamp'] # Order by newest first

    def __str__(self):
        return f"{self.user.username} - {self.name} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"

    def save(self, *args, **kwargs):
        """
        Custom save method to:
        1. Save the new instance.
        2. Automatically delete the oldest datasets for the user,
           keeping only the last 5 records.
        """
        # 1. Save the current instance first
        super().save(*args, **kwargs)

        # 2. Enforce the history limit (keep last 5)
        user_datasets: QuerySet = UploadedDataset.objects.filter(user=self.user).order_by('-timestamp')
        count = user_datasets.count()

        if count > 5:
            # Get the IDs of the datasets to keep (the 5 newest)
            ids_to_keep = user_datasets.values_list('id', flat=True)[:5]
            
            # Find and delete all datasets that are NOT in the 'ids_to_keep' list
            datasets_to_delete = UploadedDataset.objects.filter(user=self.user).exclude(id__in=ids_to_keep)
            
            # NOTE: For a complete app, file deletion logic (os.remove(dataset.file_path)) 
            # would be added here *before* calling .delete().
            datasets_to_delete.delete()