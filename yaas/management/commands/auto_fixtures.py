import string
import json
import random
import pkg_resources
from datetime import timedelta
from django.core.management import BaseCommand
from django.utils.crypto import get_random_string
from django.utils.timezone import now
from yaas.models import Auction, Bid


class Command(BaseCommand):

    def handle(self, *args, **options):
        users = []
        auctions = []
        bids = []

        for x in range(51):
            username = get_random_string(length=random.randint(5, 15))
            password = get_random_string(length=random.randint(6, 26))
            email = generate_mail()
            json_user = {"model": "auth.user", "pk": x,
                         "fields": {"username": username, "email": email, "password": password}}
            users.append(json_user)

        for x in range(51):
            auction = Auction
            auction.seller = random.randint(0, 50)
            auction.title = get_random_string(length=random.randint(5, 15))
            auction.description = get_random_string(length=random.randint(10, 50))
            auction.minimum_price = random.randint(1, 5)
            auction.deadline = str(now() + timedelta(days=random.randint(5, 30)))
            auction.lifecycle = random.choice(["A", "B"])
            auction.lock = False
            auction.lock_timestamp = None
            json_auction = {"model": "yaas.Auction", "pk": x, "fields": {"seller": auction.seller,
                                                                         "title": auction.title,
                                                                         "description": auction.description,
                                                                         "minimum_price": auction.minimum_price,
                                                                         "deadline": auction.deadline,
                                                                         "lifecycle": auction.lifecycle,
                                                                         "lock": auction.lock,
                                                                         "lock_timestamp": auction.lock_timestamp}}
            num = random.randint(0, 10)
            bid_owners = [y for y in range(0, 51) if y != auction.seller]
            for x in range(num):
                bid = Bid
                bid.user = random.choice(bid_owners)
                if x == num-1:
                    status = 'W'
                    amount = random.randint(801, 1000)
                else:
                    status = 'L'
                    amount = random.randint(5, 800)
                bid.amount = amount
                bid.status = status

                json_bid = {"model": "yaas.Bid", "pk": x, "fields": {"auction": x,
                                                                     "user": bid.user,
                                                                     "amount": bid.amount,
                                                                     "status": bid.status}}
                bids.append(json_bid)

            auctions.append(json_auction)

        all_data = users + auctions + bids

        file = pkg_resources.resource_filename("fixtures", "fixtures/test_data.json")
        with open(file, 'w') as outfile:
            json.dump(all_data, outfile)


def generate_mail():
    domains = ["amail.com", "bmail.com", "cmail.com", "dmail.com", "fmail.com", "hmail.com"]
    letters = string.ascii_lowercase[:12]
    name = ''.join(random.choice(letters) for i in range(random.randint(5, 15)))
    domain = random.choice(domains)
    return name + '@' + domain
