from django.db import models
import uuid

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
    items = models.JSONField()
    name = models.CharField(max_length=150)
    email = models.EmailField()
    address = models.TextField()
    state = models.CharField(max_length=100)
    has_paid = models.BooleanField(default=False)
    total = models.FloatField(default=0.0)
    phone = models.CharField(max_length=10, default=9999999999)
    transaction_uuid = models.CharField(max_length=255, default=uuid.uuid4)

    def __str__(self):
        return self.name