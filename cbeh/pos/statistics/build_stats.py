from django.db.models import Sum
# from django import db
from django.db import connection

from datetime import datetime
from copy import copy

from pos.models import *
from pos.constants import *

# Calculate POS stats for every LGA and Suburb region
def areaPosStats():
    # Delete all records from the area_pop_stats table if it's not a custom user region
    # Area_Pop_Stats.objects.all().delete()
    qs = Area_Pop_Stats.objects.exclude(region_pk__type=REGION_TYPE_CHOICE_USER) # Get all regions excluding the User regions
    qs = qs.exclude(region_pk__type__contains=REGION_TYPE_CHOICE_USER_LGA_SUBURB) # Exlude Special User Regions
    if qs.exists():
        qs.delete() # Delete occurs only if there is anything to delete

    # Loop through regions table
    counter = 0
    for currentRegion in Region.objects.all().order_by('type','name'):
        if (currentRegion.type == REGION_TYPE_CHOICE_SUBURB) or (currentRegion.type == REGION_TYPE_CHOICE_LGA):
            counter = counter + 1
            # print str(counter) + ") " + currentRegion.name

            # Get the current region id
            regionID = currentRegion.id

            getPosStats(regionID)

# Calculate POS stats for every LGA only (not Suburbs or user regions)
def areaPosStats_lgas():
    # Delete all records from the area_pop_stats table if it's not a custom user region or Suburb
    qs = Area_Pop_Stats.objects.exclude(region_pk__type=REGION_TYPE_CHOICE_USER).exclude(region_pk__type=REGION_TYPE_CHOICE_SUBURB) # Get all regions excluding the Suburbs and User regions
    qs = qs.exclude(region_pk__type__contains=REGION_TYPE_CHOICE_USER_LGA_SUBURB) # Exlude Special User Regions
    if qs.exists():
        qs.delete() # Delete occurs only if there is anything to delete

    # Loop through regions table
    counter = 0
    for currentRegion in Region.objects.all().order_by('type','name'):
        if currentRegion.type == REGION_TYPE_CHOICE_LGA:
            counter = counter + 1
            # print str(counter) + ") " + currentRegion.name

            # Get the current region id
            regionID = currentRegion.id

            getPosStats(regionID)

# Calculate POS stats for every Suburb only (not LGAs or user regions)
def areaPosStats_suburbs():
    # Delete all records from the area_pop_stats table if it's not a custom user region or LGA
    qs = Area_Pop_Stats.objects.exclude(region_pk__type=REGION_TYPE_CHOICE_USER).exclude(region_pk__type=REGION_TYPE_CHOICE_LGA) # Get all regions excluding the LGAs and User regions
    qs = qs.exclude(region_pk__type__contains=REGION_TYPE_CHOICE_USER_LGA_SUBURB) # Exlude Special User Regions
    if qs.exists():
        qs.delete() # Delete occurs only if there is anything to delete

    # Loop through regions table
    counter = 0
    for currentRegion in Region.objects.all().order_by('type','name'):
        if currentRegion.type == REGION_TYPE_CHOICE_SUBURB:
            counter = counter + 1
            # print str(counter) + ") " + currentRegion.name

            # Get the current region id
            regionID = currentRegion.id

            getPosStats(regionID)

# Calculate POS stats for 1 user region
def areaPosStats_userRegion(regionID):
    # First check if this regionID has data in the table already
    # If so delete it before creating new data
    qs = Area_Pop_Stats.objects.filter(region_pk=regionID)
    if qs.exists():
        qs.delete()
    getPosStats(regionID)

