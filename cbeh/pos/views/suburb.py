from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.template import RequestContext, loader


from pos.models import *

def details(request, pk):
    suburb = Suburb.objects.get(pk=pk)
    try:
        t = loader.get_template('pos/suburb/details.html')
        c = RequestContext(request, {
            'suburb' : suburb,
        })
        return HttpResponse(t.render(c))

    except Suburb.DoesNotExist:
        raise Http404, 'Suburb with pk=%s not found' % pk
