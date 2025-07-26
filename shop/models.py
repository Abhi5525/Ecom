from django.db import models
import uuid, datetime
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.conf import settings


# Create your models here.
class products(models.Model):
    title = models.CharField(max_length=150)
    price = models.FloatField()
    discount_price = models.FloatField()
    category = models.CharField(max_length=200)
    description = models.TextField()
    image = models.CharField(max_length= 300)

    def __str__(self):
        return self.title
    
    
class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    items = models.JSONField()
    name = models.CharField(max_length=150)
    email = models.EmailField()
    address = models.TextField()
    state = models.CharField(max_length=100)
    has_paid = models.BooleanField(default=False)
    total = models.FloatField(default=0.0)
    phone = models.CharField(max_length=10, default='9999999999')
    transaction_uuid = models.CharField(max_length=255, default=uuid.uuid4)
    order_date = models.DateField(default=datetime.date.today)

    def __str__(self):
        return f"Order {self.id} by {self.user.email}"
    
class User(AbstractUser):
    username = models.CharField(max_length=100, unique=True)  # Remove the username field
    email = models.EmailField(_('email address'), unique=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email