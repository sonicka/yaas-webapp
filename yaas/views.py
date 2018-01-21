import requests
from datetime import timedelta
from django import forms

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.forms import ModelForm
from django.http import Http404, HttpResponseRedirect, HttpResponse, HttpResponseNotFound
from django.urls import reverse
from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.contrib.auth import authenticate, login, logout
from django.utils import translation

from django.utils.timezone import now
from django.views.generic import View
from django.views.generic.edit import CreateView
from rest_framework import viewsets
from rest_framework.renderers import JSONRenderer
from django.utils.translation import gettext as _

from serializers import AuctionSerializer
from .forms import UserForm
from yaas.models import Auction, Bid


def index(request):
    return render(request, 'index.html')


class UserFormView(View):
    form_class = UserForm
    template_name = 'registration_form.html'

    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user.set_password(password)
            user.save()
            user = authenticate(username=username, email=email, password=password)

            if user is not None:

                if user.is_active:
                    login(request, user)
                    return redirect('auctions:index')

        return render(request, self.template_name, {'form': form})


def register(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.INFO, _("Your account is created. You can now login."))
            return HttpResponseRedirect(reverse("index"))
        else:
            form = UserForm(request.POST)
    else:
        form = UserForm()
    return render(request, 'registration_form.html', {'form': form})


def login_view(request):
    msg = _("Login here.")
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                auth.login(request, user)
                return render(request, "index.html", {'msg': _("You've been logged in.")})
        else:
            return render(request, "index.html", {'msg': _("Login failed. Please try again.")})
    else:
        return render(request, "login.html", {'msg': msg})
    return render(request, "index.html", {'msg': msg})


def logout_view(request):
    logout(request)
    msg = _("You've been logged out.")
    return render(request, 'index.html', {'msg': msg})


