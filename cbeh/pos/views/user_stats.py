import json

from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.template import RequestContext, loader
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required

from pos.models import *
from pos.statistics import build_stats

from datetime import datetime
import xlwt

@login_required()
def details(request, pk):
    project_obj = Project.objects.get(pk=pk)

    # Check if region has a polygon (and hence any stats yet)
    if project_obj.region.mpoly is None:
        raise Http404, 'You need to draw a region for your project before you can view any scenario calculations. Please create one before viewing scenario calculations.'

    # Get modifiable stats
    stats = User_Statistic.objects.get(project=project_obj)

    # if project_obj.region.type[:2] == REGION_TYPE_CHOICE_USER_LGA_SUBURB:
    #     region_pk = project_obj.region.type[3:]
    #     region = Region.objects.get(pk=region_pk)
    #     # Get original stats
    #     # Area stats
    #     park_stats = get_area_stats(region, 1)
    #     # Population stats
    #     sub_lga_id = region.sub_lga_id
    #     population_stats = ABS_Region_Population.objects.get(sub_lga_id=sub_lga_id)
    # else:
    # Get original stats
    # Area stats
    park_stats = get_area_stats(project_obj)
    # Population stats
    population_stats = ABS_Region_Population.objects.get(sub_lga_id=project_obj.region.sub_lga_id)

    # Multiplier to convert hectares to square metres
    sq_m = 10000
    values_dict = {
        'parks': {
            'all_parks': park_stats[0]['region_value'] * sq_m,
            'natural': park_stats[1]['region_value'] * sq_m,
            'residual': park_stats[2]['region_value'] * sq_m,
            'school_grounds': park_stats[3]['region_value'] * sq_m,
            'pocket_parks': park_stats[5]['region_value'] * sq_m,
            'small_parks': park_stats[6]['region_value'] * sq_m,
            'medium_parks': park_stats[7]['region_value'] * sq_m,
            'large_parks_1': park_stats[8]['region_value'] * sq_m,
            'large_parks_2': park_stats[9]['region_value'] * sq_m,
            'district_parks_1': park_stats[10]['region_value'] * sq_m,
            'district_parks_2': park_stats[11]['region_value'] * sq_m,
            'regional_parks': park_stats[12]['region_value'] * sq_m
        },
        'populations': {
            'age_0_4': population_stats.age_0_4__2,
            'age_5_14': population_stats.age_5_14_2,
            'age_15_19': population_stats.age_15_192,
            'age_20_24': population_stats.age_20_242,
            'age_25_34': population_stats.age_25_342,
            'age_35_44': population_stats.age_35_442,
            'age_45_54': population_stats.age_45_542,
            'age_55_64': population_stats.age_55_642,
            'age_65_74': population_stats.age_65_742,
            'age_75_84': population_stats.age_75_842,
            'age_85_plus': population_stats.age_85ov_p,
            'total_pop': population_stats.tot_p_p
        }
    }

    # Load the template
    c = RequestContext(request, {
                'user_stats': stats,
                'original_stats': values_dict,
                'project_pk': project_obj.pk,
                'project_name': project_obj.project_name,
                'region': project_obj.region
            })
    t = loader.get_template('pos/user_stats/user_stats.html')
    return HttpResponse(t.render(c))
    # return render_to_response('pos/user_stats/user_stats.html', {})

# Calculate the Area/Population/Catchment statistics for all LGAS
@login_required()
def calculate_lga_stats(request):
    build_stats.areaPosStats_lgas()
    return HttpResponse(json.dumps("Success"), mimetype="application/json")

# Calculate the Area/Population/Catchment statistics for all Suburbs
@login_required()
def calculate_suburb_stats(request):
    build_stats.areaPosStats_suburbs()
    return HttpResponse(json.dumps("Success"), mimetype="application/json")

# Calculate the Facility statistics for all LGAs and Suburbs
@login_required()
def calculate_facility_stats(request):
    build_stats.facilityStats()
    return HttpResponse(json.dumps("Success"), mimetype="application/json")

# Save modified scenario figures for a user region
@login_required()
def save_modified_stats(request):
    area_list = request.POST.getlist('area_list[]')
    population_list = request.POST.getlist('pop_list[]')
    project_pk = int(request.POST['project_pk'])

    # Check data in lists are numbers only
    areas_ok = check_area_list(area_list)
    populations_ok = check_population_list(population_list)

    data = [areas_ok, populations_ok]

    # Store modified stats if everything is in acceptable format
    if areas_ok and populations_ok:
        # Get the user stat data row
        project_obj = Project.objects.get(pk=project_pk)
        user_stat = User_Statistic.objects.get(project=project_obj)
        # Area stats
        user_stat.all_parks = area_list[0]
        user_stat.pocket_park = area_list[1]
        user_stat.small_park = area_list[2]
        user_stat.medium_park = area_list[3]
        user_stat.large_park_1 = area_list[4]
        user_stat.large_park_2 = area_list[5]
        user_stat.district_park_1 = area_list[6]
        user_stat.district_park_2 = area_list[7]
        user_stat.regional_space = area_list[8]
        # Population stats
        user_stat.age_0_4 = population_list[0]
        user_stat.age_5_14 = population_list[1]
        user_stat.age_15_19 = population_list[2]
        user_stat.age_20_24 = population_list[3]
        user_stat.age_25_34 = population_list[4]
        user_stat.age_35_44 = population_list[5]
        user_stat.age_45_54 = population_list[6]
        user_stat.age_55_64 = population_list[7]
        user_stat.age_65_74 = population_list[8]
        user_stat.age_75_84 = population_list[9]
        user_stat.age_85_plus = population_list[10]
        user_stat.total_pop = population_list[11]

        user_stat.save()

    return HttpResponse(json.dumps(data), mimetype="application/json")

