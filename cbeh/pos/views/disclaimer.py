from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.template import RequestContext, loader
from django.shortcuts import render_to_response
from django.core.context_processors import csrf

from pos.models import *

def details(request):
    if request.POST:
        # Continue to search page if user has agreed to the disclaimer info
        # First set a cookie if it doesn't already exist
        if request.COOKIES.has_key('after_disclaimer_redirect_path'):
            redirectPath = request.COOKIES['after_disclaimer_redirect_path']
        else:
            redirectPath = '/cbeh/pos/search'
        response = HttpResponseRedirect(redirectPath)
        response.set_cookie('pos_disclaimer_cookie', 'has_agreed') # Overwrites any existing cookie with the same name
        return response
    else:
        return render_to_response('pos/disclaimer/details.html',
                                    {},
                                    context_instance=RequestContext(request))
