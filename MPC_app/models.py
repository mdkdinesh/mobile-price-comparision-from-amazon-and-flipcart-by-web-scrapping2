from django.db import models


# Create your models here.
class Amazon(models.Model):
    name = models.CharField(max_length=35)
    color = models.CharField(max_length=20)
    ram = models.IntegerField()
    rom = models.IntegerField()
    price = models.IntegerField()


class Flipcart(models.Model):
    name = models.CharField(max_length=35)
    color = models.CharField(max_length=20)
    ram = models.IntegerField()
    rom = models.IntegerField()
    price = models.IntegerField()


class Compare(models.Model):
    name = models.CharField(max_length=35)
    color = models.CharField(max_length=20)
    ram = models.IntegerField()
    rom = models.IntegerField()
    amazon_price = models.IntegerField()
    flipcart_price = models.IntegerField()
    diff = models.IntegerField()
