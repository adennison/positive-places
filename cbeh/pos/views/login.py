from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.template import RequestContext, loader
from django.shortcuts import render_to_response, render
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth import authenticate
from django.core.context_processors import csrf


# Admin Login for data upload
def login_admin_data_upload(request):
    state = "Please log in below..."
    username = password = ''

    if request.POST:
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_superuser:
                if user.is_active:
                    django_login(request, user)
                    request.session.set_expiry(0) # Auto log out on browser close
                    return HttpResponseRedirect('/cbeh/pos/file_upload')
                else:
                    state = "Your account is not active, please contact the site admin."
            else:
                state = "You need Admin login privileges to upload data."
        else:
            state = "Your username and/or password were incorrect. Please try again."

    #django_logout(request) # Log the admin user out if they are already logged in, so they can log in again

    return render_to_response('pos/login/admin_login.html',
        {'state': state, 'username': username},
        context_instance=RequestContext(request)
    )


# Standard User Login for accessing Projects
def login_user(request):
    state = 'Please log in to access the following POS Tool advanced functions:'
    username = password = ''
    redirect_url = ''

    if request.POST:
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                if 'redirect_path' in request.POST:
                    redirect_url = request.POST.get('redirect_path')
                else:
                   redirect_url = '/cbeh/pos/project/advanced/'
                django_login(request, user)
                request.session.set_expiry(0) # Auto log out on browser close
                return HttpResponseRedirect(redirect_url)
            else:
                state = "Your account is not active, please contact the site admin."
        else:
            state = "Your username and/or password were incorrect. Please try again."
            if 'redirect_path' in request.POST:
                redirect_url = request.POST.get('redirect_path')

    return render_to_response('pos/login/user_login.html',
        {'state': state, 'username': username, 'redirect_url': redirect_url},
        context_instance=RequestContext(request)
    )


# Logout
def logout(request):
    django_logout(request)
    return HttpResponseRedirect('/cbeh/pos/welcome')
