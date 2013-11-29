# Views index page
# Create your views here.
#from django.template import Context, loader
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from polls.models import Poll, Choice
#from django.http import Http404
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse

def home(request):
    return render_to_response('pos/home/details.html')

def file_upload(request):
    return render_to_response('pos/data_upload/details.html')

def search(request):
    if 'term' in request.GET:
        tags = Pos.objects.filter(name__istartswith=request.GET['term'])[:10]
        return HttpResponse(u'\n'.join(pos.name for pos in tags))
    return render_to_response('pos/search/details.html')

def pos_view(request):
    return render_to_response('pos/pos_view/details.html')

def address(request):
    return render_to_response('pos/address/details.html')

def login(request):
    return render_to_response('pos/login/details.html')