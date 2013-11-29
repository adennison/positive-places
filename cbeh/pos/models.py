# GR268 & GR342
# Django Models for POS database tables
# Classes defined:
#     Region, Pos, Facility, Facility_Statistics, Area_Pop_Stats,
#     Park_Type_Distance, DSR_Type_Distance, Catchment_Polygon, UserProfile,
#     User_Statistic, Project, ABS_SA1, ABS_Region_Population

try:
    import json
except ImportError:
    import simplejson as json

from constants import * # Import Constants file, in same directory - many!
from django.contrib.gis.db import models
from django.contrib.gis.geos import *
from django.contrib.gis.gdal import OGRGeometry
from django.contrib.gis.measure import Distance
from django.contrib.auth.models import User
#from registration.signals import user_registered
import math

# Define the Region class's fields (Suburb / LGA / Metro Area / City)
class Region(models.Model):
    sub_lga_id = models.CharField(max_length=15, blank=False, null=False,
        help_text="The shapefile ID from UWA for this region's feature.")
    name = models.CharField(max_length=180,
        blank=False, db_index=True,
        help_text='The Proper name of the region.')
    short_name = models.CharField(max_length=180,
        blank=True, db_index=True,
        help_text='The short form name of the region, such as "Stirling" for City of Stirling.')
    type = models.CharField(max_length=180, choices=REGION_TYPE_CHOICES,
        blank=False, db_index=True,
        help_text='The type of the region, such as Suburb, City, etc.')
    mpoly = models.MultiPolygonField(srid=28350, null=True,
        spatial_index=True, geography=False,
        help_text='The polygon representing the shape of the region.')
    objects = models.GeoManager()

    # Check if the region has a stored polygon
    def check_polygon(self):
        if self.mpoly is None:
            return False
        else:
            return True

    # Get the stats for the 3 tabbed tables in the region view
    def get_park_stats(self):
        # Create empty dictionary
        parkStats = {}

        # Get the area pop stats for the selected region
        qs = Area_Pop_Stats.objects.filter(region_pk_id=self.pk)

        # Check that there were records returned
        if len(qs) > 0:
            # # Get the park type distances
            # for choiceType in PARK_TYPE_CHOICES:
            #     regionParkType = choiceType[0]
            #     qp = Park_Type_Distance.objects.get(park_type=regionParkType)
            #     parkTypeDistance = qp.type_distance
            #     parkStats['typedistance_' + str(regionParkType)] = int(parkTypeDistance)

            # # # Get DSR type distances
            # for choiceType in DSR_TYPE_CHOICES:
            #     regionDsrType = choiceType[0]
            #     qd = DSR_Type_Distance.objects.get(dsr_type=regionDsrType)
            #     dsrTypeDistance = qd.type_distance
            #     parkStats['dsrdistance_' + str(regionDsrType)] = int(dsrTypeDistance)

            for stat in qs:
                regionStat = stat.region_stat
                regionParkType = stat.park_type
                regionDsrType = stat.dsr_type

                # Get the park type distances
                if regionParkType >= PARK_TYPE_CHOICE_POCKET and regionParkType <= PARK_TYPE_CHOICE_REGIONAL:
                    qp = Park_Type_Distance.objects.get(park_type=regionParkType)
                    parkTypeDistance = qp.type_distance
                    parkStats['typedistance_' + str(regionParkType)] = int(parkTypeDistance)

                # Get DSR type distances
                if regionDsrType >= DSR_TYPE_CHOICE_POCKET and regionDsrType <= DSR_TYPE_CHOICE_REGIONAL:
                    qd = DSR_Type_Distance.objects.get(dsr_type=regionDsrType)
                    dsrTypeDistance = qd.type_distance
                    parkStats['dsrdistance_' + str(regionDsrType)] = int(dsrTypeDistance)

                regionValue = stat.region_value
                if regionParkType > 0 and regionDsrType == 0: # Get park stats
                    if not 'percentpop' in regionStat and not regionStat.endswith('dsr'): # only get stats required for tables to display
                        keyName = regionStat + '_' + str(regionParkType) # uniquely ID each stat for display
                        if regionStat == AREA_POP_FREQUENCY:
                            parkStats[keyName] = int(regionValue)
                        else:
                            parkStats[keyName] = round(regionValue, 2)
                        # print keyName, regionParkType,regionDsrType

                elif regionDsrType > 0 and regionParkType == 0: # Get DSR stats
                    if not 'percentpop' in regionStat and regionStat.endswith('dsr'): # only get stats required for tables to display
                        keyName = regionStat + '_' + str(regionDsrType) # uniquely ID each stat for display
                        if regionStat == AREA_POP_FREQUENCY:
                            parkStats[keyName] = int(regionValue)
                        else:
                            parkStats[keyName] = round(regionValue, 2)
        return parkStats

    # Put in a code as integer, return True/False if it is a Park Code
    def check_park_code(self, code):
        for tuple in PARK_TYPE_CHOICES:
            if tuple[0] == code:
                return True
        return False # If it gets this far then no match

    # Put in Park Type code as integer, returns Park Type Description
    def get_park_type_desc(self, code):
        for tuple in PARK_TYPE_CHOICES:
            if tuple[0] == code:
                return tuple[1]

    # Put in POS Choice Code as integer, returns POS Choice Description
    def get_pos_type_desc(self, code):
        for tuple in POS_TYPE_C_CHOICES:
            if tuple[0] == code:
                return tuple[1]

    # Transform a region to WGS84 coordinates
    def get_mpoly_wgs(self):
        try:
            return self.mpoly.transform(4326, clone=True)
        except:
            return 'false'

    # Get a Region's WKT in WGS84
    def get_wgs84_wkt(self):
        mpoly_wgs84 = self.get_mpoly_wgs()
        if mpoly_wgs84 != 'false':
            return mpoly_wgs84[0].wkt
        return mpoly_wgs84

    # Get the area of a region object, in Hectares
    def get_area_ha(self):
        area_sqm = self.mpoly.area
        area_ha = area_sqm * 0.0001
        return area_ha

    # Get the area of a region object, in Hectares and rounded to the nearest Integer
    def get_area_ha_integer(self):
        return int(self.get_area_ha())

    # for a region object of type ***, find the outer type that it intersects
    # e.g. Suburb in LGA,  LGA in Metro Area, etc.
    # Returns a list of intersecting outer region names
    def get_parent_regions(self):
        qs = Region.objects.filter(mpoly__intersects=self.mpoly) # queryset
        regionType = self.type
        if regionType == REGION_TYPE_CHOICE_CD: # Census District
            qs = qs.filter(type=REGION_TYPE_CHOICE_SUBURB).order_by('short_name')
        elif regionType == REGION_TYPE_CHOICE_SUBURB: # Suburb
            qs = qs.filter(type=REGION_TYPE_CHOICE_LGA).order_by('short_name')
        elif regionType == REGION_TYPE_CHOICE_LGA: # LGA
        #    qs = qs.filter(type=REGION_TYPE_CHOICE_METRO).order_by('short_name')
            qs = qs.filter(type=REGION_TYPE_CHOICE_CITY).order_by('short_name')
        elif regionType == REGION_TYPE_CHOICE_METRO: # Metro Area
            qs = qs.filter(type=REGION_TYPE_CHOICE_CITY).order_by('short_name')
        elif regionType == REGION_TYPE_CHOICE_CITY: # City
            #qs = qs.filter(type=REGION_TYPE_CHOICE_STATE).order_by('short_name')
            qs = ["Western Australia"]
        elif regionType == REGION_TYPE_CHOICE_STATE: # State
            #qs = qs.filter(type=REGION_TYPE_CHOICE_COUNTRY).order_by('short_name')
            qs = ["Australia"]
        elif regionType == REGION_TYPE_CHOICE_COUNTRY: # Country
            qs = ["Australia"]
        return qs

    # if this region is a User region, CD or a Suburb, get the LGA
    def get_lga(self):
        qs = Region.objects.filter(mpoly__intersects=self.mpoly) # queryset
        regionType = self.type
        if (regionType == REGION_TYPE_CHOICE_USER) or \
            (regionType == REGION_TYPE_CHOICE_CD) or \
            (regionType == REGION_TYPE_CHOICE_SUBURB): # User Region or CD or Suburb
            qs = qs.filter(type=REGION_TYPE_CHOICE_LGA).order_by('short_name')
        else:
            qs = ["-"]
        return qs

    # if this region is a Suburb or LGA, get the Metro Region
    def get_metro_region(self):
        qs = Region.objects.filter(mpoly__intersects=self.mpoly) # queryset
        regionType = self.type
        if (regionType == REGION_TYPE_CHOICE_SUBURB) or (regionType == REGION_TYPE_CHOICE_LGA): # Suburb or LGA
            qs = qs.filter(type=REGION_TYPE_CHOICE_METRO).order_by('short_name')
        else:
            qs = ["-"]
        return qs

    # get the City that this region is in
    def get_city(self):
        qs = Region.objects.filter(mpoly__intersects=self.mpoly) # queryset
        regionType = self.type
        qs = qs.filter(type=REGION_TYPE_CHOICE_CITY).order_by('short_name')
        return qs

    # get the region description label
    def get_region_type_description(self):
        for tuple in REGION_TYPE_CHOICES:
            if self.type == tuple[0]:
                return tuple[1]
        return 'Region' # If it gets to here there is a problem

    # Get the parent region's type
    def get_parent_region_label(self):
        index = -1
        for tuple in REGION_TYPE_CHOICES:
            index = index + 1
            if self.type == tuple[0]:
                #print REGION_TYPE_CHOICES[index+1][1]
                return REGION_TYPE_CHOICES[index+1][1]

    @models.permalink
    def get_absolute_url(self):
        return ('pos.views.region.details', [self.id])

    def __unicode__(self):
        return self.name
    # Metadata for the Region Class
    class Meta:
        ordering = ['name']
        verbose_name = 'Region'
        verbose_name_plural = 'Regions'