# Go ahead and calculate all the stats for a region
def getPosStats(regionID):
    start_time = datetime.now()
    # Calculate region area
    region = Region.objects.get(pk=regionID)
    regionArea = region.mpoly.area * 0.0001
    # regionArea = round(region.mpoly.area * 0.0001,2)


    # if region.type == REGION_TYPE_CHOICE_LGA:
    #   lgaPolys = ABS_LGA.objects.get(lga_code=region.sub_lga_id)
    # elif (region.type == REGION_TYPE_CHOICE_SUBURB) or (region.type == REGION_TYPE_CHOICE_USER):
    #   lgaPolys = Region.objects.filter(mpoly__intersects=region.mpoly)

    # Get the population data for the current region
    regionPopulation = ABS_Region_Population.objects.get(sub_lga_id=region.sub_lga_id)

    # lgaPolys = ABS_LGA.objects.get(lga_code="LGA51820")
    # print ''
    # print lgaPolys
    # print ''

    # Calculate total park area
    posPark = Pos.objects.filter(mpoly__intersects=region.mpoly).filter(pos_type_c = POS_TYPE_C_CHOICE_PARK)
    parkArea = 0
    for pos in posPark.area('mpoly'):
        parkArea = parkArea + pos.area.sq_km * 100
    totalParkArea = round(parkArea, 2)

    # # Calculate total park area
    # parkArea = 0
    # for pos in posPark:
    #   parkArea = parkArea + region.mpoly.intersection(pos.mpoly).area
    # totalParkArea = round(parkArea / 10000)

    # Calculate total pos area
    posExclude = Pos.objects.filter(mpoly__intersects=region.mpoly).filter(pos_type_c__in=[POS_TYPE_C_CHOICE_PARK, POS_TYPE_C_CHOICE_NATURAL, POS_TYPE_C_CHOICE_RESIDUAL_GREEN_SPACE])  # All parks
    posArea = 0
    for pos in posExclude.area('mpoly'):
        posArea = posArea + pos.area.sq_km * 100
    totalPosArea = round(posArea, 2)

    # # Create Unioned Catchment polygons for all Parks (6-13) and all DSRs (16-20)
    # parkCatchments = Catchment_Polygon.objects.filter(park_type__gte=7)  # leave out 6
    # unionedParkCatchments = Catchment_Polygon.objects.get(park_type=6).mpoly
    # for parkCatchment in parkCatchments:
    #   unionedParkCatchments = unionedParkCatchments.union(parkCatchment.mpoly)
    # parkCatchmentObj = Catchment_Polygon()
    # parkCatchmentObj.park_type = 1
    # parkCatchmentObj.dsr_type = 0
    # parkCatchmentObj.mpoly = unionedParkCatchments
    # parkCatchmentObj.save()
    # dsrCatchments = Catchment_Polygon.objects.filter(dsr_type__gte=17) # leave out 16
    # unionedDsrCatchments = Catchment_Polygon.objects.get(dsr_type=16).mpoly
    # for dsrCatchment in dsrCatchments:
    #   unionedDsrCatchments = unionedDsrCatchments.union(dsrCatchment.mpoly)
    # dsrCatchmentObj = Catchment_Polygon()
    # dsrCatchmentObj.park_type = 0
    # dsrCatchmentObj.dsr_type = 1
    # dsrCatchmentObj.mpoly = unionedDsrCatchments
    # dsrCatchmentObj.save()

    # Loop through pos types (1-5)
    for currentPosTup in POS_TYPE_C_CHOICES:
        currentPosType = currentPosTup[0]

        addCountStat(region, regionID, currentPosType, 0)
        addAreaStat(region, regionID, currentPosType, 0)

        if currentPosType == POS_TYPE_C_CHOICE_PARK:
            addPercentParkStat(region, regionID, currentPosType, 0, totalParkArea)
            addPercentPosStat(region, regionID, currentPosType, 0, totalPosArea)
            addPercentSubLgaStat(region, regionID, currentPosType, 0, regionArea)
            # addCatchmentStat(lgaPolys, region, regionID, currentPosType, 0)
            addCatchmentStat(regionPopulation, region, regionID, currentPosType, 0)
        elif currentPosType == POS_TYPE_C_CHOICE_NATURAL or currentPosType == POS_TYPE_C_CHOICE_RESIDUAL_GREEN_SPACE:
            addPercentPosStat(region, regionID, currentPosType, 0, totalPosArea)
            addPercentSubLgaStat(region, regionID, currentPosType, 0, regionArea)
        elif currentPosType == POS_TYPE_C_CHOICE_SCHOOL_GROUNDS:
            addPercentSubLgaStat(region, regionID, currentPosType, 0, regionArea)

    # Loop through park types (6-13)
    for currentParkTup in PARK_TYPE_CHOICES:
        currentParkType = currentParkTup[0]

        addCountStat(region, regionID, currentParkType, 0)
        addAreaStat(region, regionID, currentParkType, 0)
        addPercentParkStat(region, regionID, currentParkType, 0, totalParkArea)
        addPercentPosStat(region, regionID, currentParkType, 0, totalPosArea)
        addPercentSubLgaStat(region, regionID, currentParkType, 0, regionArea)
        # addCatchmentStat(lgaPolys, region, regionID, currentParkType, 0)
        addCatchmentStat(regionPopulation, region, regionID, currentParkType, 0)

    # DSR Type 1 (i.e. figures for all DSR catchments unioned)
    currentDsrType = 1
    # addCatchmentStat(lgaPolys, region, regionID, 0, currentDsrType)
    addCatchmentStat(regionPopulation, region, regionID, 0, currentDsrType)
    # Loop through the rest of the dsr types (16-20)
    for currentDsrTup in DSR_TYPE_CHOICES:
        currentDsrType = currentDsrTup[0]
        # addCatchmentStat(lgaPolys, region, regionID, 0, currentDsrType)
        addCatchmentStat(regionPopulation, region, regionID, 0, currentDsrType)

    # Calculate extra stats (14, 15)
    for currentType in (STAT_TYPE_CHOICE_TOTAL_POS, STAT_TYPE_CHOICE_TOTAL_POS_PLUS_SCHOOLS):
        if currentType == STAT_TYPE_CHOICE_TOTAL_DSR:
            addCountStat(region, region, regionID, 0, currentType)
            addAreaStat(region, regionID, 0, currentType)
            addPercentSubLgaStat(region, regionID, 0, currentType, regionArea)

        if currentType == STAT_TYPE_CHOICE_TOTAL_PARKS:
            addCountStat(region, regionID, currentType, 0)
            addAreaStat(region, regionID, currentType, 0)
            addPercentSubLgaStat(region, regionID, currentType, 0, regionArea)
        else:
            addCountStat(region, regionID, currentType, 0)
            addAreaStat(region, regionID, currentType, 0)
            addPercentSubLgaStat(region, regionID, currentType, 0, regionArea)
    # print ''
    # print 'Elapsed time: ', datetime.now() - start_time
    # print ''

