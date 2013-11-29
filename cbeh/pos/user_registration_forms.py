from django import forms
from django.forms import ModelForm, PasswordInput
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User

from captcha.fields import CaptchaField

from pos.models import *


class UserForm(ModelForm):
    """User Form subclass"""
    # These 2 functions for password checks
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance', None)
        if instance is not None and instance.pk:
            self.fields['password'].required = False

    def clean_password(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('confirm_password')
        if self.instance is not None and self.instance.pk:
            if not len(password):
                password = self.instance.password
                self.cleaned_data['password'] = password
                return password
        if (password and password2) and (password != password2):
            raise forms.ValidationError(u"Passwords do not match")
            return password

        return make_password(password)

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if first_name == '':
            raise forms.ValidationError(u'This field is required')
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if last_name == '':
            raise forms.ValidationError(u'This field is required')
        return last_name

    def clean_email(self):
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username')
        if email and User.objects.filter(email=email).exclude(username=username).count():
            raise forms.ValidationError(u'Email address already exists')
        elif email == '':
            raise forms.ValidationError(u'This field is required')
        return email

    def clean_honeypot(self):
        honeypot = self.cleaned_data.get('honeypot')
        if honeypot != '':
            raise forms.ValidationError(u'You are not a human')
        return honeypot

    # Add extra field to the form for password confirmation input
    confirm_password = forms.CharField(widget=forms.PasswordInput())
    # Add honeypot field to catch automated bots filling out the form
    # (hidden field should be empty if a human is using it)
    honeypot = forms.CharField(widget=forms.HiddenInput, required=False)

    class Meta:
        model = User
        fields = (  # Only show these fields & in this order when generating the form
            'first_name', 'last_name', 'username',
            'email', 'confirm_password', 'password', 'honeypot'
        )
        widgets = {'password': PasswordInput}


class UserProfileForm(ModelForm):
    def clean(self):
        cleaned_data = super(UserProfileForm, self).clean()
        return cleaned_data

    class Meta:
        model = UserProfile
        fields = (  # Only show these fields & in this order when generating the form
            'organisation', 'job', 'intent_to_publish',
        )


class CaptchaTestForm(forms.Form):
    captcha = CaptchaField()
