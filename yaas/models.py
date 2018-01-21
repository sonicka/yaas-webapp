from decimal import Decimal
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models
from django.urls.base import reverse
from django.utils.timezone import now


class Auction(models.Model):
    LIFECYCLE = (
        ('A', 'Active/Due'),
        ('B', 'Banned'),
        ('X', 'Adjudicated'),
    )

    seller = models.ForeignKey(User, default="", on_delete="models.CASCADE")
    title = models.CharField(max_length=24, blank=False, null=False)
    description = models.CharField(max_length=512, blank=False)
    minimum_price = models.FloatField(blank=False, validators=[MinValueValidator(Decimal('0.01'))])
    deadline = models.DateTimeField(blank=False)
    lifecycle = models.CharField(max_length=1, choices=LIFECYCLE, default='A')
    lock = models.BooleanField(default=False)
    lock_timestamp = models.DateTimeField(blank=True, null=True, default=None)

    def is_due(self):
        return self.deadline <= now()

    def __unicode__(self):
        return self.title

    @staticmethod
    def get_absolute_url():
        return reverse("index")


class Bid(models.Model):
    STATUS = (
        ('W', 'Wining'),
        ('L', 'Losing'),
    )

    auction = models.ForeignKey(Auction, on_delete="models.CASCADE")
    user = models.ForeignKey(User, on_delete="models.CASCADE")
    amount = models.FloatField()
    status = models.CharField(max_length=1, choices=STATUS)