# Calculate frequency stat
def addCountStat(region, regionID, parkType, dsrType):
    if parkType in ([x[0] for x in POS_TYPE_C_CHOICES]):
        posFrequency = Pos.objects.filter(mpoly__intersects=region.mpoly).filter(pos_type_c = parkType)
    elif parkType in ([x[0] for x in PARK_TYPE_CHOICES]):
        posFrequency = Pos.objects.filter(mpoly__intersects=region.mpoly).filter(park_type = parkType)
    elif parkType == STAT_TYPE_CHOICE_TOTAL_POS:
        posFrequency = Pos.objects.filter(mpoly__intersects=region.mpoly).filter(pos_type_c__in=[POS_TYPE_C_CHOICE_PARK, POS_TYPE_C_CHOICE_NATURAL, POS_TYPE_C_CHOICE_RESIDUAL_GREEN_SPACE])
    elif parkType == STAT_TYPE_CHOICE_TOTAL_POS_PLUS_SCHOOLS:
        posFrequency = Pos.objects.filter(mpoly__intersects=region.mpoly).filter(pos_type_c__in=[POS_TYPE_C_CHOICE_PARK, POS_TYPE_C_CHOICE_NATURAL, POS_TYPE_C_CHOICE_RESIDUAL_GREEN_SPACE, POS_TYPE_C_CHOICE_SCHOOL_GROUNDS])
    else:
        posFrequency = {}

    frequencyStat = len(posFrequency)

    regionStat = "frequency"

    r = Area_Pop_Stats(region_pk_id = regionID, park_type = parkType, dsr_type = dsrType, region_stat = regionStat, region_value = str(frequencyStat))
    r.save()

# Calculate sum_area_ha stat
def addAreaStat(region, regionID, parkType, dsrType):
    if parkType in ([x[0] for x in POS_TYPE_C_CHOICES]):
        posExclude = Pos.objects.filter(mpoly__intersects=region.mpoly).filter(pos_type_c = parkType)
    elif parkType in ([x[0] for x in PARK_TYPE_CHOICES]):
        posExclude = Pos.objects.filter(mpoly__intersects=region.mpoly).filter(park_type = parkType)
    elif parkType == STAT_TYPE_CHOICE_TOTAL_POS:
        posExclude = Pos.objects.filter(mpoly__intersects=region.mpoly).filter(pos_type_c__in=[POS_TYPE_C_CHOICE_PARK, POS_TYPE_C_CHOICE_NATURAL, POS_TYPE_C_CHOICE_RESIDUAL_GREEN_SPACE])
    elif parkType == STAT_TYPE_CHOICE_TOTAL_POS_PLUS_SCHOOLS:
        posExclude = Pos.objects.filter(mpoly__intersects=region.mpoly).filter(pos_type_c__in=[POS_TYPE_C_CHOICE_PARK, POS_TYPE_C_CHOICE_NATURAL, POS_TYPE_C_CHOICE_RESIDUAL_GREEN_SPACE, POS_TYPE_C_CHOICE_SCHOOL_GROUNDS])
    else:
        posExclude = {}

    if len(posExclude) > 0:
        posArea = 0
        for pos in posExclude.area('mpoly'):
            posArea = posArea + pos.area.sq_km * 100
        areaStat = round(posArea, 2)
    else:
        areaStat = 0

    regionStat = "sum_area_ha"

    r = Area_Pop_Stats(region_pk_id = regionID, park_type = parkType, dsr_type = dsrType, region_stat = regionStat, region_value = str(areaStat))
    r.save()

