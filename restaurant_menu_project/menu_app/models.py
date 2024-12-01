from django.db import models

class Restaurant(models.Model):
    restaurant_id = models.AutoField(primary_key=True)  # SERIAL PRIMARY KEY
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Menu(models.Model):
    menu_id = models.AutoField(primary_key=True)  # SERIAL PRIMARY KEY
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, to_field='restaurant_id')
    version = models.IntegerField()
    date = models.DateField()

    def __str__(self):
        return f"Menu {self.version} for {self.restaurant.name}"


class MenuSection(models.Model):
    section_id = models.AutoField(primary_key=True)  # SERIAL PRIMARY KEY
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, to_field='menu_id')
    section_name = models.CharField(max_length=100)
    section_order = models.IntegerField()

    def __str__(self):
        return self.section_name


class DietaryRestriction(models.Model):
    restriction_id = models.AutoField(primary_key=True)  # SERIAL PRIMARY KEY
    label = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.label


class MenuItem(models.Model):
    item_id = models.AutoField(primary_key=True)  # SERIAL PRIMARY KEY
    section = models.ForeignKey(MenuSection, on_delete=models.CASCADE, to_field='section_id')
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    dietary_restriction = models.ForeignKey(DietaryRestriction, null=True, blank=True, on_delete=models.SET_NULL, to_field='restriction_id')

    def __str__(self):
        return self.name


class ProcessingLog(models.Model):
    log_id = models.AutoField(primary_key=True)  # SERIAL PRIMARY KEY
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, to_field='menu_id')
    status = models.CharField(max_length=50)
    error_message = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log for Menu {self.menu.menu_id}"
