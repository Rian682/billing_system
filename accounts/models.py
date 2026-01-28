from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
class User(AbstractUser):
    phone = models.CharField(max_length=15, blank=True)
    role = models.CharField(max_length=20, choices=[('staff', 'Staff'), ('manager', 'Manager')])


    def __str__(self):
        return self.username