# Calculate percentpark stat
def addPercentParkStat(region, regionID, parkType, dsrType, totalParkArea):
    # Calculate area
    if parkType in ([x[0] for x in POS_TYPE_C_CHOICES]):
        posExclude = Pos.objects.filter(mpoly__intersects=region.mpoly).filter(pos_type_c = parkType)
    elif parkType in ([x[0] for x in PARK_TYPE_CHOICES]):
        posExclude = Pos.objects.filter(mpoly__intersects=region.mpoly).filter(park_type = parkType)
    elif parkType == STAT_TYPE_CHOICE_TOTAL_POS:
        posExclude = Pos.objects.filter(mpoly__intersects=region.mpoly).filter(pos_type_c__in=[POS_TYPE_C_CHOICE_PARK, POS_TYPE_C_CHOICE_NATURAL, POS_TYPE_C_CHOICE_RESIDUAL_GREEN_SPACE])
    elif parkType == STAT_TYPE_CHOICE_TOTAL_POS_PLUS_SCHOOLS:
        posExclude = Pos.objects.filter(mpoly__intersects=region.mpoly).filter(pos_type_c__in=[POS_TYPE_C_CHOICE_PARK, POS_TYPE_C_CHOICE_NATURAL, POS_TYPE_C_CHOICE_RESIDUAL_GREEN_SPACE, POS_TYPE_C_CHOICE_SCHOOL_GROUNDS])
    else:
        posExclude = {}

    if len(posExclude) > 0:
        posArea = 0
        for pos in posExclude.area('mpoly'):
            posArea = posArea + pos.area.sq_km * 100
        # posArea = 0
        # for pos in posExclude:
        #   posArea = posArea + region.mpoly.intersection(pos.mpoly).area
        # posArea = posArea / 10000
        # print ''
        # print posArea
        # print ''
    else:
        posArea = 0

    # if the area is not 0 do the % calc
    if posArea == 0:
        areaStat = 0
    else:
        areaStat = round((100 / totalParkArea) * posArea, 2)

    regionStat = "percentpark"

    # Save the record
    r = Area_Pop_Stats(region_pk_id = regionID, park_type = parkType, dsr_type = dsrType, region_stat = regionStat, region_value = str(areaStat))
    r.save()

    # posExclude = {}

# Calculate percentpos stat
def addPercentPosStat(region, regionID, parkType, dsrType, totalPosArea):
    # Calculate area
    if parkType in ([x[0] for x in POS_TYPE_C_CHOICES]):
        posExclude = Pos.objects.filter(mpoly__intersects=region.mpoly).filter(pos_type_c = parkType)
    elif parkType in ([x[0] for x in PARK_TYPE_CHOICES]):
        posExclude = Pos.objects.filter(mpoly__intersects=region.mpoly).filter(park_type = parkType)
    elif parkType == STAT_TYPE_CHOICE_TOTAL_POS:
        posExclude = Pos.objects.filter(mpoly__intersects=region.mpoly).filter(pos_type_c__in=[POS_TYPE_C_CHOICE_PARK, POS_TYPE_C_CHOICE_NATURAL, POS_TYPE_C_CHOICE_RESIDUAL_GREEN_SPACE])
    elif parkType == STAT_TYPE_CHOICE_TOTAL_POS_PLUS_SCHOOLS:
        posExclude = Pos.objects.filter(mpoly__intersects=region.mpoly).filter(pos_type_c__in=[POS_TYPE_C_CHOICE_PARK, POS_TYPE_C_CHOICE_NATURAL, POS_TYPE_C_CHOICE_RESIDUAL_GREEN_SPACE, POS_TYPE_C_CHOICE_SCHOOL_GROUNDS])
    else:
        posExclude = {}

    if len(posExclude) > 0:
        posArea = 0
        for pos in posExclude.area('mpoly'):
            posArea = posArea + pos.area.sq_km * 100
    else:
        posArea = 0

    # if the area is not 0 do the % calc
    if posArea == 0:
        areaStat = 0
    else:
        areaStat = round((posArea / totalPosArea) * 100, 2)

    regionStat = "percentpos"

    # Save the record
    r = Area_Pop_Stats(region_pk_id = regionID, park_type = parkType, dsr_type = dsrType, region_stat = regionStat, region_value = str(areaStat))
    r.save()

    # posExclude = {}

# Calculate percentsublga stat
def addPercentSubLgaStat(region, regionID, parkType, dsrType, regionArea):
    # Calculate area
    if parkType in ([x[0] for x in POS_TYPE_C_CHOICES]):
        posExclude = Pos.objects.filter(mpoly__intersects=region.mpoly).filter(pos_type_c = parkType)
    elif parkType in ([x[0] for x in PARK_TYPE_CHOICES]):
        posExclude = Pos.objects.filter(mpoly__intersects=region.mpoly).filter(park_type = parkType)
    elif parkType == STAT_TYPE_CHOICE_TOTAL_POS:
        posExclude = Pos.objects.filter(mpoly__intersects=region.mpoly).filter(pos_type_c__in=[POS_TYPE_C_CHOICE_PARK, POS_TYPE_C_CHOICE_NATURAL, POS_TYPE_C_CHOICE_RESIDUAL_GREEN_SPACE])
    elif parkType == STAT_TYPE_CHOICE_TOTAL_POS_PLUS_SCHOOLS:
        posExclude = Pos.objects.filter(mpoly__intersects=region.mpoly).filter(pos_type_c__in=[POS_TYPE_C_CHOICE_PARK, POS_TYPE_C_CHOICE_NATURAL, POS_TYPE_C_CHOICE_RESIDUAL_GREEN_SPACE, POS_TYPE_C_CHOICE_SCHOOL_GROUNDS])
    else:
        posExclude = {}

    if len(posExclude) > 0:
        posArea = 0
        for pos in posExclude.area('mpoly'):
            posArea = posArea + pos.area.sq_km * 100
    else:
        posArea = 0

    # if the area is not 0 do the % calc
    if posArea == 0:
        areaStat = 0
    else:
        areaStat = round((posArea / regionArea) * 100, 2)

    regionStat = "percentsublga"

    # Save the record
    r = Area_Pop_Stats(region_pk_id = regionID, park_type = parkType, dsr_type = dsrType, region_stat = regionStat, region_value = str(areaStat))
    r.save()

