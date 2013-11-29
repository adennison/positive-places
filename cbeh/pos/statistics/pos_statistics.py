from django.db.models import Sum
from pos.models import *
from pos.constants import *

# Calculate all the POS stats for a given region
def regionPosStats(regionPK):
	# Create an empty dictionary
	regionStats = {}

	# Get the selected region object and area
	region = Region.objects.get(pk=regionPK)
	print region.name
	regionArea = round(region.mpoly.area * .0001,2)

	# Get the POS objects
	posExclude = Pos.objects.filter(mpoly__within=region.mpoly).filter(pos_type_c__in=[1,2,3])	# All parks
	pos_qs = Pos.objects.filter(mpoly__within=region.mpoly).filter(pos_type_c__in=[1,2,3,4])	# All parks + schools

	# Loop through all the POS objects and calculate areas
	total_area = 0
	pos_exclude_area = 0
	pos_park_area = 0
	pos_type_area = {}
	park_type_area = {}
	for pos in pos_qs.area('mpoly'):
	    area = round((pos.area.sq_km * 100),2)
	    total_area += area
	    pos_type_area_area = pos_type_area.setdefault(pos.pos_type_c, 0)
	    pos_type_area[pos.pos_type_c] += area
	    if pos.pos_type_c in (1,2,3,4):
	    	pos_exclude_area += area
	    	if pos.pos_type_c in (1,2,3):
	    		pos_park_area += area
	    if pos.park_type != 0:
	        park_type_area_area = park_type_area.setdefault(pos.park_type, 0)
	        park_type_area_area += area
	        park_type_area[pos.park_type] = park_type_area_area

	# Get all the park POS objects
	totalParks = Pos.objects.filter(mpoly__within=region.mpoly).filter(pos_type_c=POS_TYPE_C_CHOICE_PARK)
	totalParksArea = pos_type_area[1]

	# Calculate Region Stats
	regionStats['frequency_14'] = len(posExclude) 					# Count of pos objects
	regionStats['sum_area_ha_14'] = pos_park_area 					# Area of pos objects
	regionStats['posPercentAreaLga'] = pos_park_area / regionArea 	# pos Area / region area (%)

	# Calculate allPOS stats
	regionStats['frequency_15'] = len(pos_qs) 							# Count of allPos objects
	regionStats['sum_area_ha_15'] = pos_exclude_area 					# allPos area (ha)
	regionStats['allPosPercentAreaLga'] = pos_exclude_area / regionArea	# allPos Area / Region area (%)

	# Loop through the different pos types
	for pos_type_code, pos_type_name in POS_TYPE_C_CHOICES:
		if pos_type_code != POS_TYPE_C_CHOICE_CLUB_OR_PAY:
			# Get the objects
			currentPos = Pos.objects.filter(mpoly__within=region.mpoly).filter(pos_type_c=pos_type_code)
			currentPosArea = pos_type_area[pos_type_code]

			# Calculate the stats
			regionStats['frequency_%s' % pos_type_code] = len(currentPos) 								# Count of all current POS objects
			regionStats['sum_area_ha_%s' % pos_type_code] = currentPosArea 								# Area of current POS objects (ha)
			regionStats['percentpos_%s' % pos_type_code] = round(currentPosArea/pos_park_area,2) 		# POS area / total POS area (%)
			regionStats['percentsublga_%s' % pos_type_code] = round(currentPosArea/regionArea,2) 		# POS area / total region area (%)
			if pos_type_code in (POS_TYPE_C_CHOICE_PARK, POS_TYPE_C_CHOICE_RESIDUAL_GREEN_SPACE,):
				regionStats['percentpark_%s' % pos_type_code] = round(currentPosArea/totalParksArea,2)	# Current POS area / total park area (%)

	# Loop through the different Park types
	for park_type_code, park_type_name in PARK_TYPE_CHOICES:
		# Get the objects
		currentPark = Pos.objects.filter(mpoly__within=region.mpoly).filter(park_type=park_type_code)
		currentParkArea = park_type_area[park_type_code]

		# Calculate the stats
		regionStats['frequency_%s' % park_type_code] = len(currentPark) 							# Count of all current POS objects
		regionStats['sum_area_ha_%s' % park_type_code] = currentParkArea 							# Area of current POS objects (ha)
		regionStats['percentpark_%s' % park_type_code] = round(currentParkArea / totalParksArea,2)	# Park area / total park (%)
		regionStats['percentpos_%s' % park_type_code] = round(currentParkArea / pos_park_area,2) 	# Park area / total POS area (%)
		regionStats['percentsublga_%s' % park_type_code] = round(currentParkArea / regionArea,2) 	# Park area / total region area (%)

	# Calculate the LGA Area Totals
	regionStats['percentsublga_14'] = regionStats['percentsublga_1'] + regionStats['percentsublga_2'] + regionStats['percentsublga_3']
	regionStats['percentsublga_15'] = regionStats['percentsublga_14'] + regionStats['percentsublga_4']

	return regionStats

