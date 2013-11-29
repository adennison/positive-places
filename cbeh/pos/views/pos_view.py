try:
    import json
except ImportError:
    import simplejson as json

from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.template import RequestContext, loader
from django.conf import settings
from django.contrib.gis.gdal import SpatialReference, CoordTransform

from pos.models import *
from pos.views.search import *

def details(request, pk):
    pos = Pos.objects.get(pk=pk)

    # Get the centroid of the POS, to get the other nearest POS geometries
    centroid_mgaz50 = pos.mpoly.centroid
    wgs84 = CoordTransform(SpatialReference(28350), SpatialReference(4326))
    centroid_wgs84 = GEOSGeometry(centroid_mgaz50.transform(wgs84, True).wkt)
    latitude = centroid_wgs84.coords[1]
    longitude = centroid_wgs84.coords[0]

    # Find 'X' nearest Parks
    # returns 2 lists: first is a queryset with all matched data, second is a list of the uniquely matched POS Names
    nearestXPosList = pos.get_nearest_x_parks(
        longitude,
        latitude,
        NEAREST_PARKS_NUMBER,
        NEAREST_POS_NUMBER,
        POS_SEARCH_RADIUS
    )
    dataForHttp = format_pos_queryset(request, nearestXPosList)
    nearestPosList = dataForHttp[0]
    nearestPartsList = dataForHttp[1]
    posTypesList = dataForHttp[2]

    try:
        t = loader.get_template('pos/pos_view/details.html')
        c = RequestContext(request, {
            'pos' : pos,
            'latitude' : latitude,
            'longitude' : longitude,
            'nearestParksNumber' : NEAREST_PARKS_NUMBER,
            'nearestPosList' : nearestPosList[:NEAREST_PARKS_NUMBER],
            'nearestPartsListJSON' : json.dumps(nearestPartsList),
            'posTypesListJSON' : json.dumps(posTypesList),
            'geoserver_url': settings.GEOSERVER_URL
        })
        return HttpResponse(t.render(c))
    except Pos.DoesNotExist:
        raise Http404, 'Park with pk=%s not found' % pk
