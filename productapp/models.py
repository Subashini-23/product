from django.db import models

# Create your models here.

class Product(models.Model):
    s_no = models.AutoField(primary_key=True)
    product_id = models.CharField(max_length=100, unique=True)
    product_name = models.CharField(max_length=255)

    def __str__(self):
        return self.product_name

class Order(models.Model):
    order_id = models.AutoField(primary_key=True)
    customer_id = models.CharField(max_length=100)
    product_name = models.CharField(max_length=255)
    quantity = models.IntegerField()

    def __str__(self):
        return f"Order {self.order_id} by {self.customer_id}"

