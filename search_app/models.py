from django.db import models

class Restaurant(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    lat = models.FloatField()
    long = models.FloatField()
    cuisines = models.CharField(max_length=255)
    average_cost_for_two = models.IntegerField()
    price_range = models.IntegerField()
    user_rating_aggregate = models.FloatField()
    user_rating_votes = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'restaurants'

class MenuItem(models.Model):
    id = models.AutoField(primary_key=True)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=255)
    price = models.FloatField()
    price_issue = models.BooleanField()
    original_price = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'menu_items'