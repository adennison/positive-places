from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.template import RequestContext, loader
from django.shortcuts import render_to_response

from pos.models import *

def details(request):
    return render_to_response('pos/about/about.html',
        {},
        context_instance=RequestContext(request)
    )