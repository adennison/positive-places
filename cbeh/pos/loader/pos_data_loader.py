## Data loader for POS data into PostGIS database
## Written by B Khoo and A Hayek
## June 2012
##
## Example instantiation and usage:
#from pos.loader.pos_data_loader import PosDataLoader # import the class
#loader = PosDataLoader() # Create an object of the class
#loader.load_pos() # Call the load_pos method

# Import some classes
from os import environ, path
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
from django.contrib.gis.gdal import DataSource
from pos.models import *
import csv

# PosDataLoader class
class PosDataLoader(object):

    # Set up constants

    # MGA Zone 50
    SRID_STR = 'SRID=28350'
    SRID_INT = 28350

    # Region SHP Keys
    REGION_KEY_SUB_ID = 'SSC_CODE'
    REGION_KEY_LGA_ID = 'LGA_CODE'
    REGION_KEY_NAME = 'NAME'
    REGION_KEY_SHORT_NAME = 'SHORT_NAME'
    REGION_KEY_TYPE = 'TYPE'

    # POS SHP Keys
    POS_KEY_SOURCE_ID = 'POSID'
    POS_KEY_PART_ID = 'PARTID'
    POS_KEY_UID = 'UID'
    POS_KEY_TYPE_CLASS = 'POS_TYPE_C'
    POS_KEY_PARK_NAME = 'PARK_NAME'
    POS_KEY_PARK_TYPE = 'PARK_TYPE'
    POS_KEY_DSR_TYPE = 'DSR_TYPE'
    POS_KEY_POS_DAT = 'POS_DAT'
    POS_KEY_ADJ_PSF = 'ADJ_PSF'
    POS_KEY_ADJ_BF = 'ADJ_BF'
    POS_KEY_QUAL_CHILD = 'QUAL_CHILD'
    POS_KEY_QUAL_ADOLE = 'QUAL_ADOLE'
    POS_KEY_QUAL_ADULT = 'QUAL_ADULT'

    # SA1 SHP Keys
    SA1_KEY_7DIGIT = 'SA1_7DIGIT'
    SA1_KEY_TOT_P_P = 'TOT_P_P'
    SA1_KEY_AGE_0_4__2 = 'AGE_0_4__2'
    SA1_KEY_AGE_5_14_2 = 'AGE_5_14_2'
    SA1_KEY_AGE_15_192 = 'AGE_15_192'
    SA1_KEY_AGE_20_242 = 'AGE_20_242'
    SA1_KEY_AGE_25_342 = 'AGE_25_342'
    SA1_KEY_AGE_35_442 = 'AGE_35_442'
    SA1_KEY_AGE_45_542 = 'AGE_45_542'
    SA1_KEY_AGE_55_642 = 'AGE_55_642'
    SA1_KEY_AGE_65_742 = 'AGE_65_742'
    SA1_KEY_AGE_75_842 = 'AGE_75_842'
    SA1_KEY_AGE_85OV_p = 'AGE_85OV_p'

    # Catchment SHP Keys
    CATCHMENT_KEY_CATCHMENT_ID = 'CATCHMENT_ID'
    CATCHMENT_KEY_PARK_TYPE = 'PARK_TYPE'
    CATCHMENT_KEY_DSR_TYPE = 'DSR_TYPE'

    # Facility CSV Keys
    FACILITY_KEY_SOURCE_ID = 'posid'
    FACILITY_KEY_PART_ID = 'partid'
    FACILITY_KEY_UID = 'uid'
    FACILITY_KEY_OTHER = 'other'

    # Area and Population Stats, and Facility Stats Keys
    STATS_KEY_SUB_LGA_CODE = 'sub_lga_code'
    STATS_KEY_PARK_TYPE = 'park_type'
    STATS_KEY_DSR_TYPE = 'dsr_type'

    # POS Type
    POS_TYPE_C_REVERSE_LOOKUP = {}
    for tup in POS_TYPE_C_CHOICES: # POS_TYPE_C_CHOICES, imported from models.py
        POS_TYPE_C_REVERSE_LOOKUP[tup[1]] = tup[0]

    # POS Facility
    POS_FACILITY_REVERSE_LOOKUP = {}
    for tup in POS_FACILITY_CHOICES: # POS_FACILITY_CHOICES, imported from models.py
        POS_FACILITY_REVERSE_LOOKUP[tup[1]] = tup[0]

    def __init__(self):
        pass

    # Handles the data loading from the shapefiles
    def load_shapefile(self, datasource, type):
        if type == 'POS':
            self.load_pos(datasource)
        elif type == 'SA1':
            self.load_sa1(datasource, type)
        elif type == "CATCHMENTS":
            self.load_catchment(datasource, type)
        else:
            self.load_region(datasource, type)

    # Load a CSV file - checks which type, then calls appropriate function
    def load_csv_file(self, fileObject, type):
        if type == 'FACILITY':
            self.load_facilities(fileObject)
        elif (type == 'AREA_POP_STATS') or (type == 'FACILITIES_STATS'):
            self.load_stats_file(fileObject, type)
        elif (type == 'LGA_POPULATION') or (type == 'SUBURB_POPULATION'):
            self.load_lga_suburb_population_data(fileObject, type)

    # Load POS shapefile
    def load_pos(self, datasource):
        for layer in datasource:
            for feat in layer:
                pos = Pos() # class imported from models.py
                pos.source_id = feat.get(self.POS_KEY_SOURCE_ID)
                pos.part_id = feat.get(self.POS_KEY_PART_ID)
                pos.uid = feat.get(self.POS_KEY_UID)
                pos.pos_type_c = feat.get(self.POS_KEY_TYPE_CLASS)
                pos.park_name = feat.get(self.POS_KEY_PARK_NAME)
                pos.park_type = feat.get(self.POS_KEY_PARK_TYPE)
                pos.dsr_type = feat.get(self.POS_KEY_DSR_TYPE)
                pos.pos_dat = feat.get(self.POS_KEY_POS_DAT)
                pos.adj_psf = feat.get(self.POS_KEY_ADJ_PSF)
                pos.adj_bf = feat.get(self.POS_KEY_ADJ_BF)
                pos.qual_child = feat.get(self.POS_KEY_QUAL_CHILD)
                pos.qual_adole = feat.get(self.POS_KEY_QUAL_ADOLE)
                pos.qual_adult = feat.get(self.POS_KEY_QUAL_ADULT)
                geom = GEOSGeometry(feat.geom.transform(self.SRID_INT, True).wkt)
                pos.mpoly = geom if isinstance(geom, MultiPolygon) else MultiPolygon(geom)
                pos.save()
                #print 'POS:', pos.pk, pos.source_id, pos.pos_type_c, pos.park_name

    # Load a Region shapefile (Suburb / LGA / Metro Area / City)
    def load_region(self, datasource, type):
        for layer in datasource:
            layerFieldsLowercase = [fieldName.lower() for fieldName in layer.fields]
            for feat in layer:
                # Create a region object
                region = Region() # class imported from models.py
                # Check if the datasource has SSC_CODE field, if not populate using LGA_CODE field
                if self.REGION_KEY_SUB_ID.lower() in layerFieldsLowercase:
                    region.sub_lga_id = feat.get(self.REGION_KEY_SUB_ID)
                else:
                    region.sub_lga_id = feat.get(self.REGION_KEY_LGA_ID)
                region.name = feat.get(self.REGION_KEY_NAME)
                # Check if the datasource has SHORT_NAME field, if not populate with NAME field
                if self.REGION_KEY_SHORT_NAME.lower() in layerFieldsLowercase:
                    region.short_name = feat.get(self.REGION_KEY_SHORT_NAME).title()
                else:
                    region.short_name = region.name
                region.type = type
                geom = GEOSGeometry(feat.geom.transform(self.SRID_INT, True).wkt)
                if geom and isinstance(geom, Polygon):
                    region.mpoly = MultiPolygon(geom)
                elif geom and isinstance(geom, MultiPolygon):
                    region.mpoly = geom
                region.save()
                #print 'REGION: ', region.id, region.type, region.name

    # Load a SA1 shapefile
    def load_sa1(self, datasource, type):
        for layer in datasource:
            for feat in layer:
                abs_sa1 = ABS_SA1()
                abs_sa1.sa1_7digit = feat.get(self.SA1_KEY_7DIGIT)
                abs_sa1.tot_p_p = feat.get(self.SA1_KEY_TOT_P_P)
                abs_sa1.age_0_4__2 = feat.get(self.SA1_KEY_AGE_0_4__2)
                abs_sa1.age_5_14_2 = feat.get(self.SA1_KEY_AGE_5_14_2)
                abs_sa1.age_15_192 = feat.get(self.SA1_KEY_AGE_15_192)
                abs_sa1.age_20_242 = feat.get(self.SA1_KEY_AGE_20_242)
                abs_sa1.age_25_342 = feat.get(self.SA1_KEY_AGE_25_342)
                abs_sa1.age_35_442 = feat.get(self.SA1_KEY_AGE_35_442)
                abs_sa1.age_45_542 = feat.get(self.SA1_KEY_AGE_45_542)
                abs_sa1.age_55_642 = feat.get(self.SA1_KEY_AGE_55_642)
                abs_sa1.age_65_742 = feat.get(self.SA1_KEY_AGE_65_742)
                abs_sa1.age_75_842 = feat.get(self.SA1_KEY_AGE_75_842)
                abs_sa1.age_85ov_p = feat.get(self.SA1_KEY_AGE_85OV_p)
                geom = GEOSGeometry(feat.geom.transform(self.SRID_INT, True).wkt)
                abs_sa1.mpoly = geom if isinstance(geom, MultiPolygon) else MultiPolygon(geom)
                abs_sa1.save()

    # Load a Catchment shapefile
    def load_catchment(self, datasource, type):
        for layer in datasource:
            for feat in layer:
                catchment = Catchment_Polygon()
                catchment.park_type = feat.get(self.CATCHMENT_KEY_PARK_TYPE)
                catchment.dsr_type = feat.get(self.CATCHMENT_KEY_DSR_TYPE)
                geom = GEOSGeometry(feat.geom.transform(self.SRID_INT, True).wkt)
                catchment.mpoly = geom if isinstance(geom, MultiPolygon) else MultiPolygon(geom)
                catchment.save()

    # Load a LGA/Suburb population data CSV file
    def load_lga_suburb_population_data(self, fileObject, type):
        if type == 'LGA_POPULATION':
            fieldsDict = LGA_ABS_STATS_FIELDS
            populationChoice = ABS_POPULATION_TYPE_CHOICE_LGA
        elif type == 'SUBURB_POPULATION':
            fieldsDict = SUBURB_ABS_STATS_FIELDS
            populationChoice = ABS_POPULATION_TYPE_CHOICE_SUBURB
        csvReader = csv.reader(fileObject) # Create a CSV reader object
        fieldList = csvReader.next() # Get the field names from the header
        fieldList = [fieldName.lower() for fieldName in fieldList] # Make all fields lowercase
        for oneLineList in csvReader:
            oneLineList = [' '.join(item.split()) for item in oneLineList] # strip all spaces, except for internals
            if any(oneLineList): # if data exists in this list
                lineDict = dict(zip(fieldList, oneLineList)) # map {field_name : row_data, ...}
                popRow = ABS_Region_Population() # Create a table row
                for key in lineDict:
                    if key in fieldsDict:
                        # Add data into the table row
                        if self.is_number(lineDict[key]):
                            setattr(popRow, key, int(lineDict[key]))
                        else:
                            if (key == 'lga_code') or (key == 'ssc_code'):
                                popRow.sub_lga_id = lineDict[key]

                            else:
                                setattr(popRow, key, lineDict[key])
                popRow.type = populationChoice
                popRow.save()

    # Load Area & Population Statistics CSV file, or,
    # Load Facilities Statistics file - require pivot to data
    def load_stats_file(self, fileObject, type):
        csvReader = csv.reader(fileObject) # Create a CSV reader object
        fieldList = csvReader.next() # Get the field names from the header
        fieldList = [fieldName.lower() for fieldName in fieldList] # Make all fields lowercase
        for oneLineList in csvReader:
            oneLineList = [' '.join(item.split()) for item in oneLineList] # strip all spaces, except for internals
            if any(oneLineList): # if data exists in this list
                lineDict = dict(zip(fieldList, oneLineList)) # map {field_name : row_data, ...}
                for key in lineDict:
                    # Only create row if this key is Facility Stats info (not IDs, etc.)
                    if key not in [self.STATS_KEY_SUB_LGA_CODE, self.STATS_KEY_PARK_TYPE, self.STATS_KEY_DSR_TYPE]:
                        if self.is_number(lineDict[key]):
                            if type == 'AREA_POP_STATS':
                                statRow = Area_Pop_Stats()
                                statRow.dsr_type = lineDict[self.STATS_KEY_DSR_TYPE]
                                statRow.region_stat = key
                                statRow.region_value = "%.15g" % float(lineDict[key]) # Python 2.6 converting float to decimal!
                            elif type == 'FACILITIES_STATS':
                                statRow = Facility_Statistics()
                                statRow.facility_stat = key
                                statRow.facility_count = int(lineDict[key])
                            # Extract the single item from the queryset using [0]
                            statRow.region_pk = Region.objects.filter(sub_lga_id=lineDict[self.STATS_KEY_SUB_LGA_CODE])[0]
                            statRow.park_type = lineDict[self.STATS_KEY_PARK_TYPE]
                            statRow.save()

    # Load Facilities Statistics CSV file - requires pivot to data
    def load_facilities_stats(self, fileObject, type):
        csvReader = csv.reader(fileObject) # Create a CSV reader object
        fieldList = csvReader.next() # Get the field names from the header
        fieldList = [fieldName.lower() for fieldName in fieldList] # Make all fields lowercase
        for oneLineList in csvReader:
            oneLineList = [' '.join(item.split()) for item in oneLineList] # strip all spaces, except for internals
            if any(oneLineList): # if data exists in this list
                lineDict = dict(zip(fieldList, oneLineList)) # map {field_name : row_data, ...}
                for key in lineDict:
                    # Only create row if this key is Facility Stats info (not IDs, etc.)
                    if key not in [self.STATS_KEY_SUB_LGA_CODE, self.STATS_KEY_PARK_TYPE]:
                        if self.is_number(lineDict[key]):
                            facilityStat = Facility_Statistics()
                            facilityStat.region_pk = Region.objects.filter(sub_lga_id=lineDict[self.STATS_KEY_SUB_LGA_CODE])[0] # extract the single item from the queryset with [0]
                            areaPopStat.park_type = lineDict[self.STATS_KEY_PARK_TYPE]
                            areaPopStat.region_stat = key
                            areaPopStat.region_value = float(lineDict[key])
                            areaPopStat.save()

    # Load Facilities CSV file - requires pivot to data
    def load_facilities(self, fileObject):
        csvReader = csv.reader(fileObject) # Create a CSV reader object
        fieldList = csvReader.next() # Get the field names from the header
        fieldList = [fieldName.lower() for fieldName in fieldList] # Make all fields lowercase
        for oneLineList in csvReader:
            oneLineList = [' '.join(item.split()) for item in oneLineList] # strip all spaces, except for internals
            if any(oneLineList): # if data exists in this list
                lineDict = dict(zip(fieldList, oneLineList)) # map {field_name : row_data, ...}
                for key in lineDict:
                    # Only create row if this key is Facility info (not IDs, etc.)
                    if key not in [self.FACILITY_KEY_SOURCE_ID, self.FACILITY_KEY_PART_ID, self.FACILITY_KEY_UID]:
                        facility = Facility()
                        #facility.source_id = int(lineDict[self.FACILITY_KEY_SOURCE_ID])
                        #facility.part_id = int(lineDict[self.FACILITY_KEY_PART_ID])
                        facility.pos_pk = Pos.objects.filter(uid=lineDict[self.FACILITY_KEY_UID])[0] # extract the single item from the queryset with [0]
                        if key == self.FACILITY_KEY_OTHER:
                            facility.facility_type = self.FACILITY_KEY_OTHER
                            if lineDict[key]: # if not an empty string
                                facility.other = lineDict[key]
                            if lineDict[key]:
                                facility.code = 1
                            else:
                                facility.code = 0
                        else:
                            facility.facility_type = key
                            if lineDict[key]:
                                facility.code = int(lineDict[key])
                    facility.save()

    # Delete all records from a database table, e.g. all Suburbs
    def del_db_table_rows(self, type):
        if type == 'POS':
            querySet = Pos.objects.all() # Pos class imported from models.py
        elif type == 'FACILITY':
            querySet = Facility.objects.all() # Facility class imported from models.py
        elif type == 'AREA_POP_STATS':
            querySet = Area_Pop_Stats.objects.all()
        elif type == 'FACILITIES_STATS':
            querySet = Facility_Statistics.objects.all()
        elif type == 'SA1':
            querySet = ABS_SA1.objects.all()
        elif type == 'LGA_POPULATION':
            querySet = ABS_Region_Population.objects.filter(type=ABS_POPULATION_TYPE_CHOICE_LGA)
        elif type == 'SUBURB_POPULATION':
            querySet = ABS_Region_Population.objects.filter(type=ABS_POPULATION_TYPE_CHOICE_SUBURB)
        elif type == 'CATCHMENTS':
            querySet = Catchment_Polygon.objects.all()
        else:
            querySet = Region.objects.filter(type__exact=type) # Region class imported from models.py
        if (querySet.exists()):
            querySet.delete() # Delete occurs only if there is anything to delete

    # Do a check if string is a number
    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False
