from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.template import RequestContext, loader
from django.shortcuts import render_to_response
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import GEOSGeometry

from pos.models import *
from pos.statistics import build_stats

# POS People nominated the maximum area allowed for a user region
MAXIMUM_AREA_HA = 5000

# Draw or modify a user_region
@login_required()
def draw_user_region(request, pk):
    try:
        # Check if the currently logged in user is loading their own project/region
        user = request.user
        userRegion = Region.objects.get(pk=pk)
        project = userRegion.project
        if user != project.user:
            raise Http404, 'User %s does not own project %s with primary key= %s' % (user.username, project.project_name, pk)

        # Check if there is any region polygon
        userRegionPolygon = userRegion.mpoly
        if userRegionPolygon is None:
            c = RequestContext(request, {
                'project': project,
                'userRegionPk': userRegion.pk,
                'userRegionWkt': 'false',
                'max_hectares': MAXIMUM_AREA_HA,
                'geoserver_url': settings.GEOSERVER_URL
            })
        else:
            c = RequestContext(request, {
                'project': project,
                'userRegionPk': userRegion.pk,
                'userRegionWkt': userRegion.get_mpoly_wgs()[0].wkt,  # get the single polygon
                'max_hectares': MAXIMUM_AREA_HA,
                'geoserver_url': settings.GEOSERVER_URL
            })
        t = loader.get_template('pos/user_region/draw_user_region.html')
        return HttpResponse(t.render(c))

    except Region.DoesNotExist:
        raise Http404, 'User Region with primary key= %s not found' % pk

    except Project.DoesNotExist:
        raise Http404, 'This region with primary key= %s does not belong to any project' % pk

# Upload a new user_region or overwrite an existing one by uploading again
@login_required()
def upload_user_region(request, pk):
    try:
        # Check if the currently logged in user is loading their own project/region
        user = request.user
        userRegion = Region.objects.get(pk=pk)
        project = userRegion.project
        if user != project.user:
            raise Http404, 'User %s does not own project %s with primary key= %s' % (user.username, project.project_name, pk)

        # Check if there is any region polygon
        userRegionPolygon = userRegion.mpoly
        if userRegionPolygon is None:
            c = RequestContext(request, {
                'project': project,
                'userRegionPk': userRegion.pk,
                'userRegionWkt': 'false',
                'max_hectares': MAXIMUM_AREA_HA,
                'geoserver_url': settings.GEOSERVER_URL
            })
        else:
            c = RequestContext(request, {
                'project': project,
                'userRegionPk': userRegion.pk,
                'userRegionWkt': userRegion.get_mpoly_wgs()[0].wkt,  # get the single polygon
                'max_hectares': MAXIMUM_AREA_HA,
                'geoserver_url': settings.GEOSERVER_URL
            })
        t = loader.get_template('pos/user_region/upload_user_region.html')
        return HttpResponse(t.render(c))

    except Region.DoesNotExist:
        raise Http404, 'User Region with primary key= %s not found' % pk

    except Project.DoesNotExist:
        raise Http404, 'This region with primary key= %s does not belong to any project' % pk

# Upload a new user_region or overwrite an existing one by uploading again
@login_required()
def select_lga_suburb_user_region(request, pk):
    try:
        # Check if the currently logged in user is loading their own project/region
        user = request.user
        userRegion = Region.objects.get(pk=pk)
        project = userRegion.project
        if user != project.user:
            raise Http404, 'User %s does not own project %s with primary key= %s' % (user.username, project.project_name, pk)

        # Check if there is any region polygon
        userRegionPolygon = userRegion.mpoly
        if userRegionPolygon is None:
            c = RequestContext(request, {
                'project': project,
                'userRegionPk': userRegion.pk,
                'userRegionWkt': 'false'
            })
        else:
            c = RequestContext(request, {
                'project': project,
                'userRegionPk': userRegion.pk,
                'userRegionWkt': userRegion.get_mpoly_wgs()[0].wkt  # get the single polygon
            })
        t = loader.get_template('pos/user_region/select_lga_suburb_user_region.html')
        return HttpResponse(t.render(c))

    except Region.DoesNotExist:
        raise Http404, 'User Region with primary key= %s not found' % pk

    except Project.DoesNotExist:
        raise Http404, 'This region with primary key= %s does not belong to any project' % pk