def addCatchmentStat(regionPopulation, region, regionID, parkType, dsrType):
    # Get appropriate catchment polygon
    if parkType >= 1 and dsrType == 0:
        catchment = Catchment_Polygon.objects.get(park_type=parkType)
        # catchment = Catchment_Polygon.objects.filter(park_type = parkType)
        count = 1
    elif parkType == 0 and dsrType >= 1:
        catchment = Catchment_Polygon.objects.get(dsr_type = dsrType)
        # catchment = Catchment_Polygon.objects.filter(dsr_type = dsrType)
        count = 1
    else:
        count = 0

    if count == 1:
        # Clip the catchment boundary to the region before doing 100's of SA1 intersections to it
        clippedCatchment = catchment.mpoly.intersection(region.mpoly)
        sa1Areas = ABS_SA1.objects.filter(mpoly__intersects=region.mpoly).filter(mpoly__intersects=clippedCatchment)

        # catchmentUnion = catchment.unionagg()
        # sa1Polys = ABS_SA1.objects.filter(geom__intersects=region.mpoly).filter(geom__intersects=catchmentUnion)

        tot_p_p_Sum = 0
        age_0_4_2_Sum = 0
        age_5_14_2_Sum = 0
        age_15_192_Sum = 0
        age_20_242_Sum = 0
        age_25_342_Sum = 0
        age_35_442_Sum = 0
        age_45_542_Sum = 0
        age_55_642_Sum = 0
        age_65_742_Sum = 0
        age_75_842_Sum = 0
        age_85ov_p_Sum = 0

        insert_list = []

        for sa1 in sa1Areas:
            intersectArea = sa1.mpoly.intersection(clippedCatchment).area
            proportion = intersectArea / sa1.mpoly.area
            tot_p_p_Sum = tot_p_p_Sum + (proportion * sa1.tot_p_p)

            sum_start = datetime.now()
            age_0_4_2_Sum = age_0_4_2_Sum + (proportion * sa1.age_0_4__2)
            age_5_14_2_Sum = age_5_14_2_Sum + (proportion * sa1.age_5_14_2)
            age_15_192_Sum = age_15_192_Sum + (proportion * sa1.age_15_192)
            age_20_242_Sum = age_20_242_Sum + (proportion * sa1.age_20_242)
            age_25_342_Sum = age_25_342_Sum + (proportion * sa1.age_25_342)
            age_35_442_Sum = age_35_442_Sum + (proportion * sa1.age_35_442)
            age_45_542_Sum = age_45_542_Sum + (proportion * sa1.age_45_542)
            age_55_642_Sum = age_55_642_Sum + (proportion * sa1.age_55_642)
            age_65_742_Sum = age_65_742_Sum + (proportion * sa1.age_65_742)
            age_75_842_Sum = age_75_842_Sum + (proportion * sa1.age_75_842)
            age_85ov_p_Sum = age_85ov_p_Sum + (proportion * sa1.age_85ov_p)

        for currentStat in ABS_STATS:
            statField = currentStat[1]
            # lgaTotal =  getattr(lgaPolys, currentStat[1])
            if statField == ABS_STATS[1][1]:
                regionTotal =  getattr(regionPopulation, ABS_FIELD_STATS[1][1])
            else:
                regionTotal =  getattr(regionPopulation, statField)

            if parkType == 0 and dsrType >= 1:
                statName = currentStat[0] + 'dsr'
            else:
                statName = currentStat[0]

            if regionTotal == 0:
                catchmentStat = 0
            else:
                catchmentStat = round((float(locals()[statField + '_Sum']) / float(regionTotal)) * 100, 2)
            if catchmentStat > 100: # if calculation has a decimal slightly over 100
                catchmentStat = 100

            insert_list.append(Area_Pop_Stats(region_pk_id = regionID, park_type = parkType, dsr_type = dsrType, region_stat = statName, region_value = str(catchmentStat)))

        Area_Pop_Stats.objects.bulk_create(insert_list)