# Define the POS class's fields
class Pos(models.Model):
    source_id = models.IntegerField(blank=False, null=False,
        help_text="The ID from UWA for this POS.")
    part_id = models.IntegerField(blank=False, null=False,
        help_text="The part ID for this POS part.")
    uid = models.CharField(max_length=20,
        blank=False, null=False, db_index=True,
        help_text="The UID for this POS part. Combines the POS ID and Part ID uniquely.")
    pos_type_c = models.IntegerField(choices=POS_TYPE_C_CHOICES,
        blank=False, null=False,
        help_text='The type classification of the public open space.')
    park_name = models.CharField(max_length=180, blank=True, db_index=True,
        help_text='The name of the Park if known. Only for parks.')
    park_type = models.IntegerField(choices=PARK_TYPE_CHOICES, blank=True,
        help_text='The type of park. Only for parks.')
    dsr_type = models.IntegerField(choices=DSR_TYPE_CHOICES, blank=True,
        help_text='The DSR type of park. Only for parks.')
    pos_dat = models.IntegerField(choices=SURVEY_TYPE_CHOICES, blank=True,
        help_text='The survey type conducted on a park. Only for parks.')
    adj_psf = models.IntegerField(choices=PSF_CHOICES, blank=True,
        help_text='Adjacency of a park to a Paid Sporting Facility. Only for parks.')
    adj_bf = models.IntegerField(choices=BF_CHOICES, blank=True,
        help_text='Adjacency or containment of a park to a Bush Forever area. Only for parks.')
    qual_child = models.IntegerField(blank=True,
        help_text="The quality score for the park, for children. Only for parks.")
    qual_adole = models.IntegerField(blank=True,
        help_text="The quality score for the park, for adolescents. Only for parks.")
    qual_adult = models.IntegerField(blank=True,
        help_text="The quality score for the park, for adults. Only for parks.")
    mpoly = models.MultiPolygonField(srid=28350, spatial_index=True, geography=False,
        help_text='The polygon representing the shape of the public open space.')
    objects = models.GeoManager()

    # Get the nearest x POSs to the input point location within radius)
    def get_nearest_x_parks(self, long, lat, xNearestParks, xNearestPos, radius):
        # firstly, convert lat/long coords to MGA Easting, Northing values
        pointGeosObj = Point(long, lat, srid=4326)
        mgaSrid = self.get_mga_srid_from_long(long) # find out the MGA zone
        pointMGA = pointGeosObj.transform(mgaSrid, clone=True)
