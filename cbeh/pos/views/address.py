from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.template import RequestContext, loader
from django.shortcuts import render_to_response
from django.conf import settings

from pos.models import *

def index(request):
	return render_to_response('pos/address/details.html', {})

# def index(request):
#     t = loader.get_template('pos/address/details.html')
#     c = RequestContext(request, {
#         'geoserver_url': settings.GEOSERVER_URL
#     })
#     return HttpResponse(t.render(c))