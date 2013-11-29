from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.template import RequestContext, loader
from django.shortcuts import render_to_response

from pos.models import *

def details(request):
    return render_to_response('pos/contact_us/contact_us.html',
        {},
        context_instance=RequestContext(request)
    )