#        qs = Pos.objects.filter(mpoly__distance_lte=(pointMGA, 50000)).distance(pointMGA).order_by('distance')[:25] # get everything within 50km
        pointMGABuffer = pointMGA.buffer(radius) # search area limited
        qs = Pos.objects.filter(mpoly__within=(pointMGABuffer)).distance(pointMGA).order_by('distance')
        #qs = qs.filter(pos_type_c=POS_TYPE_C_CHOICE_PARK) # refine to only parks
        if qs.exists() == False: # if no POSs returned in the queryset
            return False
        else:
            nearPosList = []
            posCounter = 0
            parkCounter = 0
            for onePos in qs:
                if onePos.pos_type_c == POS_TYPE_C_CHOICE_PARK:
                    parkCounter = parkCounter + 1
                posCounter = posCounter + 1
                nearPosList.append(onePos)
                if parkCounter >= xNearestParks and posCounter >= xNearestPos:
                    # Sort the lists by putting the first 'xNearestParks' at the front
                    counter = 0
                    parkCounter = 0
                    for aPos in nearPosList:
                        if aPos.pos_type_c == POS_TYPE_C_CHOICE_PARK:
                            if (counter > 0) and (parkCounter < xNearestParks):
                                nearPosList.insert(parkCounter, nearPosList.pop(counter))
                            parkCounter = parkCounter + 1
                        counter = counter + 1
                    #displayCounter = 0
                    #for aPos in nearPosList:
                    #    displayCounter = displayCounter + 1
                    #    print str(displayCounter) + " " + str(aPos.name) + ', ' + str(aPos.distance) + ', ' + aPos.get_pos_type_desc()
                    return nearPosList

    # Get the MGA zone as SRID based on an input longitude parameter
    def get_mga_srid_from_long(self, longitude):
        if longitude < 114:
            mgaZone = 28349 # zone 49
        elif longitude >= 114 and longitude <= 120:
            mgaZone = 28350 # zone 50
        elif longitude >= 120 and longitude <= 126:
            mgaZone = 28351 # zone 51
        elif longitude >= 126 and longitude <= 132:
            mgaZone = 28352 # zone 52
        elif longitude >= 132 and longitude <= 138:
            mgaZone = 28353 # zone 53
        elif longitude >= 138 and longitude <= 144:
            mgaZone = 28354 # zone 54
        elif longitude >= 144 and longitude <= 150:
            mgaZone = 28355 # zone 55
        elif longitude >= 150:
            mgaZone = 28356 # zone 56
        return mgaZone

    # Get the area of this POS in hectares (input sq m)
    def get_area_ha(self):
        area_sqm = self.mpoly.area
        area_ha = area_sqm * 0.0001
        return round(area_ha, 2)

    # Get the total area of all this POS's parts, in hectares
    def get_area_all_parts_ha(self):
        parts = self.get_parts()
        totalArea = self.get_area_ha()
        for part in parts:
            totalArea = totalArea + part.get_area_ha()
        return round(totalArea, 2)

    # Transform a POS to WGS84 coordinates
    def get_mpoly_wgs(self):
        return self.mpoly.transform(4326, clone=True)

    # Get the other parts that share this POS's 'source_id', return queryset
    def get_parts(self):
        return Pos.objects.filter(source_id=self.source_id).exclude(pk=self.pk)

    # Get all the parts including this one that share this POS's 'source_id', return queryset
    def get_all_parts(self):
        return Pos.objects.filter(source_id=self.source_id)

    # Get the other parts of this POS in WGS84
    def get_part_mpoly_wgs(self):
        other = self.mpoly.clone()
        for part in self.get_parts():
            other.extend(part.mpoly)
        return other.transform(4326, clone=True)

    # Get a list of all this POS's parts, with pos_type_c description
    # Returns a JSON list for passing on to Javascript for map rendering
    def get_pos_list_json(self):
        partsList = [{
                        'pos_pk' : self.pk, \
                        'name' : self.park_name, \
                        'pos_type_c' : self.get_pos_type_desc(), \
                        'pos_wkt' : self.get_mpoly_wgs().wkt
        }]
        otherParts = self.get_parts()
        for part in otherParts:
            partsList.append( {
                                'pos_pk' : part.pk, \
                                'name' : part.park_name, \
                                'pos_type_c' : part.get_pos_type_desc(), \
                                'pos_wkt' : part.get_mpoly_wgs().wkt
                            } )
        return json.dumps(partsList)

    # Get all the Facilities info that this POS has
    def get_facility_info(self):
        # Initially set the expandable categories' presence to 'No'
        facilityDict = {
                        CATEGORY_DISPLAY_SPORTING : POS_GENERAL_MAPPING[0],
#                        CATEGORY_DISPLAY_PLAYGROUND : POS_GENERAL_MAPPING[0],
                        CATEGORY_DISPLAY_WATER : POS_GENERAL_MAPPING[0],
                        CATEGORY_DISPLAY_LIGHTS : POS_GENERAL_MAPPING[0],
#                        CATEGORY_DISPLAY_PATHS : POS_GENERAL_MAPPING[0]
                        }
        # Get the facility records for this park from the database
        qs = Facility.objects.filter(pos_pk_id=self.pk)

        # Format all the facility info for the park into the dictionary
        for facility in qs:
            facilityType = facility.facility_type
            facilityCode = facility.code
            # Check code is acceptable, if not set to 0
            # Set the facility presence text
            if facilityType == POS_FACILITY_CHOICE_TREES.lower():
                if not ((facilityCode >= 0) and (facility.code <= 3)):
                    facilityCode = 0
                facilityPresence = POS_TREES_MAPPING[facilityCode]
            # elif facilityType == POS_FACILITY_CHOICE_PATHSHADE.lower():
            #     if not ((facilityCode >= 0) and (facility.code <= 3)):
            #         facilityCode = 0
            #     facilityPresence = POS_PATHSHADE_MAPPING[facilityCode]
            elif facilityType == POS_FACILITY_CHOICE_PLAYSHADE.lower():
                if not ((facilityCode >= 0) and (facility.code <= 2)):
                    facilityCode = 0
                facilityPresence = POS_PLAYSHADE_MAPPING[facilityCode]
            elif facilityType == POS_FACILITY_CHOICE_DOGS.lower():
                if not ((facilityCode >= 0) and (facility.code <= 2)):
                    facilityCode = 0
                facilityPresence = POS_DOGS_MAPPING[facilityCode]
            else:
                if facilityCode == 0:
                    facilityPresence = POS_GENERAL_MAPPING[0] # 'No'
                elif facilityCode == 1:
                    if facilityType == POS_FACILITY_CHOICE_LIGHTFEAT.lower():
                        facilityPresence = POS_LIGHTFEATURES_MAPPING[1] # 'Around Courts, ...etc'
                    else:
                        facilityPresence = POS_GENERAL_MAPPING[1] # 'Yes'
                else: # i.e. an erroneous code
                    facilityCode = 0
                    facilityPresence = POS_GENERAL_MAPPING[0] # 'No'
            # Check categories to display
            for categDict in CATEGORY_DISPLAY_FACILITY_MAPPING:
                categoryName = categDict.keys()[0] # only 1 key in the dictionary
                categoryList = [listItem.lower() for listItem in categDict[categoryName]] # Make all strings lowercase before checking
                if ( (facilityCode != 0) and (facilityType in categoryList) and (facilityDict[categoryName] == POS_GENERAL_MAPPING[0])):
                    facilityDict[categoryName] = POS_GENERAL_MAPPING[1]
                    break # Only care if there is at least 1 match
            # Add to dictionary
            facilityDict[facilityType] = facilityPresence
        # Lastly add paid sporting facility presence (from POS table, not Facility table)
        adjPSF = POS_GENERAL_MAPPING[self.adj_psf]
        if not ((adjPSF == 0) or (adjPSF == 1)):
            adjPSF = POS_GENERAL_MAPPING[0]
        facilityDict['adj_psf'] = adjPSF

        return facilityDict

    # Get the POS Facility Choice description, given the short info. (i.e. 'TREEPERIMA' --> 'Trees - Perimeter all sides')
    def get_pos_description(self, inDescription):
        for tuple in POS_FACILITY_CHOICES:
            facilityChoice = tuple[0].lower()
            if facilityChoice == inDescription:
                return tuple[1]
        return inDescription + ' (unknown key)'

    # Put in POS Type Choice code as integer, returns POS Type Choice Description
    def get_pos_type_desc(self):
        for tuple in POS_TYPE_C_CHOICES:
            if tuple[0] == self.pos_type_c:
                return tuple[1]

    # Put in Park Type code as integer, returns Park Type Description
    def get_park_type_desc(self):
        for tuple in PARK_TYPE_CHOICES:
            if tuple[0] == self.park_type:
                return tuple[1]

    # get the Suburb(s) that this POS is in
    def get_suburb(self):
        qs = Region.objects.filter(mpoly__intersects=self.mpoly) # query set
        qs = qs.filter(type=REGION_TYPE_CHOICE_SUBURB).order_by('short_name')
        return qs

    # get the LGA(s) that this POS is in
    def get_lga(self):
        qs = Region.objects.filter(mpoly__intersects=self.mpoly) # query set
        qs = qs.filter(type=REGION_TYPE_CHOICE_LGA).order_by('short_name')
        return qs

    # get the Metro Region(s) that this POS is in
    def get_metro_region(self):
        qs = Region.objects.filter(mpoly__intersects=self.mpoly) # query set
        qs = qs.filter(type=REGION_TYPE_CHOICE_METRO).order_by('short_name')
        return qs

    # get the City that this POS is in
    def get_city(self):
        qs = Region.objects.filter(mpoly__intersects=self.mpoly) # query set
        qs = qs.filter(type=REGION_TYPE_CHOICE_CITY).order_by('short_name')
        return qs

    @models.permalink
    def get_absolute_url(self):
        return ('pos.views.pos_view.details', [self.pk])

    def __unicode__(self):
        return u'%d (%d)' % (self.source_id, self.part_id)

    class Meta:
        ordering = ['park_name', 'uid']
        verbose_name = 'Public Open Space'
        verbose_name_plural = 'Public Open Spaces'

