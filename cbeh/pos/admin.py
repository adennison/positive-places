from django.contrib.gis import admin
from pos.models import *

class PosAdmin(admin.GeoModelAdmin):
    list_display = ('lga', 'size_class', 'pos_type_c', 'area')
    list_filter = ('size_class', 'pos_type_c')
#admin.site.register(Pos, PosAdmin)

class SuburbAdmin(admin.GeoModelAdmin):
    list_display = ('name', 'population', 'area')
#admin.site.register(Suburb, SuburbAdmin)

class LgaAdmin(admin.GeoModelAdmin):
    list_display = ('name', 'population', 'area')
#admin.site.register(Lga, LgaAdmin)

class PosToSuburbMappingAdmin(admin.ModelAdmin):
    list_display = ('pos', 'suburb', 'area')
    list_filter = ('suburb',)
#admin.site.register(PosToSuburbMapping, PosToSuburbMappingAdmin)

class FacilityAdmin(admin.ModelAdmin):
    list_display = ('facility_type', 'count', 'pos')
    list_filter = ('facility_type',)
#admin.site.register(Facility, FacilityAdmin)