from django.apps import AppConfig
from django.contrib.auth.forms import UserCreationForm
from django import forms


class YaasConfig(AppConfig):
    name = 'auctions'


class UserForm(UserCreationForm):
    email = forms.EmailField(required=True, max_length=254)

    def save(self, commit=True):
        user = super(UserForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
