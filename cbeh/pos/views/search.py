try:
    import json
except ImportError:
    import simplejson as json

from django.http import HttpResponseRedirect, HttpRequest, HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.template import RequestContext, loader
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.contrib.gis.geos import Point, GEOSGeometry
from django.contrib.gis.gdal import OGRGeometry
from django.contrib import messages
from django.conf import settings
from pos.constants import *
from pos.models import *

NEAREST_PARKS_NUMBER = 5 # Nearest X Parks Polygons To Search For
NEAREST_POS_NUMBER = 200 # Nearest X POS Polygons To Search For
POS_SEARCH_RADIUS = 50000 # Limit search radius - set to 50km

def search(request):
    if request.method == 'GET':
        # If user is typing in a Park/Suburb/LGA autocomplete text box,
        # return the autocomplete array for the dropdown box
        if 'term' in request.GET:
            if request.GET['look'] == 'park_autocomplete':
                qs = Pos.objects.filter(park_name__icontains=request.GET['term']) # case inexact
                qs = qs.filter(pos_type_c__exact=POS_TYPE_C_CHOICE_PARK)
                qs = qs.order_by('park_name')
                matchedList = format_qs_to_json(qs, 'park')
            elif request.GET['look'] == 'region_autocomplete':
                qs = Region.objects.filter(name__icontains=request.GET['term'])
                qs = (qs.filter(type__exact=REGION_TYPE_CHOICE_SUBURB)) | (qs.filter(type__exact=REGION_TYPE_CHOICE_LGA))
                matchedList = format_qs_to_json(qs, 'region')
            return HttpResponse(json.dumps(matchedList))
        # If user makes an address search request,
        # search database for nearest Parks and load results page
        elif 'geocodeLocation' in request.GET:
            addressList = format_address(request.GET['geocodeLocation'])
            latitude = float(request.GET['latitude'])
            longitude = float(request.GET['longitude'])
            # Find 'X' nearest Parks
            pos = Pos()
            nearestXPosList = pos.get_nearest_x_parks(longitude, latitude, NEAREST_PARKS_NUMBER, NEAREST_POS_NUMBER, POS_SEARCH_RADIUS) # returns 2 lists: first is a queryset with all matched data, second is a list of the uniquely matched POS Names
            dataForHttp = format_pos_queryset(request, nearestXPosList)
            if hasattr(dataForHttp, 'get_messages'):
                return render_to_response('pos/search/search.html', locals(), context_instance=RequestContext(request))
            else:
                nearestPosList = dataForHttp[0]
                nearestPartsList = dataForHttp[1]
                posTypesList = dataForHttp[2]
                t = loader.get_template('pos/address/details.html')
                c = RequestContext(request, { 'addressList' : addressList,\
                                              'latitude' : latitude, \
                                              'longitude' : longitude, \
                                              'latitude_rounded' : round(latitude, 3), \
                                              'longitude_rounded' : round(longitude, 3), \
                                              'nearestParksNumber' : NEAREST_PARKS_NUMBER, \
                                              'nearestPosList' : nearestPosList[:NEAREST_PARKS_NUMBER], \
                                              'nearestPartsListJSON' : json.dumps(nearestPartsList), \
                                              'posTypesListJSON' : json.dumps(posTypesList), \
                                              'geoserver_url': settings.GEOSERVER_URL
                                            })
                return HttpResponse(t.render(c))
        # Otherwise user just hit the search page, so load it
        else:
            t = loader.get_template('pos/search/search.html')
            c = RequestContext(request, {
                #'pos_list' : Pos.objects.order_by('name').distinct('name'),
                #'lga_list' : Region.objects.filter(type='LGA'),
                #'suburb_list' : Region.objects.filter(type='SUB'),
            })
            return HttpResponse(t.render(c))

    # Otherwise the user hit 'Search' for a Park or Suburb/LGA
    elif request.method == 'POST':
        # (1) Receive Park Search from user - redirect to POS page
        if 'park_pk' in request.POST:
            park = Pos.objects.get(pk=request.POST['park_pk'])
            return HttpResponseRedirect(park.get_absolute_url())
        # (2) Receive Region Search from user - redirect to Regions page
        elif 'region_pk' in request.POST:
            region = Region.objects.get(pk=request.POST['region_pk'])
            return HttpResponseRedirect(region.get_absolute_url())

    # Anything else - load the Search page
    else:
        t = loader.get_template('pos/search/search.html')
        c = RequestContext(request, {
            #'pos_list' : Pos.objects.order_by('name').distinct('name'),
            #'lga_list' : Region.objects.filter(type='LGA'),
            #'suburb_list' : Region.objects.filter(type='SUB'),
        })
        return HttpResponse(t.render(c))

