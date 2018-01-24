from django.core.mail import send_mail
from django.core.management import BaseCommand
from django.utils.translation import gettext as _

from yaas.models import Auction, Bid


class Command(BaseCommand):
    help = 'Resolves auction at its deadline.'

    def handle(self, *args, **options):
        auctions = Auction.objects.all().filter(lifecycle='A')
        for auction in auctions:
            if auction.is_due():
                winner = None
                others = []
                mails = []
                if Bid.objects.filter(status='W', auction=auction):
                    winner = Bid.objects.filter(status='W', auction=auction).get().user
                    if Bid.objects.filter(status='L', auction=auction):
                        others = Bid.objects.filter(status='L', auction=auction)
                    for bid in others:
                        mails.append(bid.user)
                auction.lifecycle = 'X'
                auction.save()

                send_mail(_('Auction ended.'),
                          _('Your auction ') + str(auction.title) + _(' has been successfully resolved.') +
                          _(" Winner: {}").format(winner.username if winner else 'None'),
                          'no_reply@yaas.com',
                          [auction.seller.email], fail_silently=False)
                if winner:
                    send_mail(_('Auction won.'), _('You have won this auction: ') + str(auction.title),
                              'no_reply@yaas.com', [winner.email], fail_silently=False)

                mails = []
                for bidder in others:
                    mails.append(bidder.user.email)

                send_mail(_('Auction lost.'), _('You have lost this auction: ') + str(auction.title),
                          'no_reply@yaas.com', mails, fail_silently=False)