@login_required()
def calculate_metrics(request):

    area_list = request.GET.getlist('area_list[]')
    population_list = request.GET.getlist('population_list[]')

    # Check data in lists are numbers only
    areas_ok = check_area_list(area_list)
    populations_ok = check_population_list(population_list)

    data = [areas_ok, populations_ok]

    if areas_ok and populations_ok:
        # Begin calculations and store into list
        all_metrics = []
        for pop in population_list:
            age_metrics = []
            for area in area_list:
                if float(pop) == 0:
                    age_metrics.append('0.00')
                else:
                    age_metrics.append( "%.2f" % (float(area) / float(pop)))
            all_metrics.append(age_metrics)

        data.append(all_metrics)

    return HttpResponse(json.dumps(data), mimetype="application/json")

@login_required()
def reset_areas(request):

    project_pk = int(request.GET['project_pk'])
    project_obj = Project.objects.get(pk=project_pk)
    park_stats = get_area_stats(project_obj)

     # Multiplier to convert hectares to square metres
    sq_m = 10000
    park_areas_dict = {
        'all_parks': floatformat(float(park_stats[0]['region_value']) * sq_m),
        'pocket_parks': floatformat(float(park_stats[5]['region_value']) * sq_m),
        'small_parks': floatformat(float(park_stats[6]['region_value']) * sq_m),
        'medium_parks': floatformat(float(park_stats[7]['region_value']) * sq_m),
        'large_parks_1': floatformat(float(park_stats[8]['region_value']) * sq_m),
        'large_parks_2': floatformat(float(park_stats[9]['region_value']) * sq_m),
        'district_parks_1': floatformat(float(park_stats[10]['region_value']) * sq_m),
        'district_parks_2': floatformat(float(park_stats[11]['region_value']) * sq_m),
        'regional_parks': floatformat(float(park_stats[12]['region_value']) * sq_m)
    }

    return HttpResponse(json.dumps(park_areas_dict), mimetype="application/json")

@login_required()
def reset_populations(request):

    project_pk = int(request.GET['project_pk'])
    project_obj = Project.objects.get(pk=project_pk)
    population_stats = ABS_Region_Population.objects.get(sub_lga_id=project_obj.region.sub_lga_id)

    populations_dict = {
        'age_0_4': population_stats.age_0_4__2,
        'age_5_14': population_stats.age_5_14_2,
        'age_15_19': population_stats.age_15_192,
        'age_20_24': population_stats.age_20_242,
        'age_25_34': population_stats.age_25_342,
        'age_35_44': population_stats.age_35_442,
        'age_45_54': population_stats.age_45_542,
        'age_55_64': population_stats.age_55_642,
        'age_65_74': population_stats.age_65_742,
        'age_75_84': population_stats.age_75_842,
        'age_85_plus': population_stats.age_85ov_p,
        'total_pop': population_stats.tot_p_p
    }

    return HttpResponse(json.dumps(populations_dict), mimetype="application/json")

