from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.template import RequestContext, loader
from django.shortcuts import render, render_to_response
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.sites.models import get_current_site
from django.core.mail import EmailMultiAlternatives

from django.conf import settings

from pos.models import *
from pos.user_registration_forms import *


# Set up new users
def register(request):
    # If request was POST - saving a user
    if request.method == 'POST':
        userForm = UserForm(request.POST)
        userProfileForm = UserProfileForm(request.POST)
        captchaForm = CaptchaTestForm(request.POST)
        if userForm.is_valid() and userProfileForm.is_valid() and captchaForm.is_valid():
            userObj = userForm.save()
            # Want to get the object to apply the 1:1 relationship to User
            userProfileObj = userProfileForm.save(commit=False)
            userProfileObj.user = userObj
            userProfileObj.save()
            messages.success(request, 'Thank you for registering. A confirmation email has been sent to your email address.')
            send_user_credentials(request, userObj, request.POST.get('password', None))
            send_admin_new_user_details(request, userObj)
            # Load the template
            return HttpResponseRedirect(reverse('register'))
        # Else form(s) invalid
        else:
            messages.error(request, 'Please review the form and correct it before re-submitting.')

    # Otherwise load an empty form to create a new user
    else:
        # Create the forms with no bound data
        userForm = UserForm()
        userProfileForm = UserProfileForm()
        captchaForm = CaptchaTestForm()

    # Load the template
    t = loader.get_template('pos/registration/register.html')
    c = RequestContext(request, {
        'userForm': userForm,
        'userProfileForm': userProfileForm,
        'captchaForm': captchaForm,
    })
    return HttpResponse(t.render(c))


# Send confirmation email to a newly registered user
def send_user_credentials(request, user, password):
    site = get_current_site(request)
    c = RequestContext(request, {
        'site': site,
        'user_instance': user,
        'password': password,
    })

    txt = loader.get_template('pos/registration/register_user_email_confirmation.html')
    text_message = txt.render(c)
    # alt = loader.get_template('%s/admin/setup_people_email_alt.html' % site.name.lower())
    # html_message = alt.render(c)

    subject = 'User Registration For %s' % site.name
    from_email = settings.DEFAULT_FROM_EMAIL

    msg = EmailMultiAlternatives(subject, text_message, from_email, [user.email])
    # msg.attach_alternative(html_message, "text/html")
    try:
        msg.send()
    except:
        messages.error(request, 'Failed to send credentials to the user. Please contact your systems administrator.')


# Send email to admin with credentials of a newly registered user
def send_admin_new_user_details(request, user):
    site = get_current_site(request)
    c = RequestContext(request, {
        'site': site,
        'user_instance': user,
    })

    txt = loader.get_template('pos/registration/register_user_email_to_admin.html')
    text_message = txt.render(c)

    subject = 'New User Registration for %s' % site.name
    from_email = settings.DEFAULT_FROM_EMAIL

    admin_email = User.objects.get(pk=1).email
    msg = EmailMultiAlternatives(subject, text_message, from_email, [admin_email])
    #msg = EmailMultiAlternatives(subject, text_message, from_email, ['akealhayek@gmail.com'])  # just for local builds and testing
    try:
        msg.send()
    except:
        messages.error(request, 'Failed to send credentials to the administrator.')
