from django.db import models

# Create your models here.


class DagFile(models.Model):
    dag_file = models.FileField(upload_to='media')
