from django.contrib.auth.models import User
from django.test import TestCase
from django.test import RequestFactory
from .views import *


class TestUC3(TestCase):
    """ Test for UC3 - Create an auction """

    fixtures = ['fixtures/test_data.json']

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='user', email='user@user.com', password='userpassword')

    def test_create_auction(self):
        form_data = {'title': 'something', 'description': 'something2', 'minimum_price': '10.0',
                     'deadline': '3018-01-17'}
        form = AddAuctionForm(data=form_data)
        self.assertEqual(form.is_valid(), True)

        count_before = Auction.objects.count()
        auction1 = Auction.objects.create(title="Title", description="Description",
                                          deadline=now() + timedelta(hours=72),
                                          seller=self.user, minimum_price=10)
        auction2 = Auction.objects.get(title="Title")
        self.assertIsNotNone(auction1)
        self.assertIsNotNone(auction2)
        count_after = Auction.objects.count()
        self.assertEqual(auction1, auction2)
        self.assertEqual(auction2.seller, self.user)
        self.assertEqual(count_before, count_after - 1)

        # try to add a new auction without authenticating user
        self.client.logout()
        response = self.client.post('/addauction/', {'title': 'my title', 'description': 'my description',
                                                     'minimum_price': '10', 'deadline': '2018-02-05'})
        self.assertRedirects(response, '/accounts/login/?next=/addauction/')

        # try to add a new auction after authenticating user
        self.client.login(username='user', password='userpassword')
        response = self.client.post('/addauction/', {'title': 'my title', 'description': 'my description',
                                                     'minimum_price': '10', 'deadline': '2018-02-05'})
        self.assertEqual(response.status_code, 302)  # if it's successful it redirects
        self.assertIn('/auctions/', str(response.__getattribute__('url')))


class TestUC6(TestCase):
    """ Test for UC6 - Bid """
    def setUp(self):
        self.factory = RequestFactory()
        self.user1 = User.objects.create_user(
            username='user1', email='user1@user.com', password='userpassword')
        self.user2 = User.objects.create_user(
            username='user2', email='user2@user.com', password='userpassword')

        self.auction1 = Auction.objects.create(title="Title", description="Description",
                                               deadline=now() + timedelta(hours=72),
                                               seller=self.user1, minimum_price=1.00)
        self.auction2 = Auction.objects.create(title="Title", description="Description",
                                               deadline=now() + timedelta(hours=72),
                                               seller=self.user1, minimum_price=1.00)

    # check if seller can bid on their own auction
    def test_bid_on_own(self):
        request = self.factory.post('/bid/', {'amount': str(5.00)})
        request.user = self.user1
        response = bid(request, 1)
        current_bid = None
        if Bid.objects.all().filter(auction=self.auction1):
            current_bid = Bid.objects.all().filter(auction=self.auction1)
        self.assertEqual(response.status_code, 200)  # request successful
        self.assertEqual(current_bid, None)  # no bid exists for given auction

    # check if generic user can bid on an auction
    def test_bid(self):
        request = self.factory.post('/bid/', {'amount': str(5.00)})
        request.user = self.user2
        response = bid(request, 1)
        current_bid = None
        if Bid.objects.all().filter(auction=self.auction1):
            current_bid = Bid.objects.all().filter(auction=self.auction1)

        self.assertEqual(response.status_code, 200)  # request successful
        self.assertEqual(current_bid[0].auction, self.auction1)  # check the bid auction
        self.assertEqual(current_bid[0].user, self.user2)  # check the bid owner
        self.assertEqual(current_bid[0].amount, 5.00)  # check the bid amount
        self.assertEqual(current_bid[0].status, 'W')  # a winning bid should exist

    # check if it is possible to bid less than 0.01
    def test_min_bid(self):
        request = self.factory.post('/bid/', {'amount': str(1.009)})
        request.user = self.user2
        response = bid(request, 2)
        current_bid = None
        if Bid.objects.all().filter(auction=self.auction2):
            current_bid = Bid.objects.all().filter(auction=self.auction2)
        self.assertEqual(response.status_code, 200)  # request successful
        self.assertEqual(current_bid, None)  # no bid exists for given auction
