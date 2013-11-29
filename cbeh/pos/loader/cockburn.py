# from pos.loader.cockburn import CockburnLoader
# loader = CockburnLoader()
# loader.load_data()

from os import environ, path
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
from django.contrib.gis.gdal import DataSource
from pos.models import *

class CockburnLoader(object):

    BASE_DIR = path.join(environ['WORKSPACE_HOME'], 'test_data', 'cockburn')

    SRID_STR = 'SRID=28350'

    LGA_KEY_NAME = 'LA_NAME'
    LGA_KEY_SHORT_NAME = 'SHORT_NAME'
    LGA_KEY_AREA = 'AREA'

    SUBURB_KEY_NAME = 'NAME_2006'

    POS_KEY_AREA_KM = 'Area_km'
    POS_KEY_SIZE_CLASS = 'SizeClass'
    POS_KEY_TYPE_C = 'POS_Type_C'
    POS_KEY_LGA = 'LGA'
    POS_KEY_OTHER = 'OTHER'

    POS_SIZE_CLASS_REVERSE_LOOKUP = {}
    for tup in POS_SIZE_CLASS_CHOICES:
        POS_SIZE_CLASS_REVERSE_LOOKUP[tup[1]] = tup[0]
    POS_SIZE_CLASS_REVERSE_LOOKUP['Small Neigh Park'] = 'SML'
    POS_SIZE_CLASS_REVERSE_LOOKUP['Med Neigh Park'] = 'MED'
    POS_SIZE_CLASS_REVERSE_LOOKUP['Large Neigh Park'] = 'LRG'

    POS_TYPE_C_REVERSE_LOOKUP = {}
    for tup in POS_TYPE_C_CHOICES:
        POS_TYPE_C_REVERSE_LOOKUP[tup[1]] = tup[0]

    def __init__(self):
        pass

    def load_lga(self, datasource):
        for layer in datasource:
            for feat in layer:
                lga = Lga()
                lga.population = -1;
                lga.name = feat.get(self.LGA_KEY_NAME)
                lga.short_name = feat.get(self.LGA_KEY_SHORT_NAME).title()

                if not lga.short_name:
                    lga.name = 'Unknown'
                    lga.short_name = 'Unknown'

                lga.name = lga.name if len(lga.name.strip()) > 0 else lga.short_name
                lga.area = feat.get(self.LGA_KEY_AREA)
                #geom = GEOSGeometry(';'.join([self.SRID_STR, feat.geom.wkt]))
                geom = GEOSGeometry(feat.geom.transform(4326, True).wkt)
                if geom and isinstance(geom, Polygon):
                    lga.mpoly = MultiPolygon(geom)
                lga.save()
                print 'LGA:', lga.id, lga.name

    def load_suburb(self, datasource):
        for layer in datasource:
            for feat in layer:
                geom = GEOSGeometry(feat.geom.transform(4326, True).wkt)
                suburb = Suburb()
                suburb.name = feat.get(self.SUBURB_KEY_NAME)
                suburb.population = -1;
                suburb.area = -1;
                suburb.mpoly = geom if isinstance(geom, MultiPolygon) else MultiPolygon(geom)

                if Lga.objects.filter(mpoly__intersects=suburb.mpoly).count() > 0:
                    suburb.save()
                    print 'Suburb:', suburb.id, suburb.name

    def load_pos(self, datasource):
        for layer in datasource:
            for feat in layer:
                geom = GEOSGeometry(feat.geom.transform(4326, True).wkt)
                pos = Pos()
                pos.lga = Lga.objects.get(short_name=feat.get(self.POS_KEY_LGA))
                pos.size_class = self.POS_SIZE_CLASS_REVERSE_LOOKUP[feat.get(self.POS_KEY_SIZE_CLASS)]
                pos.pos_type_c = self.POS_TYPE_C_REVERSE_LOOKUP[feat.get(self.POS_KEY_TYPE_C)]
                pos.area = feat.get(self.POS_KEY_AREA_KM) * 1000000
                pos.mpoly = geom if isinstance(geom, MultiPolygon) else MultiPolygon(geom)
                pos.save()
                print 'POS:', pos.id, pos.pos_type_c

                for suburb in Suburb.objects.filter(mpoly__intersects=pos.mpoly):
                    pos_to_suburb = PosToSuburbMapping()
                    pos_to_suburb.pos = pos
                    pos_to_suburb.suburb = suburb
                    pos_to_suburb.area = -1
                    pos_to_suburb.save()
                    print '\tPOS To Suburb Mapping:', pos_to_suburb.id, pos_to_suburb.suburb.name

                for facility_choice in POS_FACILITY_CHOICES:
                    facility_code = facility_choice[0]
                    if not facility_code == self.POS_KEY_OTHER:
                        count = feat.get(facility_code)
                        if count and count > 0:
                            facility = Facility()
                            facility.count = count
                            facility.facility_type = facility_code
                            facility.pos = pos
                            facility.save()
                            print '\tFacility:', facility.id, facility.facility_type

                other = feat.get(self.POS_KEY_OTHER)
                if other.strip() and other != '0':
                    facility = Facility()
                    facility.count = 1
                    facility.facility_type = self.POS_KEY_OTHER
                    facility.other = other
                    facility.pos = pos
                    facility.save()
                    print '\tFacility:', facility.id, facility.facility_type

    def load_data(self):
        lga_ds = DataSource(path.join(self.BASE_DIR, 'lga', 'LGA_Boundaries.shp'))
        suburb_ds = DataSource(path.join(self.BASE_DIR, 'suburb', 'WASuburbs2006_proj.shp'))
        pos_ds = DataSource(path.join(self.BASE_DIR, 'pos', 'ANDS_sample_COCKBURN.shp'))

        self.load_lga(lga_ds)
        self.load_suburb(suburb_ds)
        self.load_pos(pos_ds)

        print lga_ds
        print suburb_ds
        print pos_ds