# Save the region polygon drawn on the OpenLayers map
# Also works for a user region selected from an existing LGA/Suburb page
# AJAX Post
@login_required()
def save_user_region_polygon(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    # Get data from the request
    wgs84_wkt = request.POST.get('wkt')
    pk = request.POST.get('user_region_pk')

    # Get the Polygon from another Region or from the drawn feature
    if wgs84_wkt == 'from_existing_region':
        from_region_pk = request.POST.get('from_region_pk')
        from_region = Region.objects.get(pk=from_region_pk)
        # Update the Region's type field with the from_region
        upd_region = Region.objects.get(pk=pk)
        upd_region.type = REGION_TYPE_CHOICE_USER_LGA_SUBURB
        upd_region.save()
        multiPolygon = from_region.mpoly
    else:
        # Turn the WGS84 WKT into MGA Zone 50 GEOS Geometry
        polygon = GEOSGeometry('SRID=4326;' + wgs84_wkt)
        polygon.transform(28350)
        multiPolygon = MultiPolygon(polygon)
        multiPolygon_area_ha = multiPolygon.area / 10000

    response_data = {
        'issue': False,
        'message': 'Good'
    }

    # No need to validate if copying an existing region
    if wgs84_wkt != 'from_existing_region':
        # Validate the geometry
        if multiPolygon_area_ha > MAXIMUM_AREA_HA:
            response_data['issue'] = True
            response_data['message'] = 'Your area of %.2f hectares is greater than the maximum allowed of %.0f hectares. Please modify your region.' % (multiPolygon_area_ha, MAXIMUM_AREA_HA)
            return HttpResponse(json.dumps(response_data, indent=2),
            mimetype="application/json"
        )
        elif polygon.valid == False:
            response_data['issue'] = True
            response_data['message'] = 'Your region has invalid geometry. Please modify your region.'
            return HttpResponse(json.dumps(response_data, indent=2),
            mimetype="application/json"
        )

    # Save geometry into database
    user_region = Region.objects.get(pk=pk)
    user_region.mpoly = multiPolygon
    user_region.save()

    if user_region.type[:2] == REGION_TYPE_CHOICE_USER_LGA_SUBURB:
        # Build the initial scenario modelling area and population statistics
        create_user_stats(user_region.project, True, True, from_region)
        # Copy the Area and Pop stats from the original LGA/Suburb region
        check_area_pop_stats = Area_Pop_Stats.objects.filter(region_pk=user_region)
        if check_area_pop_stats.exists():
            check = True
        else:
            check = False
        for orig_area_pop_stat in Area_Pop_Stats.objects.filter(region_pk=from_region):
            if check == False:
                # Save a new model object if it doesn't exist
                orig_area_pop_stat.pk = None
                orig_area_pop_stat.region_pk = user_region
                orig_area_pop_stat.save()
            else:
                # Overwrite the existing object if it does exist
                area_pop_stat = check_area_pop_stats.get(
                    park_type=orig_area_pop_stat.park_type,
                    dsr_type=orig_area_pop_stat.dsr_type,
                    region_stat=orig_area_pop_stat.region_stat
                )
                area_pop_stat.region_value = orig_area_pop_stat.region_value
                area_pop_stat.save()

        check_abs_stats = ABS_Region_Population.objects.filter(sub_lga_id=user_region.sub_lga_id)
        abs_pop_stat = ABS_Region_Population.objects.get(sub_lga_id=from_region.sub_lga_id)
        if not check_abs_stats.exists():
            # Save a new model object if doesn't exist
            abs_pop_stat.pk = None
            abs_pop_stat.sub_lga_id = user_region.sub_lga_id
            abs_pop_stat.type = user_region.type
            abs_pop_stat.save()
        else:
            # Overwrite the existing object if it does exist
            existing_abs_stats = check_abs_stats[0]
            existing_abs_stats.tot_p_p = abs_pop_stat.tot_p_p
            existing_abs_stats.age_0_4__2 = abs_pop_stat.age_0_4__2
            existing_abs_stats.age_5_14_2 = abs_pop_stat.age_5_14_2
            existing_abs_stats.age_15_192 = abs_pop_stat.age_15_192
            existing_abs_stats.age_20_242 = abs_pop_stat.age_20_242
            existing_abs_stats.age_25_342 = abs_pop_stat.age_25_342
            existing_abs_stats.age_35_442 = abs_pop_stat.age_35_442
            existing_abs_stats.age_45_542 = abs_pop_stat.age_45_542
            existing_abs_stats.age_55_642 = abs_pop_stat.age_55_642
            existing_abs_stats.age_65_742 = abs_pop_stat.age_65_742
            existing_abs_stats.age_75_842 = abs_pop_stat.age_75_842
            existing_abs_stats.age_85ov_p = abs_pop_stat.age_85ov_p
            existing_abs_stats.save()

        # Get stats from existing LGA/Suburb
        facility_stats = Facility_Statistics.objects.filter(region_pk=from_region)
        region_facility_stats = Facility_Statistics.objects.filter(region_pk=user_region)
        if region_facility_stats.exists():
            # If objects exist just copy the count values from the LGA/Suburb
            for region_stat in region_facility_stats:
                facility_stat = facility_stats.filter(
                    park_type=region_stat.park_type).filter(
                    facility_stat=region_stat.facility_stat)[0]
                region_stat.facility_count = facility_stat.facility_count
                region_stat.save()
        else:
            # Create new objects and copy them from LGA/Suburb
            for facility_stat in facility_stats:
                facility_stat.pk = None
                facility_stat.region_pk = user_region
                facility_stat.save()
    else:
        # Calculate the area and population statistics for the new/edited polygon
        calculate_population(user_region)
        build_stats.areaPosStats_userRegion(pk)
        # Calculate the Facility statistics
        build_stats.getFacilityStats(user_region)
        # Build the initial scenario modelling area and population statistics
        create_user_stats(user_region.project, True, True)

    return HttpResponse(json.dumps(response_data, indent=2),
        mimetype="application/json"
    )

# Calculate and store the user region population figures
def calculate_population(user_region):
    # Get all SA1's that intersect with the user region
    sa1s = ABS_SA1.objects.filter(mpoly__intersects=user_region.mpoly)
    # Get the ratio between the 'total area of each SA1' and the 'intersecting region area'
    sa1_area_dict = {}
    for sa1 in sa1s:
        area = sa1.mpoly.area
        region_area_intersect = user_region.mpoly.intersection(sa1.mpoly).area
        sa1_area_dict[sa1.sa1_7digit] = {'ratio': region_area_intersect / area}
    # Cycle through each population figure and apply the ratio to the region
    popRow = get_pop_row(user_region)
    for currentStat in ABS_FIELD_STATS:
        sum_population = 0
        stat_field = currentStat[1]
        for sa1 in sa1s:
            pop_figure =  getattr(sa1, stat_field)
            pop_proportion = sa1_area_dict[sa1.sa1_7digit]['ratio'] * pop_figure
            sum_population = sum_population + pop_proportion
        setattr(popRow, stat_field, sum_population)
    popRow.sub_lga_id = user_region.sub_lga_id
    popRow.type = REGION_TYPE_CHOICE_USER
    popRow.save()

# Create/Reset initial park area and population numbers for scenario modelling
def create_user_stats(project, reset_areas, reset_populations, *args):

    # Get the user stat data row
    user_stat = User_Statistic.objects.get(project=project)

    # Area stats
    if reset_areas == True:
        # If this is copying the data from an existing region
        if args:
            from_region =  args[0] # Get the item out of the tuple

            park_stats = Area_Pop_Stats.objects.filter(
            region_pk=from_region
            ).filter(
                park_type__gte=1
            ).filter(
                region_stat='sum_area_ha'
            ).order_by(
                'park_type'
            ).values(
                'park_type', 'region_value', 'region_stat'
            )
        else:
            park_stats = Area_Pop_Stats.objects.filter(
                region_pk=project.region
            ).filter(
                park_type__gte=1
            ).filter(
                region_stat='sum_area_ha'
            ).order_by(
                'park_type'
            ).values(
                'park_type', 'region_value', 'region_stat'
            )

        # Multiplier to convert hectares to square metres
        sq_m = 10000

        user_stat.all_parks = park_stats[0]['region_value'] * sq_m
        user_stat.pocket_park = park_stats[5]['region_value'] * sq_m
        user_stat.small_park = park_stats[6]['region_value'] * sq_m
        user_stat.medium_park = park_stats[7]['region_value'] * sq_m
        user_stat.large_park_1 = park_stats[8]['region_value'] * sq_m
        user_stat.large_park_2 = park_stats[9]['region_value'] * sq_m
        user_stat.district_park_1 = park_stats[10]['region_value'] * sq_m
        user_stat.district_park_2 = park_stats[11]['region_value'] * sq_m
        user_stat.regional_space = park_stats[12]['region_value'] * sq_m

    # Population stats
    if reset_populations == True:
        if args:
            population_stats = ABS_Region_Population.objects.get(sub_lga_id=from_region.sub_lga_id)
        else:
            population_stats = ABS_Region_Population.objects.get(sub_lga_id=project.region.sub_lga_id)

        user_stat.age_0_4 = population_stats.age_0_4__2
        user_stat.age_5_14 = population_stats.age_5_14_2
        user_stat.age_15_19 = population_stats.age_15_192
        user_stat.age_20_24 = population_stats.age_20_242
        user_stat.age_25_34 = population_stats.age_25_342
        user_stat.age_35_44 = population_stats.age_35_442
        user_stat.age_45_54 = population_stats.age_45_542
        user_stat.age_55_64 = population_stats.age_55_642
        user_stat.age_65_74 = population_stats.age_65_742
        user_stat.age_75_84 = population_stats.age_75_842
        user_stat.age_85_plus = population_stats.age_85ov_p
        user_stat.total_pop = population_stats.tot_p_p

    user_stat.save()

# Create a ABS Region Population table row if it doesn't already exist
def get_pop_row(user_region):
    try:
        pop_row = ABS_Region_Population.objects.get(sub_lga_id=user_region.sub_lga_id)
    except ObjectDoesNotExist:
        pop_row = ABS_Region_Population()
    return pop_row