def edit_user(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            password = request.POST['password']
            password2 = request.POST['password2']
            email = request.POST['email']

            if email:
                request.user.email = email
            if password and (password == password2):
                request.user.set_password(password)
            if password and password != password2:
                msg = _("Passwords don't match.")
                return render(request, "edit_user.html", {'msg': msg})
            request.user.save()
            return render(request, "edit_user.html", {'msg': _("Your account has been updated."), 'name': request.user})
    else:
        return render(request, "edit_user.html", {'msg': _("You have to log in before editing profile.")})
    return render(request, 'edit_user.html', {'name': request.user})


class AddAuctionForm(ModelForm):
    class Meta(object):
        model = Auction
        fields = ['title', 'description', 'minimum_price', 'deadline']
        widgets = {
            'title': forms.TextInput(attrs={'required': True, 'placeholder': _('add title')}),
            'description': forms.TextInput(attrs={'required': True, 'placeholder': _('add description')}),
            'minimum_price': forms.NumberInput(attrs={'required': True, 'placeholder': _('add price in €')}),
            'deadline': forms.TextInput(attrs={'required': True, 'placeholder': _('mm/dd/yyyy')}),
        }

    def clean_deadline(self):
        deadline = self.cleaned_data['deadline']
        if deadline < now() + timedelta(hours=72):
            raise ValidationError(_("Deadline must be at least 72 hours in the future."))
        return deadline


class AddAuction(LoginRequiredMixin, CreateView):
    model = Auction
    form_class = AddAuctionForm
    template_name = "create_auction.html"

    def form_valid(self, form):
        form.instance.seller = self.request.user
        super().form_valid(form)
        a_id = form.instance.id
        u = self.request.build_absolute_uri  # todo či?
        print(u)
        messages.add_message(self.request, messages.INFO, str(u))

        send_mail(_('New auction created.'), _("Your auction has been created successfully. " + str(u)),
                  'no_reply@yaas.com', [self.request.user.email], fail_silently=False)
        return HttpResponseRedirect("/auctions/" + str(a_id) + "/")


def edit_description(request, pk):
    if not Auction.objects.filter(pk=pk).exists():
        messages.add_message(request, messages.ERROR, _("Auction doesn't exist."))
        return render(request, "index.html")

    if request.user.is_authenticated:
        if Auction.objects.get(pk=pk):
            auction = Auction.objects.get(pk=pk)
            if auction.lifecycle != 'A' or request.user != auction.seller:
                messages.add_message(request, messages.ERROR, _("You are not allowed to edit this auction."))
                return HttpResponseRedirect(reverse('index'))
            else:
                auction.lock = True
                auction.lock_timestamp = now()
                auction.save()
                return render(request, 'edit_auction.html', {'user': request.user, "title": auction.title, "id": pk,
                                                             "description": auction.description,
                                                             "deadline": auction.deadline,
                                                             "min_price": auction.minimum_price})
        else:
            messages.add_message(request, messages.ERROR, _("Auction doesn't exist."))
            return render(request, "index.html")
    else:
        return render(request, "index.html", {'msg': _("You need to log in before editing an auction.")})


def update_description(request, pk):
    if request.user.is_authenticated:
        with transaction.atomic():
            auction = Auction.objects.get(pk=pk)
            auction.description = request.POST.get('description', '')
            auction.lock = False
            auction.lock_timestamp = None
            auction.save()
        return render(request, 'detail.html', {'auction': auction, 'price': auction.minimum_price, 'currency': '€',
                                               'msg': _("Auction description updated.")})


def all_auctions(request):
    set_language(request)
    auctions_all = Auction.objects.all().exclude(lifecycle='B')
    return render(request, 'all_auctions.html', {'all_auctions': auctions_all})


def my_auctions(request):
    set_language(request)
    if request.user.is_authenticated:
        auctions_my = Auction.objects.filter(seller=request.user)
        return render(request, 'my_auctions.html', {'my_auctions': auctions_my})


def detail(request, auction_id):
    try:
        auction = Auction.objects.get(pk=auction_id)

        if auction.lock_timestamp and auction.lock_timestamp + timedelta(minutes=10) < now():
            auction.lock = False
        if auction.lock and auction.seller != request.user:
            return render(request, "lock.html", {'auction': auction})

        request.session['currentauction'] = auction_id
        price = auction.minimum_price
        currency = "eur"
        if Bid.objects.filter(status="W", auction=auction).exists():
            price = Bid.objects.get(status='W', auction=auction).amount
        if 'currency' in request.session:
            if request.session['currency'] != "eur":
                currency = request.session['currency']
                rate = request.session['rate']
                price = float("{0:.2f}".format(price * rate))
        if currency == "usd":
            currency_symbol = "$"
        elif currency == "eur":
            currency_symbol = "€"
        else:
            currency_symbol = "Kč"

    except Auction.DoesNotExist:
        raise Http404(_("Auction does not exist."))

    request.session['currency'] = "eur"

    return render(request, 'detail.html', {'auction': auction, 'price': price, 'currency': currency_symbol})


def search(request):
    auctions = Auction.objects.filter(title__contains=request.GET['s']).exclude(lifecycle='B')
    return render(request, 'all_auctions.html', {'all_auctions': auctions})


def bid(request, id):
    auction = Auction.objects.get(id=id)
    if auction.lock and auction.seller != request.user:
        return render(request, "lock.html", {'auction': auction})
    auction.lock = True
    auction.lock_timestamp = now()
    auction.save()
    try:
        if request.user.is_authenticated:
            if request.method == 'POST':
                amount = request.POST['amount']
                if not auction:
                    return render("detail.html", {'msg': _("Auction not found.")})

                if auction.lifecycle != 'A' or auction.is_due():
                    return render(request, "detail.html", {'auction': auction, 'currency': "€",
                                                           'msg': _("Auction is not active.")})

                previous_winning_bid = Bid.objects.filter(status='W', auction=auction)
                if previous_winning_bid:
                    previous_winning_bid = Bid.objects.filter(status='W', auction=auction).get()

                if request.user == auction.seller:
                    msg = _("You cannot bid on your own auction.")
                    if previous_winning_bid:
                        return render(request, "detail.html", {'auction': auction, 'price': previous_winning_bid.amount,
                                                               'currency': "€", 'msg': msg})
                    else:
                        return render(request, "detail.html", {'auction': auction, 'price': auction.minimum_price,
                                                               'currency': "€", 'msg': msg})

                msg2 = _("Bid added successfully.")
                if previous_winning_bid:
                    if previous_winning_bid.user == request.user:
                        return render(request, "detail.html", {'auction': auction, 'current_bid': previous_winning_bid,
                                                               'price': previous_winning_bid.amount, 'currency': "€",
                                                               'msg': _("You are the highest bidder.")})

                    if float(amount) - previous_winning_bid.amount < 0.01:
                        return render(request, "detail.html", {'auction': auction, 'current_bid': previous_winning_bid,
                                                               'price': previous_winning_bid.amount, 'currency': "€",
                                                               'msg': _("Bid must be bigger than current price.")})
                    else:
                        send_mail(_('Auction losing.'), _("You've been overbid in auction."), 'no_reply@yaas.com',
                                  [previous_winning_bid.user.email], fail_silently=False)
                        previous_winning_bid.status = 'L'
                        previous_winning_bid.save()
                        new_bid = Bid(user=request.user, amount=float(amount), auction=auction, status='W')
                        new_bid.save()
                        return render(request, "detail.html", {'auction': auction, 'current_bid': new_bid,
                                                               'price': new_bid.amount, 'currency': "€",
                                                               'msg': msg2})
                else:
                    if auction.minimum_price > float(amount) or (float(amount) - auction.minimum_price < 0.01):
                        return render(request, "detail.html", {'auction': auction, 'price': auction.minimum_price,
                                                               'currency': "€",
                                                               'msg': _("Bid must be bigger than current price.")})
                    else:
                        new_bid = Bid(user=request.user, amount=float(amount), auction=auction, status='W')
                        new_bid.save()
                        return render(request, "detail.html", {'auction': auction, 'current_bid': new_bid,
                                                               'price': new_bid.amount, 'currency': "€",
                                                               'msg': msg2})
        else:
            return render(request, "detail.html", {'auction': auction, 'msg': _("You have to log in before bidding.")})
    finally:
        auction.lock = False
        auction.lock_timestamp = None
        auction.save()


def ban_auction(request, id):
    if request.user.is_superuser:
        auction = Auction.objects.filter(id=id)
        banmsg = _('Auction Banned.')
        if auction:
            with transaction.atomic():
                auction = Auction.objects.get(id=id)
                auction.lifecycle = 'B'
                auction.save()
            send_mail(banmsg, _("Your auction has been banned."), 'no_reply@yaas.com', [auction.seller.email],
                      fail_silently=False)
            mails = []
            bids = Bid.objects.all().filter(auction=auction)
            for b in bids:
                if b.user.email in mails:
                    pass
                else:
                    mails.append(b.user.email)
            send_mail(banmsg, _("An auction in which you have bid on has been banned."), 'no_reply@yaas.com',
                      mails, fail_silently=False)

            return render(request, "detail.html", {'auction': auction, 'price': auction.minimum_price,
                                                   'msg': banmsg, 'currency': "€"})
        else:
            return render(request, "detail.html", {'msg': _("Auction not found."),
                                                   'currency': "€"})
    else:
        return render(request, "index.html", {'msg': _("You have to be admin to ban an auction.")})


def set_language(request):
    if request.method == 'POST':
        request.session[translation.LANGUAGE_SESSION_KEY] = request.POST['lang']
        translation.activate(request.session[translation.LANGUAGE_SESSION_KEY])
    msg = _("Language changed")
    return render(request, "index.html", {'msg': msg})


def change_currency(request):
    if request.method == 'POST':
        currency = request.POST['currency']
        request.session['currency'] = currency
        exchange_rate = get_exchange_rate(currency)
        request.session['rate'] = exchange_rate
        if '/auctions/' or '/savechanges/' in request.META['HTTP_REFERER'] and not request.META[
            'HTTP_REFERER'].endswith('/auctions/'):
            return HttpResponseRedirect('/auctions/%d/' % int(request.session['currentauction']))
        else:
            request.session['currency'] = "eur"
            request.session['rate'] = get_exchange_rate("eur")
            return render(request, "index.html", {'msg': _("View an auction before changing currency.")})


def get_exchange_rate(currency):
    url = "https://openexchangerates.org/api/latest.json?app_id=d5e35cdc65fe4791bdf69ec662b71904"
    json_data = requests.get(url).json()
    eur = json_data["rates"]["EUR"]
    if currency == "usd":
        return eur
    elif currency == "czk":
        czk = json_data["rates"]["CZK"]
        return (1 / eur) * czk
    else:
        return 1


""""""" API methods """""""


class AuctionViewSet(viewsets.ModelViewSet):
    """ API endpoint that allows auctions to be viewed. """

    queryset = Auction.objects.all().exclude(lifecycle='B')
    serializer_class = AuctionSerializer


class JSONResponse(HttpResponse):
    """ An HttpResponse that renders its content into JSON. """

    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


def api_search(request, title=''):
    """ Search via API"""

    if title == '':
        auctions = Auction.objects.all().exclude(lifecycle='B')
        serializer = AuctionSerializer(auctions, many=True)
        return JSONResponse(serializer.data)

    auctions = Auction.objects.all().filter(title__contains=title).exclude(lifecycle='B')
    if len(auctions) < 1 and title != '':
        return HttpResponseNotFound('<h1>Error 404 - No auction found.\n</h1>', status=404)

    else:
        serializer = AuctionSerializer(auctions, many=True)
        return JSONResponse(serializer.data)
