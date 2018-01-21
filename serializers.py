from rest_framework import serializers
from yaas.models import Auction


class AuctionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Auction
        fields = ('id', 'seller', 'title', 'description', 'minimum_price',
                  'deadline', 'lifecycle', 'lock', 'lock_timestamp')
