"""yaas_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from rest_framework import routers

from yaas import views
from yaas.views import *

router = routers.DefaultRouter()
router.register(r'browse', views.AuctionViewSet)

urlpatterns = [
    url(r'^admin', admin.site.urls),
    url(r'^register/$', register, name='register'),
    url(r'^index/', index, name="index"),
    url(r'^index/login', login_view),
    url(r'^accounts/login/$', login_view),
    url(r'^login/$', login_view),
    url(r'^logout/$', logout_view),
    url(r'^translate/', set_language),
    url(r'^edituser/$', edit_user),
    url(r'^changecurrency/', change_currency),
    url(r'^search/$', search, name='search'),
    url(r'^addauction/$', AddAuction.as_view(), name="addauction"),
    url(r'^auctions/$', all_auctions, name='all_auctions'),
    url(r'^myauctions/', my_auctions, name='my_auctions'),
    url(r'^auctions/(?P<auction_id>[0-9]+)/$', detail, name='detail'),
    url(r'^edit/(?P<pk>\d+)/$', edit_description),
    url(r'^savechanges/(?P<pk>\d+)/$', update_description),
    url(r'^bid/(?P<id>\w+)/$', bid),
    url(r'^banauction/(?P<id>\w+)/$', ban_auction),

    url(r'^api', include(router.urls)),
    url(r'^api/search/$', api_search),
    url(r'^api/search/(\w+)', api_search),
    url(r'^', index, name="index"),
]