# Define the Facility class's fields
class Facility(models.Model):
    pos_pk = models.ForeignKey(Pos, null=False, db_index=True,
        help_text='Foreign Key based on the UID of a POS part for this facility.')
    facility_type = models.CharField(max_length=30, choices=POS_FACILITY_CHOICES,
        blank=False, null=False, db_index=True,
        help_text='The type of the facility.')
    code = models.IntegerField(blank=False, null=True,
        help_text='The corresponding code for this facility.')
    other = models.CharField(max_length=180,
        blank=True, null=True,
        help_text='Any miscellaneous facility not in the set facility types list.')

    # get the category that this facility fits into
    def get_category(self):
        for categDict in CATEGORY_FACILITY_MAPPING: # imported from constants.py in same directory
            categoryName = categDict.keys()[0]
            categoryList = [listItem.lower() for listItem in categDict[categoryName]] # Make all strings lowercase before checking
            if (self.facility_type in categoryList) and (self.code is not None):
                if self.code != 0: # all 0 codes are no presence or N/A
                    if not ((self.facility_type == POS_FACILITY_CHOICE_DOGS.lower()) and (self.code == 2)): #  Note: Dogs also has code '2' as no info
                        #print str(self.pk) + ', categoryName: ' + categoryName + ', self.facility_type: ' + self.facility_type + ', self.code: ' + str(self.code)
                        return categoryName
        return '' # if it gets to here then there is no matching category

    def __unicode__(self):
        return self.facility_type()

    class Meta:
        ordering = ['pos_pk', 'facility_type']
        verbose_name = 'Public Open Space Facility'
        verbose_name_plural = 'Public Open Space Facilities'

