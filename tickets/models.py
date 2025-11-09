from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CASCADE


# Create your models here.
class Users(AbstractUser):
    pass

# class Ticket(models.Model):
#     id = models.IntegerField(default=0)
    #created_by = models.ForeignKey(Users, on_delete=CASCADE, related_name="created_tickets")
    #date_created = models.DateTimeField(auto_now_add=True)
    #date_created = models.DateTimeField(auto_now_add=True)


#class TicketPersons(models.Model):
    # person = models.ForeignKey(Users, on_delete=CASCADE)
    # ticket = models.ForeignKey(Ticket, on_delete=CASCADE)