@login_required()
def download_scenario_stats(request):
    if request.method == 'POST':
        if 'project_pk' in request.POST:
            project_pk = request.POST['project_pk']

            # Get the user stat data row
            project_obj = Project.objects.get(pk=project_pk)
            user_stat = User_Statistic.objects.get(project=project_obj)

            # Get the project name to save the file name as
            fileName = project_obj.project_name.replace(' ', '_') + '_Scenario_' + str(date.today()) + '.xls'
            # Create the Excel file
            response = HttpResponse(mimetype='application/ms-excel')
            response['Content-Disposition'] = 'attachment; filename=%s' % fileName
            # Create the Workbook and Worksheets
            wb = xlwt.Workbook()
            scenario_sheet = wb.add_sheet('Scenario Modelling')

            # Set some styles
            # Note: multiply the font text size by 20 to get the correct 'height'
            styles = {
                'styleHead1' : xlwt.easyxf('font: name Calibri, colour dark_green_ega, bold 1, height 320'),
                'styleHead1TopLeftRightBorder' : xlwt.easyxf('font: name Calibri, colour dark_green_ega, bold 1, height 320; border: top thin, left thin, right thin'),
                'styleHead2CentredLeftRightBorder' : xlwt.easyxf('font: name Calibri, bold 1, height 240; alignment: horizontal center; border: left thin, right thin'),
                'styleHead2' : xlwt.easyxf('font: name Calibri, bold 1, height 240'),
                'styleHead2CentredRightBorder' : xlwt.easyxf('font: name Calibri, bold 1, height 240; alignment: horizontal center; border: right thin'),
                'styleBold' : xlwt.easyxf('font: name Calibri, bold 1'),
                'styleBoldCentred' : xlwt.easyxf('font: name Calibri, bold 1; alignment: horizontal center, vertical center, wrap 1'),
                'styleBoldBorderTopLeftRightCellColourWhite': xlwt.easyxf('font: name Calibri, bold 1; border: left thin, top thin, right thin; pattern: pattern solid, fore_colour white'),
                'styleItalic' : xlwt.easyxf('font: name Calibri, italic 1'),
                'styleItalicRight' : xlwt.easyxf('font: name Calibri, italic 1; alignment: horizontal right'),
                'styleItalicRightWrap' : xlwt.easyxf('font: name Calibri, italic 1; alignment: horizontal right, vertical center, wrap 1;'),
                'styleItalicCellColourWhite' : xlwt.easyxf('font: name Calibri, italic 1; pattern: pattern solid, fore_colour white'),
                'styleItalicCellColourWhiteRight' : xlwt.easyxf('font: name Calibri, italic 1; pattern: pattern solid, fore_colour white; alignment: horizontal right, vertical center, wrap 1'),
                'styleItalicCellColourWhiteRightTopBorder' : xlwt.easyxf('font: name Calibri, italic 1; pattern: pattern solid, fore_colour white; alignment: horizontal right, vertical center, wrap 1;border: top thin; pattern: pattern solid, fore_colour white'),
                'styleBoldItalic' : xlwt.easyxf('font: name Calibri, bold 1, italic 1'),
                'styleBoldItalicCentred' : xlwt.easyxf('font: name Calibri, bold 1, italic 1; alignment: horizontal center, vertical center, wrap 1'),
                'styleBoldItalicCentredRightBorder' : xlwt.easyxf('font: name Calibri, bold 1, italic 1; alignment: horizontal center, vertical center, wrap 1; border: right thin'),
                'styleBoldItalicCentredBottomBorder' : xlwt.easyxf('font: name Calibri, bold 1, italic 1; alignment: horizontal center, vertical center, wrap 1; border: bottom thin'),
                'styleBoldItalicCentredRightBottomBorder' : xlwt.easyxf('font: name Calibri, bold 1, italic 1; alignment: horizontal center, vertical center, wrap 1; border: right thin, bottom thin'),
                'styleNormalCentred' : xlwt.easyxf('font: name Calibri; alignment: horizontal center'),
                'styleNormalCentredBottomBorder' : xlwt.easyxf('font: name Calibri; alignment: horizontal center; border: bottom thin'),
                'styleNormalCentredBottomRightBorder' : xlwt.easyxf('font: name Calibri; alignment: horizontal center; border: bottom thin, right thin'),
                'styleNormalCentredBottomBorderRedText' : xlwt.easyxf('font: name Calibri, colour red; alignment: horizontal center; border: bottom thin'),
                'styleNormalLeft' : xlwt.easyxf('font: name Calibri; alignment: horizontal left'),
                'styleNormalRight' : xlwt.easyxf('font: name Calibri; alignment: horizontal right'),
                'styleNormalCentredRightBorder' : xlwt.easyxf('font: name Calibri; alignment: horizontal center; border: right thin'),
                'styleNormalCentredVertical' : xlwt.easyxf('font: name Calibri; alignment: horizontal center, vertical center'),
                'styleNormalCentredVerticalRightBorder' : xlwt.easyxf('font: name Calibri; alignment: horizontal center, vertical center; border: right thin'),
                'styleNormalCentredVerticalRightBottomBorder': xlwt.easyxf('font: name Calibri; alignment: horizontal center, vertical center; border: bottom thin, right thin'),
                'styleNormalCentredRightBorderRedText' : xlwt.easyxf('font: name Calibri, colour red; alignment: horizontal center; border: right thin'),
                'styleNormalCentredVerticalRightBottomBorderRedText' : xlwt.easyxf('font: name Calibri, colour red; alignment: horizontal center, vertical center; border: right thin, bottom thin'),
                'styleNormalCentredVerticalBottomBorderRedText' : xlwt.easyxf('font: name Calibri, colour red; alignment: horizontal center, vertical center; border: bottom thin'),
                'styleNormalCentredRightBottomBorderRedText' : xlwt.easyxf('font: name Calibri, colour red; alignment: horizontal center; border: right thin, bottom thin'),
                'styleNormal' : xlwt.easyxf('font: name Calibri;'),
                'styleNormalCellColourWhite' : xlwt.easyxf('font: name Calibri; pattern: pattern solid, fore_colour white'),
                #'styleNormalCellColourRed' : xlwt.easyxf('font: name Calibri, colour Red; pattern: pattern solid, fore_colour white'),
                'styleNormalCellColourRed' : xlwt.easyxf('font: name Calibri, colour Red'),
                'styleNormalLeftBorder' : xlwt.easyxf('font: name Calibri; border: left thin; pattern: pattern solid, fore_colour white'),
                'styleNormalRightBorder' : xlwt.easyxf('font: name Calibri; border: right thin; pattern: pattern solid, fore_colour white'),
                #'styleNormalTopBorder' : xlwt.easyxf('font: name Calibri; border: top thin; pattern: pattern solid, fore_colour white'),
                'styleNormalTopBorder' : xlwt.easyxf('font: name Calibri; border: top thin'),
                'styleNormalBorderLeftRightCellColourWhite': xlwt.easyxf('font: name Calibri; border: left thin, right thin; pattern: pattern solid, fore_colour white'),
                'styleNormalBorderLeftBottomRightCellColourWhite': xlwt.easyxf('font: name Calibri; border: left thin, bottom thin, right thin; pattern: pattern solid, fore_colour white'),
                'styleNormalSuperScript' : xlwt.easyxf('font: name Calibri, escapement superscript'),
             }
            style1 = xlwt.easyxf(num_format_str='D-MMM-YY')
            # Write the relevant data to each worksheet
            writeToScenarioSheet(scenario_sheet, styles, project_obj, user_stat)
            wb.save(response)

            return response