def calculateProportion(sa1_7digit, sa1_geom, clippedCatchment, parkType, dsrType):
    # cursor = connection.cursor()

    # # query = "select st_area(st_intersection(a.geom,b.mpoly)) / st_area(a.geom) from pos_abs_sa1 a, pos_catchment_polygon b where a.sa1_7digit = %s  and b.park_type = %s"
    # if parkType > 0 and dsrType == 0:
    #   # print get_date_time_now() + " - create query and params"
    #   #query = "select sum((st_area(st_intersection(a.geom,b.mpoly)) / st_area(a.geom))) from pos_abs_sa1 a join pos_catchment_polygon b on st_intersects(a.geom,b.mpoly) where a.sa1_7digit = %s  and b.park_type = %s"
    #   # query = "select sum((st_area(st_intersection(a.geom,b.mpoly)) / st_area(a.geom))) from pos_abs_sa1 a, pos_catchment_polygon b where a.sa1_7digit = %s  and b.park_type = %s"
    #   # params = [str(sa1_7digit), parkType]

    # elif parkType == 0 and dsrType > 0:
    #   #query = "select sum((st_area(st_intersection(a.geom,b.mpoly)) / st_area(a.geom))) from pos_abs_sa1 a join pos_catchment_polygon b on st_intersects(a.geom,b.mpoly) where a.sa1_7digit = %s  and b.dsr_type = %s"
    #   query = "select sum((st_area(st_intersection(a.geom,b.mpoly)) / st_area(a.geom))) from pos_abs_sa1 a, pos_catchment_polygon b where a.sa1_7digit = %s  and b.dsr_type = %s"
    #   params = [str(sa1_7digit), dsrType]
    # elif parkType == 1:
    #   #query = "select sum((st_area(st_intersection(a.geom,b.mpoly)) / st_area(a.geom))) from pos_abs_sa1 a join pos_catchment_polygon b on st_intersects(a.geom,b.mpoly) where a.sa1_7digit = %s  and b.park_type >= %s"
    #   query = "select sum((st_area(st_intersection(a.geom,b.mpoly)) / st_area(a.geom))) from pos_abs_sa1 a, pos_catchment_polygon b where a.sa1_7digit = %s  and b.park_type >= %s"
    #   params = [str(sa1_7digit), dsrType]
    # elif dsrType == 1:
    #   #query = "select sum((st_area(st_intersection(a.geom,b.mpoly)) / st_area(a.geom))) from pos_abs_sa1 a join pos_catchment_polygon b on st_intersects(a.geom,b.mpoly) where a.sa1_7digit = %s  and b.dsr_type >= %s"
    #   query = "select sum((st_area(st_intersection(a.geom,b.mpoly)) / st_area(a.geom))) from pos_abs_sa1 a, pos_catchment_polygon b where a.sa1_7digit = %s  and b.dsr_type >= %s"

    # print get_date_time_now() + " - execute query"
    start = datetime.now()
    intersectArea = sa1_geom.intersection(clippedCatchment).area
    proportion = intersectArea / sa1_geom.area
    # cursor.execute(query, params)
    # proportion = cursor.fetchone()[0]
    # print 'calc proportion query', datetime.now() - start
    # print query, params

    # db.close_connection()

    return proportion

def createCatchmentTable(regionID, parkType, dsrType):
    cursor = connection.cursor()

    # query = "select create_catchment_stat(%s,%s,%s)"
    # params = [regionID, parkType, dsrType]
    # cursor.execute(query, params)

    query = "select create_catchment_stat(%s,8,0)"
    params = [regionID]
    cursor.execute(query, params)

    # db.close_connection()

def calculateCatchment(statName, regionID):
    cursor = connection.cursor()

    query = "select printStats(%s,%s)"
    params = [str(statName), regionID]
    cursor.execute(query, params)
    calc = cursor.fetchone()[0]

    # db.close_connection()

    return calc

# Calculate all Facility Statistics for LGAs and Suburbs
def facilityStats():
    # Delete all records from the Facility_Statistics table if it's not a custom user region
    qs = Facility_Statistics.objects.exclude(region_pk__type=REGION_TYPE_CHOICE_USER) # Get all regions excluding the User regions
    qs = qs.exclude(region_pk__type__contains=REGION_TYPE_CHOICE_USER_LGA_SUBURB) # Exlude Special User Regions
    if qs.exists():
        qs.delete() # Delete occurs only if there is anything to delete

    # Loop through regions table
    counter = 0
    for currentRegion in Region.objects.all().order_by('type','name'):
        if (currentRegion.type == REGION_TYPE_CHOICE_SUBURB) or (currentRegion.type == REGION_TYPE_CHOICE_LGA):
            getFacilityStats(currentRegion)