# Format textual address into a list before sending to HTTP (for formatting)
def format_address(addressText):
    if addressText[-11:].lower() == ', australia':
        addressText = addressText[:-11]
        # get 1st comma and split
        commaIndex = addressText.find(',')
        if commaIndex > 0:
            addressList = [addressText[:commaIndex+1], addressText[commaIndex+2:]]
            return addressList
    else:
        return addressText

# Format the geoqueryset of nearest POSs for easy display before sending to HTTP
# Return 2 lists of dictionaries, inside an outer list
#   1st list as 'posList' below
#   2nd list as 'partsList' below
#   3rd list as 'typesList' below - unique list of pos_type_c values, for later layer creation
def format_pos_queryset(userRequest, querysetList):
    if not querysetList: # i.e. if queryset is empty
        messages.error(userRequest, 'No parks found within ' + str(POS_SEARCH_RADIUS)[:-3] + 'km of your search location. Please try searching again.')
        return messages
    else:
        counter = 0
        posList = []
        partsList = []
        typesList = []
        categoryList = []
        for pos in querysetList:
            posTypeDesc = pos.get_pos_type_desc()
            if {'description' : posTypeDesc} not in typesList:
                typesList.append({'description' : posTypeDesc})
            counter = counter + 1
            distanceMetres = pos.distance.m
            distanceVal = str(int(distanceMetres)) + ' m'
            # Find the categories that these POSs' facilities are in
            facilities = Facility.objects.filter(pos_pk_id=pos.pk) # get all facilities for this POS part
            if facilities.exists(): # if not an empty queryset
                categoryList = [] # Reset back to empty
                for oneFacility in facilities:
                    category = oneFacility.get_category()
                    if (category != ''):
                        if (category not in categoryList):
                            categoryList.append(category)
            parkName = pos.park_name
            if not parkName:
                parkName = 'Park'
            posList.append( {   'pos_pk' : pos.pk, \
                                'name' : parkName, \
                                #'pos_wkt' : pos.get_part_mpoly_wgs().wkt, \
                                'distance' : distanceVal, \
                                'quality_child' : pos.qual_child, \
                                'quality_adolescent' : pos.qual_adole, \
                                'quality_adult' : pos.qual_adult, \
                                'category_list' : sorted(categoryList)
                            } )
            partsList.append( {
                                'pos_pk' : pos.pk, \
                                'name' : parkName, \
                                'pos_type_c' : pos.get_pos_type_desc(), \
                                'adj_bush' : pos.adj_bf, \
                                'pos_wkt' : pos.get_mpoly_wgs().wkt
                            } )
        return [ posList, partsList, typesList ]

# Format a queryset to a list in preparation to return to HTTP
# If a POS queryset input, does not include duplicated park names
def format_qs_to_json(queryset, type):
    itemNameList = []
    formattedList = []
    for item in queryset:
        if item not in itemNameList:
            itemNameList.append(item)
            if type == 'park':
                formattedList.append( {
                                        'label' : item.park_name, \
                                        'value' : item.pk
                                    } )
            elif type == 'region':
                formattedList.append( {
                                        'label' : item.name, \
                                        'value' : item.pk
                                    } )
    return formattedList

def ajax_bbox_pos(request):
    srid = int(request.GET.get('srid'), 10)
    bbox = GEOSGeometry(request.GET.get('bbox'), srid=srid)

    data = []
    for pos in Pos.objects.filter(mpoly__intersects=bbox):
        pos_data = {
            'pos_pk' : pos.pk,
            'name' : pos.park_name,
            'pos_type_c' : pos.get_pos_type_desc(),
            'adj_bush' : pos.adj_bf,
            'pos_wkt' : pos.get_mpoly_wgs().wkt
        }
        data.append(pos_data)
    return HttpResponse(json.dumps(data), mimetype='application/json')