# Define the Facility Statistics table
class Facility_Statistics(models.Model):
    region_pk = models.ForeignKey(Region, null=False, db_index=True,
        help_text='Foreign Key based on the "sub_lga_id" of a Region.')
    park_type = models.IntegerField(blank=False, null=False,
        help_text='An integer code representing a park type, e.g. 6 = Pocket Park.')
    facility_stat = models.CharField(max_length=30,
        blank=False, null=False, db_index=True,
        help_text='The facility statistic.')
    facility_count = models.IntegerField(blank=False, null=False,
        help_text='An integer count of the facility_stat with this park_type, for this region_pk.')

    def __unicode__(self):
        return self.park_type()

    class Meta:
        ordering = ['region_pk', 'park_type', 'facility_stat']
        verbose_name = 'Public Open Space Facility Statistic'
        verbose_name_plural = 'Public Open Space Facility Statistics'

# Define the distance for each park type
class Area_Pop_Stats(models.Model):
    region_pk = models.ForeignKey(Region, null=False, db_index=True,
        help_text='Foreign Key based on the "sub_lga_id" of a Region.')
    park_type = models.IntegerField(blank=False, null=False,
        help_text='An integer code representing a park type, e.g. 6 = Pocket Park.')
    dsr_type = models.IntegerField(blank=False, null=False, choices=DSR_TYPE_CHOICES,
        help_text='An integer code representing a DSR park type')
    region_stat = models.CharField(max_length=30,
        blank=False, null=False, db_index=True,
        help_text='The region statistic.')
    region_value = models.DecimalField(blank=False, null=False,
        max_digits=18, decimal_places=3,
        help_text='The number value to represent for the region statistic.')

    def __unicode__(self):
        #return self.park_type.name
        return '%s %d %s' % (self.region_pk.name,self.park_type,self.region_stat)

    class Meta:
        ordering = ['region_pk', 'park_type']
        verbose_name = 'Area and Population Statistic'
        verbose_name_plural = 'Area and Population Statistics'