# Calculate the Facility Statistics for a given Region
def getFacilityStats(region):

    # Get all the park types to eventually cycle through
    park_types = [
        POS_TYPE_C_CHOICE_PARK,
        PARK_TYPE_CHOICE_POCKET,
        PARK_TYPE_CHOICE_SMALL,
        PARK_TYPE_CHOICE_MEDIUM,
        PARK_TYPE_CHOICE_LARGE_1,
        PARK_TYPE_CHOICE_LARGE_2,
        PARK_TYPE_CHOICE_DISTRICT_1,
        PARK_TYPE_CHOICE_DISTRICT_2,
        PARK_TYPE_CHOICE_REGIONAL
    ]

    # Create a mapping to store each Park's stats
    stats_map = {
        POS_FACILITY_CHOICE_SOCCER: 0,
        POS_FACILITY_CHOICE_NETCOURT: 0,
        POS_FACILITY_CHOICE_BASEBALL: 0,
        POS_FACILITY_CHOICE_BASKETHOOP: 0,
        POS_FACILITY_CHOICE_ATHLETICS: 0,
        POS_FACILITY_CHOICE_SKATEBMX: 0,
        POS_FACILITY_CHOICE_LAKEPOND: 0,
        POS_FACILITY_CHOICE_FORESHORE: 0,
        POS_FACILITY_CHOICE_STREAM: 0,
        POS_FACILITY_CHOICE_GARDENS: 0,
        POS_FACILITY_CHOICE_PATHS: 0,
        POS_FACILITY_STAT_CHOICE_PLAYFENCE_NO_0: 0,
        POS_FACILITY_STAT_CHOICE_DOGS_NO_0: 0,
        POS_FACILITY_CHOICE_SEAT: 0,
        POS_FACILITY_CHOICE_KIOSK: 0,
        POS_FACILITY_CHOICE_ART: 0,
        POS_FACILITY_CHOICE_LIGHTING: 0,
        POS_FACILITY_CHOICE_LIGHTFEAT: 0,
        POS_FACILITY_CHOICE_CARPARK: 0,
        POS_FACILITY_CHOICE_TOILETS: 0,
        POS_FACILITY_CHOICE_PICNIC: 0,
        POS_FACILITY_CHOICE_BBQ: 0,
        POS_FACILITY_CHOICE_GRASSRETIC: 0,
        POS_FACILITY_STAT_CHOICE_PATHSHADE_NO_0: 0,
        POS_FACILITY_STAT_CHOICE_PATHSHADE_YES_POOR_1: 0,
        POS_FACILITY_STAT_CHOICE_PATHSHADE_YES_MEDIUM_2: 0,
        POS_FACILITY_STAT_CHOICE_PATHSHADE_YES_GOOD_3: 0,
        POS_FACILITY_CHOICE_WILDLIFE: 0,
        POS_FACILITY_CHOICE_WETLAND: 0,
        POS_FACILITY_CHOICE_FOUNTAIN: 0,
        POS_FACILITY_CHOICE_PLAYGROUND: 0,
        POS_FACILITY_CHOICE_RUGBY: 0,
        POS_FACILITY_CHOICE_HOCKEY: 0,
        POS_FACILITY_CHOICE_FITNESS: 0,
        POS_FACILITY_CHOICE_CRICKET: 0,
        POS_FACILITY_CHOICE_FOOTBALL: 0,
        POS_FACILITY_CHOICE_TENNIS: 0,
        POS_FACILITY_STAT_CHOICE_PLAYFENCE_YES_1: 0,
        POS_FACILITY_STAT_CHOICE_DOGS_YES_1: 0,
        POS_FACILITY_STAT_CHOICE_PLAYSHADE_PARTIAL_1: 0,
        POS_FACILITY_STAT_CHOICE_PLAYSHADE_FULL_2: 0,
        POS_FACILITY_STAT_CHOICE_TREES_YES_1_50_1: 0,
        POS_FACILITY_STAT_CHOICE_DOGS_NO_INFO_2: 0,
        POS_FACILITY_STAT_CHOICE_TREES_NO_0: 0,
        POS_FACILITY_STAT_CHOICE_TREES_YES_50_100_2: 0,
        POS_FACILITY_STAT_CHOICE_TREES_YES_MORE_100_3: 0,
        POS_FACILITY_STAT_CHOICE_ADJ_PSF: 0
    }

    # Get all the Parks in and intersecting the region
    all_parks = Pos.objects.filter(pos_type_c=POS_TYPE_C_CHOICE_PARK).filter(
        mpoly__intersects=region.mpoly)

    for one_park_type in park_types:
        # Filter all_parks by the park_type to get just the stats for this park_type
        if one_park_type == POS_TYPE_C_CHOICE_PARK:
            park_x = all_parks.filter(pos_type_c=one_park_type)
        else:
            park_x = all_parks.filter(park_type=one_park_type)

        # Create a new, empty mapping for each park_type
        stats_map_1 = copy(stats_map)

        if park_x.exists():

            for park in park_x:
                # Get Adjacent Paid Sporting Facilities
                adj_psf_value = park.adj_psf
                stats_map_1[POS_FACILITY_STAT_CHOICE_ADJ_PSF] = stats_map_1[POS_FACILITY_STAT_CHOICE_ADJ_PSF] + adj_psf_value

                # Count all the facilities in park type=x, in the Region
                # 1st get all the Facilities in this Park
                facilities = Facility.objects.filter(pos_pk=park.pk)
                # Add the count info
                if facilities.exists:
                    for facility_row in facilities:
                        facility_type = facility_row.facility_type.upper()
                        facility_value = facility_row.code
                        if facility_value is None:
                            facility_value = 0

                        # Filter some of the facility_type by their code into
                        # the relevant facility_stat types
                        # If Dogs, check for 0, 1, 2
                        if facility_type == POS_FACILITY_CHOICE_DOGS:
                            if facility_value == 1:
                                facility_type = POS_FACILITY_STAT_CHOICE_DOGS_YES_1
                                facility_value = 1
                            elif facility_value == 2:
                                facility_type = POS_FACILITY_STAT_CHOICE_DOGS_NO_INFO_2
                                facility_value = 1
                            else:
                                facility_type = POS_FACILITY_STAT_CHOICE_DOGS_NO_0
                                facility_value = 1
                        # If Trees, check for 0, 1, 2, 3
                        elif facility_type == POS_FACILITY_CHOICE_TREES:
                            if facility_value == 1:
                                facility_type = POS_FACILITY_STAT_CHOICE_TREES_YES_1_50_1
                                facility_value = 1
                            elif facility_value == 2:
                                facility_type = POS_FACILITY_STAT_CHOICE_TREES_YES_50_100_2
                                facility_value = 1
                            elif facility_value == 3:
                                facility_type = POS_FACILITY_STAT_CHOICE_TREES_YES_MORE_100_3
                                facility_value = 1
                            else:
                                facility_type = POS_FACILITY_STAT_CHOICE_TREES_NO_0
                                facility_value = 1
                        # If Pathshade, check for 0, 1, 2, 3
                        elif facility_type == POS_FACILITY_CHOICE_PATHSHADE:
                            if facility_value == 1:
                                facility_type = POS_FACILITY_STAT_CHOICE_PATHSHADE_YES_POOR_1
                                facility_value = 1
                            elif facility_value == 2:
                                facility_type = POS_FACILITY_STAT_CHOICE_PATHSHADE_YES_MEDIUM_2
                                facility_value = 1
                            elif facility_value == 3:
                                facility_type = POS_FACILITY_STAT_CHOICE_PATHSHADE_YES_GOOD_3
                                facility_value = 1
                            else:
                                facility_type = POS_FACILITY_STAT_CHOICE_PATHSHADE_NO_0
                                facility_value = 1
                        # If Playshade, check for 1, 2
                        elif facility_type == POS_FACILITY_CHOICE_PLAYSHADE:
                            if facility_value == 1:
                                facility_type = POS_FACILITY_STAT_CHOICE_PLAYSHADE_PARTIAL_1
                                facility_value = 1
                            elif facility_value == 2:
                                facility_type = POS_FACILITY_STAT_CHOICE_PLAYSHADE_FULL_2
                                facility_value = 1
                            else:
                                # Put something in that won't match so no stat will be calculated later
                                facility_type = POS_FACILITY_CHOICE_PLAYSHADE
                                facility_value = 0
                        # If Playfence, check for 0, 1
                        elif facility_type == POS_FACILITY_CHOICE_PLAYFENCE:
                            # Weird one, 1st check if there are any playgrounds in the park
                            playground = facilities.get(facility_type__iexact=POS_FACILITY_CHOICE_PLAYGROUND)
                            if playground.code == 0:
                                # Put something in that won't match so no stat will be calculated later
                                facility_type = POS_FACILITY_CHOICE_PLAYSHADE
                                facility_value = 0
                            elif facility_value == 0:
                                facility_type = POS_FACILITY_STAT_CHOICE_PLAYFENCE_NO_0
                                facility_value = 1
                            elif facility_value == 1:
                                facility_type = POS_FACILITY_STAT_CHOICE_PLAYFENCE_YES_1
                                facility_value = 1

                        # Make any erroneous facility codes into 0
                        if facility_value not in [0, 1]:
                            facility_value = 0

                        # Now check facility_type if applicable
                        if facility_type in stats_map_1:
                            # Get the current value and add to it
                            stats_map_1[facility_type] = stats_map_1[facility_type] + facility_value
        # Now that the stats for the park type are done, add to the table
        # If no stats are found for the park type, it will store the...
        # ...default 0 values which are still required for the downloadable file
        for stat in stats_map_1:
            # Check to overwrite an existing facility stat
            # Used for user regions instead of deleting and creating new objects
            check_facility_stats = Facility_Statistics.objects.filter(
                region_pk=region).filter(
                park_type=one_park_type).filter(
                facility_stat=stat.lower())
            if check_facility_stats.exists():
                facility_stat = check_facility_stats[0]
            else:
                facility_stat = Facility_Statistics()
            facility_stat.region_pk = region
            facility_stat.park_type = one_park_type
            facility_stat.facility_stat = stat.lower()
            facility_stat.facility_count = stats_map_1[stat]
            facility_stat.save()
