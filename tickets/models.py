from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CASCADE


# Create your models here.
# class Users(AbstractUser):
#     jira_username = models.CharField(
#         max_length=150,
#         unique=True,
#         null=True,
#         blank=True,
#         help_text="Custom username set upon first login."
#     )
#
#     pass

# class Ticket(models.Model):
#     id = models.IntegerField(default=0)
    #created_by = models.ForeignKey(Users, on_delete=CASCADE, related_name="created_tickets")
    #date_created = models.DateTimeField(auto_now_add=True)
    #date_created = models.DateTimeField(auto_now_add=True)


#class TicketPersons(models.Model):
    # person = models.ForeignKey(Users, on_delete=CASCADE)
    # ticket = models.ForeignKey(Ticket, on_delete=CASCADE)