# Define the catchment distance for each park type
class Park_Type_Distance(models.Model):
    park_type = models.IntegerField(blank=False, null=False, choices=PARK_TYPE_CHOICES,
        help_text='An integer code representing a park type, e.g. 6 = Pocket Park.')
    type_distance = models.IntegerField(blank=False, null=False,
        help_text='The distance used to calculate the catchment population for the associated park type')

    def __unicode__(self):
        return self.get_park_type_display()

    class Meta:
        ordering = ['park_type','type_distance']
        verbose_name = 'Park Type Catchment Distance'
        verbose_name_plural = 'Park Type Catchment Distances'

# Define the catchment distance for each DSR park type
class DSR_Type_Distance(models.Model):
    dsr_type = models.IntegerField(blank=False, null=False, choices=DSR_TYPE_CHOICES,
        help_text='An integer code representing a DSR park type')
    type_distance = models.IntegerField(blank=False, null=False,
        help_text='The distance used to calculate the catchment population for the associated DSR park type')

    def __unicode__(self):
        return self.dsr_type

    class Meta:
        ordering = ['dsr_type','type_distance']
        verbose_name = 'DSR Type Catchment Distance'
        verbose_name_plural = 'DSR Type Catchment Distances'

# Define the catchment polygon for each DSR and Park type
class Catchment_Polygon(models.Model):
    park_type = models.IntegerField(choices=PARK_TYPE_CHOICES, blank=True,
        help_text='An integer code representing a park type, e.g. 6 = Pocket Park.')
    dsr_type = models.IntegerField(choices=DSR_TYPE_CHOICES, blank=True,
        help_text='An integer code representing a DSR park type')
    mpoly = models.MultiPolygonField(srid=28350, spatial_index=True, geography=False,
        help_text='The polygon representing the shape of the catchment polygon.')
    objects = models.GeoManager()

    def __unicode__(self):
        return '%s %d' % (self.park_type,self.dsr_type)

    class Meta:
        ordering = ['park_type','dsr_type']
        verbose_name = 'Type Catchment Polygon'
        verbose_name_plural = 'Type Catchment Polygons'

