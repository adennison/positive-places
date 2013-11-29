from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.template import RequestContext, loader

from pos.models import *

# LGA View

def details(request, pk):
    lga = Lga.objects.get(pk=pk)
    try:
        t = loader.get_template('pos/lga/details.html')
        c = RequestContext(request, {
            'lga' : lga,
        })
        return HttpResponse(t.render(c))

    except Lga.DoesNotExist:
        raise Http404, 'Lga with pk=%s not found' % pk