def writeToScenarioSheet(sheet, styles, project, user_stat):

    # Start writing the context information to the worksheet
    sheet.write_merge(0, 0, 0, 15, 'Scenario Modelling: ' + project.project_name, styles['styleHead1'])
    sheet.write_merge(1, 1, 0, 4)
    sheet.write_merge(1, 1, 5, 12, 'Parks', styles['styleHead2CentredLeftRightBorder'])
    sheet.write(1, 13, 'Natural', styles['styleHead2CentredRightBorder'])
    sheet.write(1, 14, 'Residual Green Space', styles['styleHead2CentredRightBorder'])
    sheet.write(1, 15,'School Grounds', styles['styleHead2CentredRightBorder'])
    sheet.col(13).width = (256 * 11)
    sheet.col(14).width = (256 * 25)
    sheet.col(15).width = (256 * 19)

    sheet.write_merge(2, 2, 0, 2, '', styles['styleNormalCentredRightBorder'])
    region_area = 'Region Area: ' + str(int(project.region.mpoly.area)) + ' m' + unichr(178)
    sheet.write_merge(3, 3, 0, 2, region_area, styles['styleNormalCentredVerticalRightBorder'])
    sheet.write(2, 3, '(m' + unichr(178) + ')', styles['styleBoldItalicCentred'])
    sheet.write(2, 4, 'All Parks', styles['styleBoldItalicCentredRightBorder'])
    sheet.write(2, 5, 'Pocket Park', styles['styleBoldItalicCentred'])
    sheet.write(2, 6, 'Small Neighbourhood Park', styles['styleBoldItalicCentred'])
    sheet.write(2, 7, 'Medium Neighbourhood Park', styles['styleBoldItalicCentred'])
    sheet.write(2, 8, 'Large Neighbourhood Park 1', styles['styleBoldItalicCentred'])
    sheet.write(2, 9, 'Large Neighbourhood Park 2', styles['styleBoldItalicCentred'])
    sheet.write(2, 10, 'District Park 1', styles['styleBoldItalicCentred'])
    sheet.write(2, 11, 'District Park 2', styles['styleBoldItalicCentred'])
    sheet.write(2, 12, 'Regional Open Space', styles['styleBoldItalicCentredRightBorder'])
    sheet.write(2, 13, '', styles['styleNormalCentredRightBorder'])
    sheet.write(2, 14, '', styles['styleNormalCentredRightBorder'])
    sheet.write(2, 15, '', styles['styleNormalCentredRightBorder'])
    for column in range(4, 13):
        sheet.col(column).width = (256 * 14)

    sheet.write(3, 3, 'Current Area', styles['styleBoldItalicCentred'])
    sheet.col(3).width = (256 * 8)

    sheet.write(4, 0, 'Age', styles['styleBoldItalicCentredBottomBorder'])
    sheet.write(4, 1, 'Current Population', styles['styleBoldItalicCentredBottomBorder'])
    sheet.write(4, 2, 'Altered Population', styles['styleBoldItalicCentredRightBottomBorder'])
    sheet.write(4, 3, 'Altered Area', styles['styleBoldItalicCentredBottomBorder'])
    sheet.col(0).width = (256 * 8)
    sheet.col(1).width = (256 * 10)
    sheet.col(2).width = (256 * 10)

    sheet.write(5, 0, 'Total', styles['styleBoldItalicCentred'])
    sheet.write(6, 0, '0-4', styles['styleBoldItalicCentred'])
    sheet.write(7, 0, '5-14', styles['styleBoldItalicCentred'])
    sheet.write(8, 0, '15-19', styles['styleBoldItalicCentred'])
    sheet.write(9, 0, '20-24', styles['styleBoldItalicCentred'])
    sheet.write(10, 0, '25-34', styles['styleBoldItalicCentred'])
    sheet.write(11, 0, '35-44', styles['styleBoldItalicCentred'])
    sheet.write(12, 0, '45-54', styles['styleBoldItalicCentred'])
    sheet.write(13, 0, '55-64', styles['styleBoldItalicCentred'])
    sheet.write(14, 0, '65-74', styles['styleBoldItalicCentred'])
    sheet.write(15, 0, '75-84', styles['styleBoldItalicCentred'])
    sheet.write(16, 0, '85+', styles['styleBoldItalicCentredBottomBorder'])

    sheet.write_merge(19, 19, 1, 3, 'Key', styles['styleBoldBorderTopLeftRightCellColourWhite'])
    sheet.write_merge(20, 20, 1, 3, 'Output metrics in m' + unichr(178) + ' / person', styles['styleNormalBorderLeftRightCellColourWhite'])
    sheet.write_merge(21, 21, 1, 3, '1m' + unichr(178) + ' = 0.0001 hectares', styles['styleNormalBorderLeftRightCellColourWhite'])
    sheet.write_merge(22, 22, 1, 3, '1m' + unichr(178) + ' = 0.00024710538147 acres', styles['styleNormalBorderLeftBottomRightCellColourWhite'])

    # Get modifiable stats
    stats = User_Statistic.objects.get(project=project)

    # if project.region.type[:2] == REGION_TYPE_CHOICE_USER_LGA_SUBURB:
    #     region_pk = project.region.type[3:]
    #     region = Region.objects.get(pk=region_pk)
    #     # Get original stats
    #     # Area stats
    #     park_stats = get_area_stats(region, 1)
    #     # Population stats
    #     sub_lga_id = region.sub_lga_id
    #     population_stats = ABS_Region_Population.objects.get(sub_lga_id=sub_lga_id)
    # else:
    # Get original stats
    # Area stats
    park_stats = get_area_stats(project)
    # Population stats
    population_stats = ABS_Region_Population.objects.get(sub_lga_id=project.region.sub_lga_id)


    # Multiplier to convert hectares to square metres
    sq_m = 10000
    original_park_stats = {
        'all_parks': park_stats[0]['region_value'] * sq_m,
        'natural': park_stats[1]['region_value'] * sq_m,
        'residual': park_stats[2]['region_value'] * sq_m,
        'school_grounds': park_stats[3]['region_value'] * sq_m,
        'pocket_parks': park_stats[5]['region_value'] * sq_m,
        'small_parks': park_stats[6]['region_value'] * sq_m,
        'medium_parks': park_stats[7]['region_value'] * sq_m,
        'large_parks_1': park_stats[8]['region_value'] * sq_m,
        'large_parks_2': park_stats[9]['region_value'] * sq_m,
        'district_parks_1': park_stats[10]['region_value'] * sq_m,
        'district_parks_2': park_stats[11]['region_value'] * sq_m,
        'regional_parks': park_stats[12]['region_value'] * sq_m
    }

    original_pop_stats = {
        'age_0_4': population_stats.age_0_4__2,
        'age_5_14': population_stats.age_5_14_2,
        'age_15_19': population_stats.age_15_192,
        'age_20_24': population_stats.age_20_242,
        'age_25_34': population_stats.age_25_342,
        'age_35_44': population_stats.age_35_442,
        'age_45_54': population_stats.age_45_542,
        'age_55_64': population_stats.age_55_642,
        'age_65_74': population_stats.age_65_742,
        'age_75_84': population_stats.age_75_842,
        'age_85_plus': population_stats.age_85ov_p,
        'total_pop': population_stats.tot_p_p
    }

    # Write original area scenario stats
    sheet.write(3, 4, original_park_stats['all_parks'], styles['styleNormalCentredVerticalRightBorder'])
    sheet.write(3, 5, original_park_stats['pocket_parks'], styles['styleNormalCentredVertical'])
    sheet.write(3, 6, original_park_stats['small_parks'], styles['styleNormalCentredVertical'])
    sheet.write(3, 7, original_park_stats['medium_parks'], styles['styleNormalCentredVertical'])
    sheet.write(3, 8, original_park_stats['large_parks_1'], styles['styleNormalCentredVertical'])
    sheet.write(3, 9, original_park_stats['large_parks_2'], styles['styleNormalCentredVertical'])
    sheet.write(3, 10, original_park_stats['district_parks_1'], styles['styleNormalCentredVertical'])
    sheet.write(3, 11, original_park_stats['district_parks_1'], styles['styleNormalCentredVertical'])
    sheet.write(3, 12, original_park_stats['regional_parks'], styles['styleNormalCentredVerticalRightBorder'])
    sheet.write(3, 13, original_park_stats['natural'], styles['styleNormalCentredVerticalRightBorder'])
    sheet.write(3, 14, original_park_stats['residual'], styles['styleNormalCentredVerticalRightBorder'])
    sheet.write(3, 15, original_park_stats['school_grounds'], styles['styleNormalCentredVerticalRightBorder'])

    # Write altered area scenario stats
    sheet.write(4, 4, stats.all_parks, styles['styleNormalCentredVerticalRightBottomBorderRedText'])
    sheet.write(4, 5, stats.pocket_park, styles['styleNormalCentredVerticalBottomBorderRedText'])
    sheet.write(4, 6, stats.small_park, styles['styleNormalCentredVerticalBottomBorderRedText'])
    sheet.write(4, 7, stats.medium_park, styles['styleNormalCentredVerticalBottomBorderRedText'])
    sheet.write(4, 8, stats.large_park_1, styles['styleNormalCentredVerticalBottomBorderRedText'])
    sheet.write(4, 9, stats.large_park_2, styles['styleNormalCentredVerticalBottomBorderRedText'])
    sheet.write(4, 10, stats.district_park_1, styles['styleNormalCentredVerticalBottomBorderRedText'])
    sheet.write(4, 11, stats.district_park_2, styles['styleNormalCentredVerticalBottomBorderRedText'])
    sheet.write(4, 12, stats.regional_space, styles['styleNormalCentredVerticalRightBottomBorderRedText'])
    sheet.write(4, 13, '', styles['styleNormalCentredVerticalRightBottomBorder'])
    sheet.write(4, 14, '', styles['styleNormalCentredVerticalRightBottomBorder'])
    sheet.write(4, 15, '', styles['styleNormalCentredVerticalRightBottomBorder'])

    # Write original population scenario stats
    sheet.write(5, 1, original_pop_stats['total_pop'], styles['styleNormalCentred'])
    sheet.write(6, 1, original_pop_stats['age_0_4'], styles['styleNormalCentred'])
    sheet.write(7, 1, original_pop_stats['age_5_14'], styles['styleNormalCentred'])
    sheet.write(8, 1, original_pop_stats['age_15_19'], styles['styleNormalCentred'])
    sheet.write(9, 1, original_pop_stats['age_20_24'], styles['styleNormalCentred'])
    sheet.write(10, 1, original_pop_stats['age_25_34'], styles['styleNormalCentred'])
    sheet.write(11, 1, original_pop_stats['age_35_44'], styles['styleNormalCentred'])
    sheet.write(12, 1, original_pop_stats['age_45_54'], styles['styleNormalCentred'])
    sheet.write(13, 1, original_pop_stats['age_55_64'], styles['styleNormalCentred'])
    sheet.write(14, 1, original_pop_stats['age_65_74'], styles['styleNormalCentred'])
    sheet.write(15, 1, original_pop_stats['age_75_84'], styles['styleNormalCentred'])
    sheet.write(16, 1, original_pop_stats['age_85_plus'], styles['styleNormalCentredBottomBorder'])

    # Write altered population scenario stats
    sheet.write(5, 2, stats.total_pop, styles['styleNormalCentredRightBorderRedText'])
    sheet.write(6, 2, stats.age_0_4, styles['styleNormalCentredRightBorderRedText'])
    sheet.write(7, 2, stats.age_5_14, styles['styleNormalCentredRightBorderRedText'])
    sheet.write(8, 2, stats.age_15_19, styles['styleNormalCentredRightBorderRedText'])
    sheet.write(9, 2, stats.age_20_24, styles['styleNormalCentredRightBorderRedText'])
    sheet.write(10, 2, stats.age_25_34, styles['styleNormalCentredRightBorderRedText'])
    sheet.write(11, 2, stats.age_35_44, styles['styleNormalCentredRightBorderRedText'])
    sheet.write(12, 2, stats.age_45_54, styles['styleNormalCentredRightBorderRedText'])
    sheet.write(13, 2, stats.age_55_64, styles['styleNormalCentredRightBorderRedText'])
    sheet.write(14, 2, stats.age_65_74, styles['styleNormalCentredRightBorderRedText'])
    sheet.write(15, 2, stats.age_75_84, styles['styleNormalCentredRightBorderRedText'])
    sheet.write(16, 2, stats.age_85_plus, styles['styleNormalCentredRightBottomBorderRedText'])

    sheet.write_merge(5, 16, 3, 3, '', styles['styleNormalCentredBottomBorder'])

    # Calculate and write metrics
    pop_stats_list = [
        stats.total_pop,
        stats.age_0_4,
        stats.age_5_14,
        stats.age_15_19,
        stats.age_20_24,
        stats.age_25_34,
        stats.age_35_44,
        stats.age_45_54,
        stats.age_55_64,
        stats.age_65_74,
        stats.age_75_84,
        stats.age_85_plus
    ]
    area_stats_list = [
        stats.all_parks,
        stats.pocket_park,
        stats.small_park,
        stats.medium_park,
        stats.large_park_1,
        stats.large_park_2,
        stats.district_park_1,
        stats.district_park_2,
        stats.regional_space
    ]

    row = 5
    for pop in pop_stats_list:
        column = 4
        for area in area_stats_list:
            if pop == 0:
                metric = 0
            else:
                metric = round(area / pop, 2)
            if column == 12 and row == 16:
                sheet.write(row, column, metric, styles['styleNormalCentredBottomRightBorder'])
            elif column == 12:
                sheet.write(row, column, metric, styles['styleNormalCentredRightBorder'])
            elif row == 16:
                sheet.write(row, column, metric, styles['styleNormalCentredBottomBorder'])
            else:
                sheet.write(row, column, metric, styles['styleNormalCentred'])
            column = column + 1
        row = row + 1

    sheet.write_merge(5, 16, 13, 15, '', styles['styleNormalCentred'])







    # sheet.col(0).width = (256 * 29)
    # sheet.row(2).set_style(xlwt.easyxf('font: height 810')) # This is the way to set a row height!

    # # Header
    # col_index = 0
    # for facility_stat_type, style_key in ACTIVITIES_COL_HEADERS:
    #     if facility_stat_type is not None:
    #         sheet.write(2, col_index, get_facility_desc(facility_stat_type), styles[style_key])
    #         sheet.col(col_index).width = (256 * 21) # Set the column cell widths
    #     col_index += 1

    # # Data Rows
    # row_index = 3
    # lower_stats = [f.lower() for f in FACILITIES_STATS_FIELDS.keys()]
    # for park_type, style_key in ACTIVITIES_ROW_HEADERS:
    #     facility_stats_qs = Facility_Statistics.objects.filter(region_pk_id=regionPK)
    #     facility_stats_qs = facility_stats_qs.filter(facility_stat__in=lower_stats,
    #         park_type=park_type)
    #     stat_lookup = {}
    #     for facility_stat in facility_stats_qs:
    #         stat_lookup[facility_stat.facility_stat] = facility_stat

    #     col_index = 0
    #     for facility_stat_type, col_header_style_key in ACTIVITIES_COL_HEADERS:
    #         if facility_stat_type is None:
    #             if park_type == STAT_TYPE_CHOICE_TOTAL_PARKS:
    #                 cell_value = get_stat_type_desc(park_type)
    #             else:
    #                 cell_value = '    ' + get_stat_type_desc(park_type)
    #             sheet.write(row_index, col_index, cell_value, styles[style_key])
    #         else:
    #             if facility_stats_qs.exists(): # Only attempt to print data if it exists
    #                 sheet.col(col_index).width = (256 * 16)
    #                 cell_value = stat_lookup[facility_stat_type.lower()].facility_count
    #                 if facility_stat_type in [
    #                             POS_FACILITY_STAT_CHOICE_ADJ_PSF,
    #                             POS_FACILITY_STAT_CHOICE_DOGS_NO_INFO_2,    # For right border at last
    #                             POS_FACILITY_CHOICE_GRASSRETIC,             # item of each category.
    #                             POS_FACILITY_CHOICE_LIGHTFEAT]:             # MS Excel aesthetics only
    #                     sheet.write(row_index, col_index, cell_value, styles['styleNormalCentredRightBorder'])
    #                 else:
    #                     sheet.write(row_index, col_index, cell_value, styles['styleNormalCentred'])
    #         col_index += 1
    #     row_index += 1

    # # Park/DSR Type Categories
    # r = 17
    # c = 0
    # sheet.write(r, c, 'Converting Between Parks and DSR Parks', styles['styleHead2'])

    # r = r + 3
    # sheet.write(r, c, 'Park Type Categories', styles['styleHead2'])
    # sheet.write(r, c + 2, 'DSR Open Space Categories', styles['styleHead2'])

    # r = r + 1
    # sheet.write(r, c, 'Pocket Park', styles['styleItalicCellColourWhiteRightTopBorder'])
    # sheet.write(r, c + 1, '0 - 0.299 ha', styles['styleNormalTopBorder'])
    # sheet.write(r, c + 2, 'Pocket Open Space^', styles['styleItalicCellColourWhiteRightTopBorder'])
    # sheet.write(r, c + 3, '0 - 0.399 ha', styles['styleNormalTopBorder'])

    # r = r + 1
    # sheet.write(r, c, 'Small Neighbourhood Park', styles['styleItalicCellColourWhiteRightTopBorder'])
    # sheet.write(r, c + 1, '0.3 ha - 0.999 ha', styles['styleNormalTopBorder'])
    # sheet.write(r, c + 2, 'Local Open Space', styles['styleItalicCellColourWhiteRightTopBorder'])
    # sheet.write(r, c + 3, '0.4 - 0.999 ha', styles['styleNormalTopBorder'])

    # r = r + 1
    # sheet.write(r, c, 'Medium Neighbourhood Park', styles['styleItalicCellColourWhiteRightTopBorder'])
    # sheet.write(r, c + 1, '1.0 ha - 1.999 ha', styles['styleNormalTopBorder'])
    # #sheet.write(r, c + 2, None, styles['styleNormalTopBorder'])
    # sheet.write(r, c + 3, None, styles['styleNormalTopBorder'])

    # r = r + 1
    # sheet.write(r, c, 'Large Neighbourhood Park 1', styles['styleItalicCellColourWhiteRightTopBorder'])
    # sheet.write(r, c + 1, '2.0 - 3.999 ha', styles['styleNormalTopBorder'])
    # #sheet.write(r, c + 2, 'Neighbourhood Open Space', styles['styleItalicRight'])
    # sheet.write_merge(r - 1, r + 1, c + 2, c + 2, 'Neighbourhood Open Space', styles['styleItalicCellColourWhiteRightTopBorder'])
    # sheet.write(r, c + 3, '1.0 - 4.999 ha', styles['styleNormal'])

    # r = r + 1
    # sheet.write(r, c, 'Large Neighbourhood Park 2', styles['styleItalicCellColourWhiteRightTopBorder'])
    # sheet.write(r, c + 1, '4.0 - 4.999 ha', styles['styleNormalTopBorder'])

    # r = r + 1
    # sheet.write(r, c, 'District Park 1', styles['styleItalicCellColourWhiteRightTopBorder'])
    # sheet.write(r, c + 1, '5.0 - 6.999 ha', styles['styleNormalTopBorder'])
    # sheet.write(r, c + 2, None, styles['styleNormalTopBorder'])
    # sheet.write(r, c + 3, None, styles['styleNormalTopBorder'])

    # r = r + 1
    # sheet.write(r, c, 'District Park 2', styles['styleItalicCellColourWhiteRightTopBorder'])
    # sheet.write(r, c + 1, '7.0 - 14.999 ha', styles['styleNormalTopBorder'])
    # sheet.write(r, c + 2, 'District Open Space' + unichr(176), styles['styleItalicRight'])
    # sheet.write(r, c + 3, '5.0 - 19.999 ha', styles['styleNormal'])

    # r = r + 1
    # sheet.write(r, c, 'Regional Park', styles['styleItalicCellColourWhiteRightTopBorder'])
    # sheet.write(r, c + 1, '> 15.0 ha', styles['styleNormalTopBorder'])

    # r = r + 1
    # sheet.write(r, c, None, styles['styleNormalTopBorder'])
    # sheet.write(r, c + 1, None, styles['styleNormalTopBorder'])
    # sheet.write(r, c + 2, 'Regional Open Space', styles['styleItalicCellColourWhiteRightTopBorder'])
    # sheet.write(r, c + 3, '> 20.0 ha', styles['styleNormalTopBorder'])

    # # Add footnotes
    # r = r + 3
    # sheet.write(r, 0, '^ Pocket Open Space category added to DSR classification framework to include these smaller sized park areas', styles['styleNormal'])
    # sheet.write(r + 1, 0, unichr(176) + ' District Open Space category expanded from 5-15 ha to 5-19.9 ha to include parks that fall between 15-20 ha', styles['styleNormal'])

    # # Publications
    # r = r + 5
    # sheet.write(r, c, 'Publications', styles['styleHead2'])
    # sheet.write(r + 1, c, 'If you make use of this dataset (or POS Tool) in your research or policy planning please cite:', styles['styleNormal'])
    # sheet.write(r + 3, c, 'Centre for the Built Environment and Health (2013). Public Open Space (POS) Geographic Information System (GIS) layer. University of Western Australia.', styles['styleNormal'])
    # sheet.write(r + 4, c,xlwt.Formula('HYPERLINK("http://researchdata.ands.org.au/public-open-space-geographic-information-system-gis-layer";"http://researchdata.ands.org.au/public-open-space-geographic-information-system-gis-layer")'),styles['styleNormal'])
    # sheet.write(r + 6, c, 'Centre for the Built Environment and Health (2013). Geo-Spatial Analytic tool for Public Open Space (POS).', styles['styleNormal'])
    # sheet.write(r + 7, c,xlwt.Formula('HYPERLINK("http://www.postool.com.au";"http://www.postool.com.au")'),styles['styleNormal'])




def get_area_stats(project_obj, *args):

    if args:
        region = project_obj
    else:
        region = project_obj.region

    park_stats = Area_Pop_Stats.objects.filter(
        region_pk=region
    ).filter(
        park_type__gte=1
    ).filter(
        region_stat='sum_area_ha'
    ).order_by(
        'park_type'
    ).values(
        'park_type', 'region_value', 'region_stat'
    )

    return park_stats

# Input number converted to string with decimal places
# If no decimal then string representation is the whole number
def floatformat(float_input):
    if float_input.is_integer():
        number_str = str(int(float_input))
    else:
        number_str = "%.2f" % float_input
        # Check if this formatted string has 00's after the decimal place
        if float(number_str).is_integer():
            number_str = floatformat(float(number_str))

    return number_str

# Check if the area list contains numerical values only
def check_area_list(list):
    for item in list:
        try:
            float(item)
        except:
            return False
    return True

# Check if the population list contains numerical values only and they are Integers
def check_population_list(list):
    for item in list:
        try:
            num = float(item)
            if num.is_integer() == False:
                return False
        except:
            return False
    return True