# User Profile table - extra fields that auth_user does not have
# One To One relation to auth_user table
class UserProfile(models.Model):
    user = models.OneToOneField(User, unique=True, null=False, db_index=True)
    organisation = models.CharField(max_length=100, blank=True)
    job = models.CharField(max_length=9, choices=USER_JOB_CHOICES, blank=True)
    intent_to_publish = models.BooleanField(default=False, blank=False)

    class Meta:
        ordering = ('user__last_name', 'user__first_name', 'user__username')

    def __unicode__(self):
        return self.user.username

# Define the User Statistic table
class User_Statistic(models.Model):
    all_parks = models.DecimalField(blank=False, null=True,
        max_digits=18, decimal_places=3)
    pocket_park = models.DecimalField(blank=False, null=True,
        max_digits=18, decimal_places=3)
    small_park = models.DecimalField(blank=False, null=True,
        max_digits=18, decimal_places=3)
    medium_park = models.DecimalField(blank=False, null=True,
        max_digits=18, decimal_places=3)
    large_park_1 = models.DecimalField(blank=False, null=True,
        max_digits=18, decimal_places=3)
    large_park_2 = models.DecimalField(blank=False, null=True,
        max_digits=18, decimal_places=3)
    district_park_1 = models.DecimalField(blank=False, null=True,
        max_digits=18, decimal_places=3)
    district_park_2 = models.DecimalField(blank=False, null=True,
        max_digits=18, decimal_places=3)
    regional_space = models.DecimalField(blank=False, null=True,
        max_digits=18, decimal_places=3)
    age_0_4 = models.IntegerField(blank=False, null=True)
    age_5_14 = models.IntegerField(blank=False, null=True)
    age_15_19 = models.IntegerField(blank=False, null=True)
    age_20_24 = models.IntegerField(blank=False, null=True)
    age_25_34 = models.IntegerField(blank=False, null=True)
    age_35_44 = models.IntegerField(blank=False, null=True)
    age_45_54 = models.IntegerField(blank=False, null=True)
    age_55_64 = models.IntegerField(blank=False, null=True)
    age_65_74 = models.IntegerField(blank=False, null=True)
    age_75_84 = models.IntegerField(blank=False, null=True)
    age_85_plus = models.IntegerField(blank=False, null=True)
    total_pop = models.IntegerField(blank=False, null=True)

    def __unicode__(self):
        return self.pk

    class Meta:
        ordering = ['pk']
        verbose_name = 'User Project Statistic'
        verbose_name_plural = 'User Project Statistics'

# Define the user Project table
class Project(models.Model):
    user = models.ForeignKey(User, null=False, db_index=True,
        help_text='Foreign Key based on the "id" of a User')
    region = models.OneToOneField(Region, unique=True, null=False, db_index=True,
        help_text="One To One relationship to a User's Region polygon")
    user_statistic = models.OneToOneField(User_Statistic, unique=True,
        null=False, db_index=True,
        help_text="One To One relationship to a User's modified statistics parameters")
    project_name = models.CharField(max_length=50, blank=False, null=False,
        help_text="The name of the user project")

    def __unicode__(self):
        return self.project_name

    class Meta:
        ordering = ['project_name']
        verbose_name = 'User Defined Project'
        verbose_name_plural = 'User Defined Projects'

# Define the SA1 population data and polygons
class ABS_SA1(models.Model):
    sa1_7digit = models.CharField(max_length=7)
    tot_p_p = models.IntegerField()
    age_0_4__2 = models.IntegerField()
    age_5_14_2 = models.IntegerField()
    age_15_192 = models.IntegerField()
    age_20_242 = models.IntegerField()
    age_25_342 = models.IntegerField()
    age_35_442 = models.IntegerField()
    age_45_542 = models.IntegerField()
    age_55_642 = models.IntegerField()
    age_65_742 = models.IntegerField()
    age_75_842 = models.IntegerField()
    age_85ov_p = models.IntegerField()
    # geom = models.PolygonField(srid=28350)
    mpoly = models.MultiPolygonField(srid=28350, spatial_index=True, geography=False,
        help_text='The polygon representing the shape of the SA1 polygon.')
    objects = models.GeoManager()

    def __unicode__(self):
        return self.sa1_7digit

    class Meta:
        ordering = ['sa1_7digit']
        verbose_name = 'ABS SA1 Polygon'
        verbose_name_plural = 'SA1 Polygons'

# Define the ABS Region population data
class ABS_Region_Population(models.Model):
    #region = models.OneToOneField(Region, unique=True, null=False, db_index=True)
    sub_lga_id = models.CharField(max_length=15, blank=False, null=False,
        help_text="The LGA/Suburb code from UWA for this region.")
    type = models.CharField(max_length=180, choices=ABS_POPULATION_TYPE_CHOICES,
        blank=False, db_index=True,
        help_text='The type of region the ABS population data is for, such as LGA or Suburb')
    tot_p_p = models.IntegerField()
    age_0_4__2 = models.IntegerField()
    age_5_14_2 = models.IntegerField()
    age_15_192 = models.IntegerField()
    age_20_242 = models.IntegerField()
    age_25_342 = models.IntegerField()
    age_35_442 = models.IntegerField()
    age_45_542 = models.IntegerField()
    age_55_642 = models.IntegerField()
    age_65_742 = models.IntegerField()
    age_75_842 = models.IntegerField()
    age_85ov_p = models.IntegerField()

    def __unicode__(self):
        return self.sub_lga_id

    class Meta:
        ordering = ['sub_lga_id']
        verbose_name = 'ABS LGA/Suburb Population Data'
        verbose_name_plural = 'ABS LGA/Suburb Population Datum'
