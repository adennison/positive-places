from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.template import RequestContext, loader
from django.conf import settings

import xlwt
#from xlwt import *
from datetime import datetime
from pos.models import *
from pos.statistics.pos_statistics import *

# For standard page load after searching for a region
def details(request, pk):
    try:
        region = Region.objects.get(pk=pk)
        # Check if this is a user region
        if (region.type == REGION_TYPE_CHOICE_USER) or (region.type == REGION_TYPE_CHOICE_USER_LGA_SUBURB):
            project = region.project
            # Check if the region is being accessed by its owner
            user = request.user
            if user.is_authenticated():
                if user != project.user:
                    raise Http404, 'User %s does not own project %s with primary key= %s' % (user.username, project.project_name, pk)
                else:
                    # Check if region has a polygon
                    if region.mpoly is None:
                        raise Http404, 'There is no polygon for the region with primary key= %s yet. Please create one before viewing any statistics.' % pk
                    else:
                        t = loader.get_template('pos/region/details.html')
                        c = RequestContext(request, {
                            'region' : region,
                            'geoserver_url': settings.GEOSERVER_URL,
                            'regionInfo' : region.get_park_stats()
                            #'regionInfo' : regionPosStats(pk)
                        })
                        return HttpResponse(t.render(c))
            else:
                raise Http404, 'User needs to log in and authenticate to view the region with primary key= %s' % pk
        else: # Load the standard LGA/Suburb region
            t = loader.get_template('pos/region/details.html')
            c = RequestContext(request, {
                'region' : region,
                'geoserver_url': settings.GEOSERVER_URL,
                'regionInfo' : region.get_park_stats()
                #'regionInfo' : regionPosStats(pk)
            })
            return HttpResponse(t.render(c))

    except Region.DoesNotExist:
        raise Http404, 'Region with pk=%s not found' % pk


# For stats file download
def download_file(request):

    if request.method == 'POST':
        if 'region_pk' in request.POST:
            region = Region.objects.get(pk=request.POST['region_pk'])
            # Get the region name to save the file name as
            fileName = region.name.replace(' ', '_') + '_' + str(date.today()) + '.xls'
            # Create the Excel file
            response = HttpResponse(mimetype='application/ms-excel')
            response['Content-Disposition'] = 'attachment; filename=%s' % fileName
            # Create the Workbook and Worksheets
            wb = xlwt.Workbook()
            metadataSheet = wb.add_sheet('Metadata')
            posSheet = wb.add_sheet('POS General Summary')
            facilitySheet = wb.add_sheet('Facility Summary')
            catchmentSheet = wb.add_sheet('Park Catchment Population')
            #dsrCatchmentSheet = wb.add_sheet('DSR Catchment Population')
            ##qualitySheet = wb.add_sheet('Attractiveness Quality')

            # Set some styles
            # Note: multiply the font text size by 20 to get the correct 'height'
            styles = {
                'styleHead1' : xlwt.easyxf('font: name Calibri, colour dark_green_ega, bold 1, height 320'),
                'styleHead1TopLeftRightBorder' : xlwt.easyxf('font: name Calibri, colour dark_green_ega, bold 1, height 320; border: top thin, left thin, right thin'),
                'styleHead2' : xlwt.easyxf('font: name Calibri, bold 1, height 240'),
                'styleHead2CentredRightBorder' : xlwt.easyxf('font: name Calibri, bold 1, height 240; alignment: horizontal center; border: right thin'),
                'styleBold' : xlwt.easyxf('font: name Calibri, bold 1'),
                'styleItalic' : xlwt.easyxf('font: name Calibri, italic 1'),
                'styleItalicRight' : xlwt.easyxf('font: name Calibri, italic 1; alignment: horizontal right'),
                'styleItalicRightWrap' : xlwt.easyxf('font: name Calibri, italic 1; alignment: horizontal right, vertical center, wrap 1;'),
                'styleItalicCellColourWhite' : xlwt.easyxf('font: name Calibri, italic 1; pattern: pattern solid, fore_colour white'),
                'styleItalicCellColourWhiteRight' : xlwt.easyxf('font: name Calibri, italic 1; pattern: pattern solid, fore_colour white; alignment: horizontal right, vertical center, wrap 1'),
                'styleItalicCellColourWhiteRightTopBorder' : xlwt.easyxf('font: name Calibri, italic 1; pattern: pattern solid, fore_colour white; alignment: horizontal right, vertical center, wrap 1;border: top thin; pattern: pattern solid, fore_colour white'),
                'styleBoldItalic' : xlwt.easyxf('font: name Calibri, bold 1, italic 1'),
                'styleBoldItalicCentred' : xlwt.easyxf('font: name Calibri, bold 1, italic 1; alignment: horizontal center, vertical center, wrap 1'),
                'styleBoldItalicCentredRightBorder' : xlwt.easyxf('font: name Calibri, bold 1, italic 1; alignment: horizontal center, vertical center, wrap 1; border: right thin'),
                'styleNormalCentred' : xlwt.easyxf('font: name Calibri; alignment: horizontal center'),
                'styleNormalLeft' : xlwt.easyxf('font: name Calibri; alignment: horizontal left'),
                'styleNormalRight' : xlwt.easyxf('font: name Calibri; alignment: horizontal right'),
                'styleNormalCentredRightBorder' : xlwt.easyxf('font: name Calibri; alignment: horizontal center; border: right thin'),
                'styleNormal' : xlwt.easyxf('font: name Calibri;'),
                'styleNormalCellColourWhite' : xlwt.easyxf('font: name Calibri; pattern: pattern solid, fore_colour white'),
                #'styleNormalCellColourRed' : xlwt.easyxf('font: name Calibri, colour Red; pattern: pattern solid, fore_colour white'),
                'styleNormalCellColourRed' : xlwt.easyxf('font: name Calibri, colour Red'),
                'styleNormalLeftBorder' : xlwt.easyxf('font: name Calibri; border: left thin; pattern: pattern solid, fore_colour white'),
                'styleNormalRightBorder' : xlwt.easyxf('font: name Calibri; border: right thin; pattern: pattern solid, fore_colour white'),
                #'styleNormalTopBorder' : xlwt.easyxf('font: name Calibri; border: top thin; pattern: pattern solid, fore_colour white'),
                'styleNormalTopBorder' : xlwt.easyxf('font: name Calibri; border: top thin'),
                'styleNormalSuperScript' : xlwt.easyxf('font: name Calibri, escapement superscript'),
             }
            style1 = xlwt.easyxf(num_format_str='D-MMM-YY')
            # Write the relevant data to each worksheet
            writeToMetadataSheet(metadataSheet, styles, request.POST['region_pk'])
            writeToPosSheet(posSheet, styles, request.POST['region_pk'])
            writeToFacilitySheet(facilitySheet, styles, request.POST['region_pk'])
            writeToCatchmentSheet(catchmentSheet, styles, request.POST['region_pk'])
            #writeToDsrCatchmentSheet(dsrCatchmentSheet, styles, request.POST['region_pk'])
            ##writeToQualitySheet(qualitySheet, styles, request.POST['region_pk'])

            wb.save(response)

            return response

# Write data to the 'Metadata' worksheet
def writeToMetadataSheet(sheet, styles, regionPK):
    # Write Suburb or LGA and its Name
    region = Region.objects.get(pk=regionPK)
    regionType = region.get_region_type_description()
    sheet.write_merge(0, 0, 0, 11, regionType + ': ' + region.name, styles['styleHead1'])

    # List of Tables
    r = 2
    sheet.write(r, 1, 'List of Tables', styles['styleHead2'])
    sheet.write(r, 2, 'Description', styles['styleHead2'])
    sheet.write(r, 7, 'Data Sources', styles['styleHead2'])

    r = r + 1
    sheet.write(r, 1, 'POS General Summary', styles['styleNormalTopBorder'])
    sheet.write(r, 2, 'Summary of count, area, percent of POS by park type, and POS', styles['styleNormalTopBorder'])
    sheet.write(r, 7, 'POS GIS Data layer, LGA boundaries, suburb boundaries', styles['styleNormalTopBorder'])

    for i in range(3,7):
        sheet.write(r,i,None,styles['styleNormalTopBorder'])

    r = r + 2
    sheet.write(r, 1, 'Facility Summary', styles['styleNormalTopBorder'])
    sheet.write(r, 2, 'Summary of facilities present by park type', styles['styleNormalTopBorder'])
    sheet.write(r, 7, 'POS Facilities Data, Park boundaries', styles['styleNormalTopBorder'])

    for i in range(3,7):
        sheet.write(r,i,None,styles['styleNormalTopBorder'])

    r = r + 2
    sheet.write(r, 1, 'Park Catchment Population', styles['styleNormalTopBorder'])
    sheet.write(r, 2, 'Summary of percent of population within designated catchment distances to park;', styles['styleNormalTopBorder'])
    sheet.write(r, 7, 'Road network (Landgate), ABS SA1 population data, LGA boundaries, suburb boundaries', styles['styleNormalTopBorder'])
    sheet.write(r + 1, 2, 'network service area (NSA) buffers were derived from points around park edges and dissolved', styles['styleNormal'])
    sheet.write(r + 2, 2, 'ABS population data from SA1 boundaries were aerially weighted with the walkable NSA buffers to derive', styles['styleNormal'])
    sheet.write(r + 3, 2, 'population figures. For further explantion please see', styles['styleNormal'])
    sheet.write(r + 4, 2, xlwt.Formula('HYPERLINK("http://www.postool.com.au/cbeh/pos/about/";"http://www.postool.com.au/cbeh/pos/about/")'),styles['styleNormal'])

    for i in range(3,7):
        sheet.write(r,i,None,styles['styleNormalTopBorder'])

    r = r + 5
    sheet.write(r, 1, 'Attractiveness/Amenity Score', styles['styleNormalTopBorder'])
    sheet.write(r, 2, 'Park attractiveness/quality information by park type', styles['styleNormalTopBorder'])
    sheet.write(r, 7, 'Under Development', styles['styleNormalTopBorder'])

    for i in range(3,7):
        sheet.write(r,i,None,styles['styleNormalTopBorder'])

    for i in range(1,8):
        sheet.write(r + 2,i,None,styles['styleNormalTopBorder'])

    # Definitions
    r = r + 4
    sheet.write(r, 1, 'Definitions', styles['styleHead2'])

    for i in range(3,7):
        sheet.write(r + 1,i,None,styles['styleNormalTopBorder'])

    r = r + 1
    sheet.write(r, 1, 'Park', styles['styleNormalTopBorder'])
    sheet.write(r, 2, 'Prepared grassed areas catering for a range of active & passive recreational activities', styles['styleNormalTopBorder'])
    sheet.write(r + 1, 2, 'Includes parks, landscaped or ornamental gardens, grassed open spaces, palying fields, ovals, reserves and other freely accessible sports surfaces', styles['styleNormalTopBorder'])

    for i in range(3,7):
        sheet.write(r + 1,i,None,styles['styleNormalTopBorder'])

    r = r + 2
    sheet.write(r, 1, 'Natural', styles['styleNormalTopBorder'])
    sheet.write(r, 2, 'Natural environments such as bushland, wetlands and coastal habitats. Areas set aside for conservation and to preserve biodiversity and wildlife habitats', styles['styleNormalTopBorder'])

    for i in range(3,7):
        sheet.write(r,i,None,styles['styleNormalTopBorder'])

    r = r + 1
    sheet.write(r, 1, 'Residual Green Space', styles['styleNormalTopBorder'])
    sheet.write(r, 2, 'Green areas of land that do not function as a park, due to their poor location, incompatible adjacent land uses', styles['styleNormalTopBorder'])
    sheet.write(r + 1, 2, '(i.e. surrounded by dual carriage ways), poor access and/or lack of infrastructure', styles['styleNormal'])

    for i in range(3,7):
        sheet.write(r,i,None,styles['styleNormalTopBorder'])

    r = r + 2
    sheet.write(r, 1, 'School Grounds+', styles['styleNormalTopBorder'])
    sheet.write(r, 2, 'Playing fields and sports surfaces / equipment adjacent to and/or owned by the school', styles['styleNormalTopBorder'])
    sheet.write(r + 1, 1, '+', styles['styleNormalRight'])
    sheet.write(r + 1, 2, 'May or may not be accessible for public use', styles['styleItalic'])

    for i in range(3,7):
        sheet.write(r,i,None,styles['styleNormalTopBorder'])

    # Park/DSR Type Categories
    r = r + 4
    c = 1
    sheet.write(r, c, 'Park Type Categories', styles['styleHead2'])
    sheet.write(r, c + 2, 'DSR Open Space Categories', styles['styleHead2'])

    r = r + 1
    sheet.write(r, c, 'Pocket Park', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 1, '0 - 0.299 ha', styles['styleNormalTopBorder'])
    sheet.write(r, c + 2, 'Pocket Open Space^', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 3, '0 - 0.399 ha', styles['styleNormalTopBorder'])

    r = r + 1
    sheet.write(r, c, 'Small Neighbourhood Park', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 1, '0.3 ha - 0.999 ha', styles['styleNormalTopBorder'])
    sheet.write(r, c + 2, 'Local Open Space', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 3, '0.4 - 0.999 ha', styles['styleNormalTopBorder'])

    r = r + 1
    sheet.write(r, c, 'Medium Neighbourhood Park', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 1, '1.0 ha - 1.999 ha', styles['styleNormalTopBorder'])
    #sheet.write(r, c + 2, None, styles['styleNormalTopBorder'])
    sheet.write(r, c + 3, None, styles['styleNormalTopBorder'])

    r = r + 1
    sheet.write(r, c, 'Large Neighbourhood Park 1', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 1, '2.0 - 3.999 ha', styles['styleNormalTopBorder'])
    #sheet.write(r, c + 2, 'Neighbourhood Open Space', styles['styleItalicRight'])
    sheet.write_merge(r - 1, r + 1, c + 2, c + 2, 'Neighbourhood Open Space', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 3, '1.0 - 4.999 ha', styles['styleNormal'])

    r = r + 1
    sheet.write(r, c, 'Large Neighbourhood Park 2', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 1, '4.0 - 4.999 ha', styles['styleNormalTopBorder'])

    r = r + 1
    sheet.write(r, c, 'District Park 1', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 1, '5.0 - 6.999 ha', styles['styleNormalTopBorder'])
    sheet.write(r, c + 2, None, styles['styleNormalTopBorder'])
    sheet.write(r, c + 3, None, styles['styleNormalTopBorder'])

    r = r + 1
    sheet.write(r, c, 'District Park 2', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 1, '7.0 - 14.999 ha', styles['styleNormalTopBorder'])
    sheet.write(r, c + 2, 'District Open Space' + unichr(176), styles['styleItalicRight'])
    sheet.write(r, c + 3, '5.0 - 19.999 ha', styles['styleNormal'])

    r = r + 1
    sheet.write(r, c, 'Regional Park', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 1, '> 15.0 ha', styles['styleNormalTopBorder'])

    r = r + 1
    sheet.write(r, c, None, styles['styleNormalTopBorder'])
    sheet.write(r, c + 1, None, styles['styleNormalTopBorder'])
    sheet.write(r, c + 2, 'Regional Open Space', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 3, '> 20.0 ha', styles['styleNormalTopBorder'])

    # Add footnotes
    r = r + 3
    sheet.write(r, 1, '^ Pocket Open Space category added to DSR classification framework to include these smaller sized park areas', styles['styleNormal'])
    sheet.write(r + 1, 1, unichr(176) + ' District Open Space category expanded from 5-15 ha to 5-19.9 ha to include parks that fall between 15-20 ha', styles['styleNormal'])

    # Facilities/Amenities
    r = r + 3
    sheet.write(r, 1, 'Facilities/Amenities', styles['styleHead2'])
    sheet.write(r + 1, 1, 'Facility information was audited for only opens classified as ''Park''. This data was collected from a', styles['styleNormal'])
    sheet.write(r + 2, 1, 'desktop audit following the Public Open Space Desktop Auditing Tool (POSDAT) protocol.', styles['styleNormal'])
    sheet.write(r + 3, 1, 'Pocket park facilities were collected using and abridged POSTOOL auditing protocol', styles['styleNormal'])
    sheet.write(r + 5, 1, 'More information can be found at:', styles['styleNormal'])
    sheet.write(r + 5, 2,xlwt.Formula('HYPERLINK("http://www.sph.uwa.edu.au/research/cbeh/projects/posdat";"http://www.sph.uwa.edu.au/research/cbeh/projects/posdat")'),styles['styleNormal'])

    # Attractiveness
    r = r + 8
    sheet.write(r, 1, 'Attractiveness/Amenity Score', styles['styleHead2'])
    sheet.write(r + 1, 1, 'Under Development', styles['styleNormal'])

    # Metadata
    r = r + 4
    sheet.write(r, 1, 'Metadata', styles['styleHead2'])
    sheet.write(r + 1, 1, 'The web tool is a project funded by the Australian National Data Service (ANDS). POS Data were collected by the Centre for the Built Environment', styles['styleNormal'])
    sheet.write(r + 2, 1, 'and Health (CBEH) at the University of Western Australia. The categories and definitions utilised are specific to research undertaken at CBEH and the Public', styles['styleNormal'])
    sheet.write(r + 3, 1, 'Open Space Desktop Auditing Tool (POSDAT)', styles['styleNormal'])

    # Legal Disclaimer
    r = r + 6
    sheet.write(r, 1, 'Legal Disclaimer', styles['styleHead2'])
    sheet.write(r + 1, 1, 'Use of the POS tool and data shall be solely at the user''s discretion and risk, and no other party shall be liable for any damages', styles['styleNormal'])
    sheet.write(r + 2, 1, 'whatsoever and howsoever caused, including where resulting from any inaccuracy, incorrectness, unsoundness and/or unreliability', styles['styleNormal'])
    sheet.write(r + 3, 1, 'in its use. The [tool] is provided without any representation or warranty of any kind, either express or implied, including but not limited', styles['styleNormal'])
    sheet.write(r + 4, 1, 'to being of satisfactory quality or fitness for a particular purpose', styles['styleNormal'])

    # Publications
    r = r + 6
    c = 1
    sheet.write(r, c, 'Publications', styles['styleHead2'])
    sheet.write(r + 1, c, 'If you make use of this dataset (or POS Tool) in your research or policy planning please cite:', styles['styleNormal'])
    sheet.write(r + 3, c, 'Centre for the Built Environment and Health (2013). Public Open Space (POS) Geographic Information System (GIS) layer. University of Western Australia.', styles['styleNormal'])
    sheet.write(r + 4, c,xlwt.Formula('HYPERLINK("http://researchdata.ands.org.au/public-open-space-pos-geographic-information-system-gis-layer";"http://researchdata.ands.org.au/public-open-space-pos-geographic-information-system-gis-layer")'),styles['styleNormal'])
    sheet.write(r + 6, c, 'Centre for the Built Environment and Health (2013). Geo-Spatial Analytic tool for Public Open Space (POS).', styles['styleNormal'])
    sheet.write(r + 7, c,xlwt.Formula('HYPERLINK("http://www.postool.com.au";"http://www.postool.com.au")'),styles['styleNormal'])

    #Set some background aesthetics
    c = 0

    sheet.col(c).width = (256 * 8)
    sheet.col(c + 1).width = (256 * 28)
    sheet.col(c + 2).width = (256 * 19)
    sheet.col(c + 3).width = (256 * 28)
    sheet.col(c + 4).width = (256 * 14)
    sheet.col(c + 5).width = (256 * 9)
    sheet.col(c + 6).width = (256 * 55)
    sheet.col(c + 7).width = (256 * 71)

# Write data to the 'POS General Summary' worksheet
def writeToPosSheet(sheet, styles, regionPK):
    # Start writing the context information to the worksheet
    region = Region.objects.get(pk=regionPK)
    regionType = region.get_region_type_description()
    sheet.write_merge(0, 0, 0, 5, regionType + ': ' + region.name, styles['styleHead1'])
    sheet.write(1, 0, 'POS Type', styles['styleHead2'])
    sheet.write(1, 1, 'Count', styles['styleBoldItalicCentred'])
    sheet.write(1, 2, 'Area (ha)', styles['styleBoldItalicCentred'])
    sheet.write(1, 3, '% Park Area', styles['styleBoldItalicCentred'])
    sheet.write(1, 4, '% Total POS Area*', styles['styleBoldItalicCentred'])
    if region.type == REGION_TYPE_CHOICE_SUBURB:
        sheet.write(1, 5, '% ' + regionType + ' Area', styles['styleBoldItalicCentred'])
    elif region.type == REGION_TYPE_CHOICE_LGA:
        sheet.write(1, 5, '% ' + REGION_TYPE_CHOICE_LGA + ' Area', styles['styleBoldItalicCentred'])
    elif (region.type == REGION_TYPE_CHOICE_USER) or (region.type == REGION_TYPE_CHOICE_USER_LGA_SUBURB):
        sheet.write(1, 5, '% Project Area', styles['styleBoldItalicCentred'])
    sheet.write(2, 0, get_stat_type_desc(STAT_TYPE_CHOICE_TOTAL_PARKS), styles['styleBold'])
    rowCounter = 3
    for parkType in PARK_TYPE_CHOICES:
        sheet.write(rowCounter, 0, '    ' + parkType[1], styles['styleItalic'])
        rowCounter = rowCounter + 1
    sheet.write(11, 0, get_stat_type_desc(POS_TYPE_C_CHOICE_NATURAL), styles['styleBold'])
    sheet.write(12, 0, get_stat_type_desc(POS_TYPE_C_CHOICE_RESIDUAL_GREEN_SPACE), styles['styleBold'])
    sheet.write(13, 0, 'Total POS*', styles['styleBoldItalic'])
    sheet.write(14, 0, get_stat_type_desc(POS_TYPE_C_CHOICE_SCHOOL_GROUNDS) + '+', styles['styleBold'])
    sheet.write(15, 0, 'Total POS* + School Grounds', styles['styleBoldItalic'])
    sheet.write(17, 0, '* POS is the public open space including categories of Parks, Natural and Residual Green Space', styles['styleNormal'])
    sheet.write(18, 0, '+ Access to School Grounds unknown/unverified', styles['styleNormal'])
    # Set the width of some of the columns
    sheet.col(0).width = (256 * 29)
    counter = 1
    while counter <= 5:
        sheet.col(counter).width = (256 * 16)
        counter = counter + 1

    # Get all the stats for this Region
    qs = Area_Pop_Stats.objects.filter(region_pk_id=regionPK)
    rowsTuple = ()

    # Add all the parks to the rows tuple
    for parkTuple in (STAT_TYPE_CHOICES):
        if parkTuple[0] <= 15 and parkTuple[1] != 'DSR POS':
            parksMap = qs.filter(park_type=parkTuple[0]).order_by('region_stat').values('region_stat', 'region_value')
            # Re-order into a list, by the printing order left to right
            parksRow = ['', '', '', '', ''] # Create 5 items only
            for statPair in parksMap:
                if statPair['region_stat'] == AREA_POP_FREQUENCY:
                    parksRow[0] = statPair['region_value']
                elif statPair['region_stat'] == AREA_POP_SUM_AREA_HA:
                    parksRow[1] = statPair['region_value']
                elif statPair['region_stat'] == AREA_POP_PERCENTPARK:
                    parksRow[2] = statPair['region_value']
                elif statPair['region_stat'] == AREA_POP_PERCENTPOS:
                    parksRow[3] = statPair['region_value']
                elif statPair['region_stat'] == AREA_POP_PERCENTSUBLGA:
                    parksRow[4] = statPair['region_value']
            rowsTuple = rowsTuple + (parksRow,)

    # Write the data
    rowCounter = 2
    for row in rowsTuple:
        colCounter = 1
        for colText in row:
            # If the stat value is '0' make it '-'
            if colText == 0:
               colText = '-'

            sheet.write(rowCounter, colCounter, colText, styles['styleNormalCentred'])

            colCounter = colCounter + 1
        rowCounter = rowCounter + 1

    # Park/DSR Type Categories
    r = 22
    c = 0
    sheet.write(r, c, 'Converting Between Parks and DSR Parks', styles['styleHead2'])

    r = r + 3
    sheet.write(r, c, 'Park Type Categories', styles['styleHead2'])
    sheet.write(r, c + 2, 'DSR Open Space Categories', styles['styleHead2'])

    r = r + 1
    sheet.write(r, c, 'Pocket Park', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 1, '0 - 0.299 ha', styles['styleNormalTopBorder'])
    sheet.write(r, c + 2, 'Pocket Open Space^', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 3, '0 - 0.399 ha', styles['styleNormalTopBorder'])

    r = r + 1
    sheet.write(r, c, 'Small Neighbourhood Park', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 1, '0.3 ha - 0.999 ha', styles['styleNormalTopBorder'])
    sheet.write(r, c + 2, 'Local Open Space', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 3, '0.4 - 0.999 ha', styles['styleNormalTopBorder'])

    r = r + 1
    sheet.write(r, c, 'Medium Neighbourhood Park', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 1, '1.0 ha - 1.999 ha', styles['styleNormalTopBorder'])
    #sheet.write(r, c + 2, None, styles['styleNormalTopBorder'])
    sheet.write(r, c + 3, None, styles['styleNormalTopBorder'])

    r = r + 1
    sheet.write(r, c, 'Large Neighbourhood Park 1', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 1, '2.0 - 3.999 ha', styles['styleNormalTopBorder'])
    sheet.write_merge(r - 1, r + 1, c + 2, c + 2, 'Neighbourhood Open Space', styles['styleItalicCellColourWhiteRightTopBorder'])
    #sheet.write(r, c + 2, 'Neighbourhood Open Space', styles['styleItalicRight'])
    sheet.write(r, c + 3, '1.0 - 4.999 ha', styles['styleNormal'])

    r = r + 1
    sheet.write(r, c, 'Large Neighbourhood Park 2', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 1, '4.0 - 4.999 ha', styles['styleNormalTopBorder'])

    r = r + 1
    sheet.write(r, c, 'District Park 1', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 1, '5.0 - 6.999 ha', styles['styleNormalTopBorder'])
    sheet.write(r, c + 2, None, styles['styleNormalTopBorder'])
    sheet.write(r, c + 3, None, styles['styleNormalTopBorder'])

    r = r + 1
    sheet.write(r, c, 'District Park 2', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 1, '7.0 - 14.999 ha', styles['styleNormalTopBorder'])
    sheet.write(r, c + 2, 'District Open Space' + unichr(176), styles['styleItalicRight'])
    sheet.write(r, c + 3, '5.0 - 19.999 ha', styles['styleNormal'])

    r = r + 1
    sheet.write(r, c, 'Regional Park', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 1, '> 15.0 ha', styles['styleNormalTopBorder'])

    r = r + 1
    sheet.write(r, c, None, styles['styleNormalTopBorder'])
    sheet.write(r, c + 1, None, styles['styleNormalTopBorder'])
    sheet.write(r, c + 2, 'Regional Open Space', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 3, '> 20.0 ha', styles['styleNormalTopBorder'])

    # Add footnotes
    r = r + 3
    sheet.write(r, 0, '^ Pocket Open Space category added to DSR classification framework to include these smaller sized park areas', styles['styleNormal'])
    sheet.write(r + 1, 0, unichr(176) + ' District Open Space category expanded from 5-15 ha to 5-19.9 ha to include parks that fall between 15-20 ha', styles['styleNormal'])

    # Publications
    r = r + 5
    sheet.write(r, c, 'Publications', styles['styleHead2'])
    sheet.write(r + 1, c, 'If you make use of this dataset (or POS Tool) in your research or policy planning please cite:', styles['styleNormal'])
    sheet.write(r + 3, c, 'Centre for the Built Environment and Health (2013). Public Open Space (POS) Geographic Information System (GIS) layer. University of Western Australia.', styles['styleNormal'])
    sheet.write(r + 4, c,xlwt.Formula('HYPERLINK("http://researchdata.ands.org.au/public-open-space-pos-geographic-information-system-gis-layer";"http://researchdata.ands.org.au/public-open-space-pos-geographic-information-system-gis-layer")'),styles['styleNormal'])
    sheet.write(r + 6, c, 'Centre for the Built Environment and Health (2013). Geo-Spatial Analytic tool for Public Open Space (POS).', styles['styleNormal'])
    sheet.write(r + 7, c,xlwt.Formula('HYPERLINK("http://www.postool.com.au";"http://www.postool.com.au")'),styles['styleNormal'])

    # Set some background aesthetics
    sheet.col(2).width = (256 * 25)

# For writing to Facility Summary sheet
ACTIVITIES_COL_HEADERS = [
    (None, None),
    (POS_FACILITY_CHOICE_TENNIS, 'styleBoldItalicCentred',),
    (POS_FACILITY_CHOICE_SOCCER, 'styleBoldItalicCentred',),
    (POS_FACILITY_CHOICE_FOOTBALL, 'styleBoldItalicCentred',),
    (POS_FACILITY_CHOICE_NETCOURT, 'styleBoldItalicCentred',),
    (POS_FACILITY_CHOICE_CRICKET , 'styleBoldItalicCentred',),
    (POS_FACILITY_CHOICE_BASEBALL , 'styleBoldItalicCentred',),
    (POS_FACILITY_CHOICE_FITNESS, 'styleBoldItalicCentred',),
    (POS_FACILITY_CHOICE_BASKETHOOP, 'styleBoldItalicCentred',),
    (POS_FACILITY_CHOICE_HOCKEY, 'styleBoldItalicCentred',),
    (POS_FACILITY_CHOICE_ATHLETICS, 'styleBoldItalicCentred',),
    (POS_FACILITY_CHOICE_RUGBY, 'styleBoldItalicCentred',),
    (POS_FACILITY_CHOICE_SKATEBMX, 'styleBoldItalicCentred',),
    (POS_FACILITY_CHOICE_PLAYGROUND, 'styleBoldItalicCentred',),
    (POS_FACILITY_STAT_CHOICE_PLAYSHADE_FULL_2, 'styleBoldItalicCentred',),
    (POS_FACILITY_STAT_CHOICE_PLAYSHADE_PARTIAL_1, 'styleBoldItalicCentred',),
    (POS_FACILITY_STAT_CHOICE_PLAYFENCE_YES_1, 'styleBoldItalicCentred',),
    (POS_FACILITY_STAT_CHOICE_PLAYFENCE_NO_0, 'styleBoldItalicCentred',),
    (POS_FACILITY_STAT_CHOICE_ADJ_PSF, 'styleBoldItalicCentredRightBorder',),
    (POS_FACILITY_STAT_CHOICE_DOGS_YES_1, 'styleBoldItalicCentred',),
    (POS_FACILITY_STAT_CHOICE_DOGS_NO_0, 'styleBoldItalicCentred',),
    (POS_FACILITY_STAT_CHOICE_DOGS_NO_INFO_2, 'styleBoldItalicCentredRightBorder',),
    (POS_FACILITY_CHOICE_LAKEPOND, 'styleBoldItalicCentred',),
    (POS_FACILITY_CHOICE_FOUNTAIN, 'styleBoldItalicCentred',),
    (POS_FACILITY_CHOICE_STREAM, 'styleBoldItalicCentred',),
    (POS_FACILITY_CHOICE_WETLAND, 'styleBoldItalicCentred',),
    (POS_FACILITY_CHOICE_WILDLIFE, 'styleBoldItalicCentred',),
    (POS_FACILITY_CHOICE_GARDENS, 'styleBoldItalicCentred',),
    (POS_FACILITY_STAT_CHOICE_TREES_YES_MORE_100_3, 'styleBoldItalicCentred',),
    (POS_FACILITY_STAT_CHOICE_TREES_YES_50_100_2, 'styleBoldItalicCentred',),
    (POS_FACILITY_STAT_CHOICE_TREES_YES_1_50_1, 'styleBoldItalicCentred',),
    (POS_FACILITY_STAT_CHOICE_TREES_NO_0, 'styleBoldItalicCentred',),
    (POS_FACILITY_CHOICE_GRASSRETIC, 'styleBoldItalicCentredRightBorder',),
    (POS_FACILITY_CHOICE_PATHS, 'styleBoldItalicCentred',),
    (POS_FACILITY_STAT_CHOICE_PATHSHADE_NO_0, 'styleBoldItalicCentred',),
    (POS_FACILITY_STAT_CHOICE_PATHSHADE_YES_POOR_1, 'styleBoldItalicCentred',),
    (POS_FACILITY_STAT_CHOICE_PATHSHADE_YES_MEDIUM_2, 'styleBoldItalicCentred',),
    (POS_FACILITY_STAT_CHOICE_PATHSHADE_YES_GOOD_3, 'styleBoldItalicCentred',),
    #(POS_FACILITY_CHOICE_PATHSHADE, 'styleBoldItalicCentred',),
    # (POS_FACILITY_CHOICE_PATHSHADE0, 'styleBoldItalicCentred',),
    # (POS_FACILITY_CHOICE_PATHSHADE1, 'styleBoldItalicCentred',),
    # (POS_FACILITY_CHOICE_PATHSHADE2, 'styleBoldItalicCentred',),
    # (POS_FACILITY_CHOICE_PATHSHADE3, 'styleBoldItalicCentred',),
    (POS_FACILITY_CHOICE_BBQ, 'styleBoldItalicCentred',),
    (POS_FACILITY_CHOICE_SEAT, 'styleBoldItalicCentred',),
    (POS_FACILITY_CHOICE_PICNIC, 'styleBoldItalicCentred',),
    (POS_FACILITY_CHOICE_KIOSK, 'styleBoldItalicCentred',),
    (POS_FACILITY_CHOICE_TOILETS, 'styleBoldItalicCentred',),
    (POS_FACILITY_CHOICE_ART, 'styleBoldItalicCentred',),
    (POS_FACILITY_CHOICE_CARPARK, 'styleBoldItalicCentred',),
    (POS_FACILITY_CHOICE_LIGHTING, 'styleBoldItalicCentred',),
    (POS_FACILITY_CHOICE_LIGHTFEAT, 'styleBoldItalicCentredRightBorder',),
]

ACTIVITIES_ROW_HEADERS = [
    (STAT_TYPE_CHOICE_TOTAL_PARKS, 'styleBold',),
    (PARK_TYPE_CHOICE_POCKET, 'styleItalic',),
    (PARK_TYPE_CHOICE_SMALL, 'styleItalic',),
    (PARK_TYPE_CHOICE_MEDIUM, 'styleItalic'),
    (PARK_TYPE_CHOICE_LARGE_1, 'styleItalic',),
    (PARK_TYPE_CHOICE_LARGE_2, 'styleItalic',),
    (PARK_TYPE_CHOICE_DISTRICT_1, 'styleItalic',),
    (PARK_TYPE_CHOICE_DISTRICT_2, 'styleItalic',),
    (PARK_TYPE_CHOICE_REGIONAL, 'styleItalic',),
]

# Write data to the 'Facility Summary' worksheet
def writeToFacilitySheet(sheet, styles, regionPK):
    # Start writing the context information to the worksheet
    region = Region.objects.get(pk=regionPK)
    regionType = region.get_region_type_description()

    sheet.write_merge(0, 0, 0, 43, regionType + ': ' + region.name, styles['styleHead1'])
    sheet.write_merge(1, 1, 1, 18, 'Activities', styles['styleHead2CentredRightBorder'])
    sheet.write_merge(1, 1, 19, 21, 'Pets', styles['styleHead2CentredRightBorder'])
    sheet.write_merge(1, 1, 22, 32, 'Nature', styles['styleHead2CentredRightBorder'])
    sheet.write_merge(1, 1, 33, 46, 'Facilities', styles['styleHead2CentredRightBorder'])
    sheet.write(2, 0, 'POS Type', styles['styleHead2'])

    sheet.col(0).width = (256 * 29)
    sheet.row(2).set_style(xlwt.easyxf('font: height 810')) # This is the way to set a row height!

    # Header
    col_index = 0
    for facility_stat_type, style_key in ACTIVITIES_COL_HEADERS:
        if facility_stat_type is not None:
            sheet.write(2, col_index, get_facility_desc(facility_stat_type), styles[style_key])
            sheet.col(col_index).width = (256 * 21) # Set the column cell widths
        col_index += 1

    # Data Rows
    row_index = 3
    lower_stats = [f.lower() for f in FACILITIES_STATS_FIELDS.keys()]
    for park_type, style_key in ACTIVITIES_ROW_HEADERS:
        facility_stats_qs = Facility_Statistics.objects.filter(region_pk_id=regionPK)
        facility_stats_qs = facility_stats_qs.filter(facility_stat__in=lower_stats,
            park_type=park_type)
        stat_lookup = {}
        for facility_stat in facility_stats_qs:
            stat_lookup[facility_stat.facility_stat] = facility_stat

        col_index = 0
        for facility_stat_type, col_header_style_key in ACTIVITIES_COL_HEADERS:
            if facility_stat_type is None:
                if park_type == STAT_TYPE_CHOICE_TOTAL_PARKS:
                    cell_value = get_stat_type_desc(park_type)
                else:
                    cell_value = '    ' + get_stat_type_desc(park_type)
                sheet.write(row_index, col_index, cell_value, styles[style_key])
            else:
                if facility_stats_qs.exists(): # Only attempt to print data if it exists
                    sheet.col(col_index).width = (256 * 16)
                    cell_value = stat_lookup[facility_stat_type.lower()].facility_count
                    if facility_stat_type in [
                                POS_FACILITY_STAT_CHOICE_ADJ_PSF,
                                POS_FACILITY_STAT_CHOICE_DOGS_NO_INFO_2,    # For right border at last
                                POS_FACILITY_CHOICE_GRASSRETIC,             # item of each category.
                                POS_FACILITY_CHOICE_LIGHTFEAT]:             # MS Excel aesthetics only
                        sheet.write(row_index, col_index, cell_value, styles['styleNormalCentredRightBorder'])
                    else:
                        sheet.write(row_index, col_index, cell_value, styles['styleNormalCentred'])
            col_index += 1
        row_index += 1

    # Park/DSR Type Categories
    r = 17
    c = 0
    sheet.write(r, c, 'Converting Between Parks and DSR Parks', styles['styleHead2'])

    r = r + 3
    sheet.write(r, c, 'Park Type Categories', styles['styleHead2'])
    sheet.write(r, c + 2, 'DSR Open Space Categories', styles['styleHead2'])

    r = r + 1
    sheet.write(r, c, 'Pocket Park', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 1, '0 - 0.299 ha', styles['styleNormalTopBorder'])
    sheet.write(r, c + 2, 'Pocket Open Space^', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 3, '0 - 0.399 ha', styles['styleNormalTopBorder'])

    r = r + 1
    sheet.write(r, c, 'Small Neighbourhood Park', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 1, '0.3 ha - 0.999 ha', styles['styleNormalTopBorder'])
    sheet.write(r, c + 2, 'Local Open Space', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 3, '0.4 - 0.999 ha', styles['styleNormalTopBorder'])

    r = r + 1
    sheet.write(r, c, 'Medium Neighbourhood Park', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 1, '1.0 ha - 1.999 ha', styles['styleNormalTopBorder'])
    #sheet.write(r, c + 2, None, styles['styleNormalTopBorder'])
    sheet.write(r, c + 3, None, styles['styleNormalTopBorder'])

    r = r + 1
    sheet.write(r, c, 'Large Neighbourhood Park 1', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 1, '2.0 - 3.999 ha', styles['styleNormalTopBorder'])
    #sheet.write(r, c + 2, 'Neighbourhood Open Space', styles['styleItalicRight'])
    sheet.write_merge(r - 1, r + 1, c + 2, c + 2, 'Neighbourhood Open Space', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 3, '1.0 - 4.999 ha', styles['styleNormal'])

    r = r + 1
    sheet.write(r, c, 'Large Neighbourhood Park 2', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 1, '4.0 - 4.999 ha', styles['styleNormalTopBorder'])

    r = r + 1
    sheet.write(r, c, 'District Park 1', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 1, '5.0 - 6.999 ha', styles['styleNormalTopBorder'])
    sheet.write(r, c + 2, None, styles['styleNormalTopBorder'])
    sheet.write(r, c + 3, None, styles['styleNormalTopBorder'])

    r = r + 1
    sheet.write(r, c, 'District Park 2', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 1, '7.0 - 14.999 ha', styles['styleNormalTopBorder'])
    sheet.write(r, c + 2, 'District Open Space' + unichr(176), styles['styleItalicRight'])
    sheet.write(r, c + 3, '5.0 - 19.999 ha', styles['styleNormal'])

    r = r + 1
    sheet.write(r, c, 'Regional Park', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 1, '> 15.0 ha', styles['styleNormalTopBorder'])

    r = r + 1
    sheet.write(r, c, None, styles['styleNormalTopBorder'])
    sheet.write(r, c + 1, None, styles['styleNormalTopBorder'])
    sheet.write(r, c + 2, 'Regional Open Space', styles['styleItalicCellColourWhiteRightTopBorder'])
    sheet.write(r, c + 3, '> 20.0 ha', styles['styleNormalTopBorder'])

    # Add footnotes
    r = r + 3
    sheet.write(r, 0, '^ Pocket Open Space category added to DSR classification framework to include these smaller sized park areas', styles['styleNormal'])
    sheet.write(r + 1, 0, unichr(176) + ' District Open Space category expanded from 5-15 ha to 5-19.9 ha to include parks that fall between 15-20 ha', styles['styleNormal'])

    # Publications
    r = r + 5
    sheet.write(r, c, 'Publications', styles['styleHead2'])
    sheet.write(r + 1, c, 'If you make use of this dataset (or POS Tool) in your research or policy planning please cite:', styles['styleNormal'])
    sheet.write(r + 3, c, 'Centre for the Built Environment and Health (2013). Public Open Space (POS) Geographic Information System (GIS) layer. University of Western Australia.', styles['styleNormal'])
    sheet.write(r + 4, c,xlwt.Formula('HYPERLINK("http://researchdata.ands.org.au/public-open-space-geographic-information-system-gis-layer";"http://researchdata.ands.org.au/public-open-space-geographic-information-system-gis-layer")'),styles['styleNormal'])
    sheet.write(r + 6, c, 'Centre for the Built Environment and Health (2013). Geo-Spatial Analytic tool for Public Open Space (POS).', styles['styleNormal'])
    sheet.write(r + 7, c,xlwt.Formula('HYPERLINK("http://www.postool.com.au";"http://www.postool.com.au")'),styles['styleNormal'])

# Write data to the 'Park Catchment Population' worksheet
def writeToCatchmentSheet(sheet, styles, regionPK):
    # Start writing the context information to the worksheet
    region = Region.objects.get(pk=regionPK)
    regionType = region.get_region_type_description()
    sheet.write_merge(0, 0, 0, 12, regionType + ': ' + region.name, styles['styleHead1'])

    # Write the park type columns
    r = 1
    c = 0

    sheet.write(r, c + 1, 'Catchment Distance', styles['styleBoldItalicCentred'])
    sheet.write(r, c + 2, 'Total Catchment Population', styles['styleBoldItalicCentred'])
    sheet.write(r, c + 3, '0-4', styles['styleBoldItalicCentred'])
    sheet.write(r, c + 4, '5-14', styles['styleBoldItalicCentred'])
    sheet.write(r, c + 5, '15-19', styles['styleBoldItalicCentred'])
    sheet.write(r, c + 6, '20-24', styles['styleBoldItalicCentred'])
    sheet.write(r, c + 7, '25-34', styles['styleBoldItalicCentred'])
    sheet.write(r, c + 8, '35-44', styles['styleBoldItalicCentred'])
    sheet.write(r, c + 9, '45-54', styles['styleBoldItalicCentred'])
    sheet.write(r, c + 10, '55-64', styles['styleBoldItalicCentred'])
    sheet.write(r, c + 11, '65-74', styles['styleBoldItalicCentred'])
    sheet.write(r, c + 12, '75-84', styles['styleBoldItalicCentred'])
    sheet.write(r, c + 13, '85+', styles['styleBoldItalicCentred'])
    sheet.write(r + 1, c, 'POS Type', styles['styleHead2'])

    # Write the DSR type columns
    r = 15
    c = 0

    sheet.write(r, c + 1, 'Catchment Distance', styles['styleBoldItalicCentred'])
    sheet.write(r, c + 2, 'Total Catchment Population', styles['styleBoldItalicCentred'])
    sheet.write(r, c + 3, '0-4', styles['styleBoldItalicCentred'])
    sheet.write(r, c + 4, '5-14', styles['styleBoldItalicCentred'])
    sheet.write(r, c + 5, '15-19', styles['styleBoldItalicCentred'])
    sheet.write(r, c + 6, '20-24', styles['styleBoldItalicCentred'])
    sheet.write(r, c + 7, '25-34', styles['styleBoldItalicCentred'])
    sheet.write(r, c + 8, '35-44', styles['styleBoldItalicCentred'])
    sheet.write(r, c + 9, '45-54', styles['styleBoldItalicCentred'])
    sheet.write(r, c + 10, '55-64', styles['styleBoldItalicCentred'])
    sheet.write(r, c + 11, '65-74', styles['styleBoldItalicCentred'])
    sheet.write(r, c + 12, '75-84', styles['styleBoldItalicCentred'])
    sheet.write(r, c + 13, '85+', styles['styleBoldItalicCentred'])
    sheet.write(r + 1, c, 'POS Type', styles['styleHead2'])

    # Write the park types
    colCounter = 2
    while colCounter <= 13:
        sheet.write(2, colCounter, '%', styles['styleNormalCentred'])
        sheet.col(colCounter).width = (256 * 6) # Set width
        colCounter = colCounter + 1
    sheet.write(3, 0, get_stat_type_desc(STAT_TYPE_CHOICE_TOTAL_PARKS), styles['styleBold'])
    sheet.write(3, 1, 'Any', styles['styleNormalCentred'])
    rowCounter = 4
    for parkType in PARK_TYPE_CHOICES:
        sheet.write(rowCounter, 0, '    ' + parkType[1], styles['styleItalic'])
        rowCounter = rowCounter + 1

    # Write the park type distances
    qd = Park_Type_Distance.objects.all()
    rowCounter = 4
    for parkDistance in qd:
        sheet.write(rowCounter, 1, str(parkDistance.type_distance) + 'm', styles['styleNormalCentred'])
        rowCounter = rowCounter + 1

    # Write the dsr types
    colCounter = 2
    while colCounter <= 13:
        sheet.write(16, colCounter, '%', styles['styleNormalCentred'])
        sheet.col(colCounter).width = (256 * 6) # Set width
        colCounter = colCounter + 1
    #sheet.write(17, 0, get_stat_type_desc(STAT_TYPE_CHOICE_TOTAL_DSR), styles['styleBold'])
    sheet.write(17, 0, 'DSR POS', styles['styleBold'])
    sheet.write(17, 1, 'Any', styles['styleNormalCentred'])
    rowCounter = 18
    for dsrType in DSR_TYPE_CHOICES:
        if not (dsrType[1] == 'None'):
            if dsrType[0] == DSR_TYPE_CHOICE_POCKET:
                sheet.write(rowCounter, 0, '    ' + dsrType[1] + '^', styles['styleItalic'])
            elif dsrType[0] == DSR_TYPE_CHOICE_DISTRICT:
                sheet.write(rowCounter, 0, '    ' + dsrType[1] + unichr(176), styles['styleItalic'])
            else:
                sheet.write(rowCounter, 0, '    ' + dsrType[1], styles['styleItalic'])
            rowCounter = rowCounter + 1

    # Write the dsr type distances
    qd = DSR_Type_Distance.objects.all()
    rowCounter = 18
    for parkDistance in qd:
        if not (parkDistance.dsr_type == 1):
            sheet.write(rowCounter, 1, str(parkDistance.type_distance) + 'm', styles['styleNormalCentred'])
            rowCounter = rowCounter + 1

    # Set the width of some of the columns
    sheet.col(0).width = (256 * 29)
    sheet.col(1).width = (256 * 19)
    sheet.col(2).width = (256 * 24)
    for i in range(3,14):
        sheet.col(i).width = (256 * 8)

    # Get all the stats for this Region
    qs = Area_Pop_Stats.objects.filter(region_pk_id=regionPK)
    rowsTuple = ()

    # Add all the parks to the rows tuple
    for parkTuple in ((STAT_TYPE_CHOICES[0],) + PARK_TYPE_CHOICES):
        parksMap = qs.filter(park_type=parkTuple[0]).order_by('region_stat').values('region_stat', 'region_value')
        # Re-order into a list, by the printing order left to right
        parksRow = ['', '', '', '', '', '', '', '', '', '', '', ''] # Create 12 items only
        roundBy = 2
        for statPair in parksMap:
            if statPair['region_stat'] == AREA_POP_SUM_PERCENTTOTALPOP:
                parksRow[0] = round(statPair['region_value'],roundBy)
            elif statPair['region_stat'] == AREA_POP_SUM_PERCENTPOP0TO4:
                parksRow[1] = round(statPair['region_value'],roundBy)
            elif statPair['region_stat'] == AREA_POP_SUM_PERCENTPOP5TO14:
                parksRow[2] = round(statPair['region_value'],roundBy)
            elif statPair['region_stat'] == AREA_POP_SUM_PERCENTPOP15TO19:
                parksRow[3] = round(statPair['region_value'],roundBy)
            elif statPair['region_stat'] == AREA_POP_SUM_PERCENTPOP20TO24:
                parksRow[4] = round(statPair['region_value'],roundBy)
            elif statPair['region_stat'] == AREA_POP_SUM_PERCENTPOP25TO34:
                parksRow[5] = round(statPair['region_value'],roundBy)
            elif statPair['region_stat'] == AREA_POP_SUM_PERCENTPOP35TO44:
                parksRow[6] = round(statPair['region_value'],roundBy)
            elif statPair['region_stat'] == AREA_POP_SUM_PERCENTPOP45TO54:
                parksRow[7] = round(statPair['region_value'],roundBy)
            elif statPair['region_stat'] == AREA_POP_SUM_PERCENTPOP55TO64:
                parksRow[8] = round(statPair['region_value'],roundBy)
            elif statPair['region_stat'] == AREA_POP_SUM_PERCENTPOP65TO74:
                parksRow[9] = round(statPair['region_value'],roundBy)
            elif statPair['region_stat'] == AREA_POP_SUM_PERCENTPOP75TO84:
                parksRow[10] = round(statPair['region_value'],roundBy)
            elif statPair['region_stat'] == AREA_POP_SUM_PERCENTPOPOVER85:
                parksRow[11] = round(statPair['region_value'],roundBy)
        rowsTuple = rowsTuple + (parksRow,)

    # Write the data
    rowCounter = 3
    for row in rowsTuple:
        colCounter = 2
        for colText in row:
            sheet.write(rowCounter, colCounter, colText, styles['styleNormalCentred'])
            colCounter = colCounter + 1
        rowCounter = rowCounter + 1

    # Add all the DSRs to the rows tuple
    rowsTuple = ()
    for parkTuple in ((STAT_TYPE_CHOICES[0],) + DSR_TYPE_CHOICES):
        dsrMap = qs.filter(dsr_type=parkTuple[0]).order_by('region_stat').values('region_stat', 'region_value')
         # Re-order into a list, by the printing order left to right
        parksRow = ['', '', '', '', '', '', '', '', '', '', '', ''] # Create 12 items only
        roundBy = 2
        for statPair in dsrMap:
            if statPair['region_stat'] == AREA_POP_SUM_PERCENTTOTALPOPDSR:
                parksRow[0] = round(statPair['region_value'],roundBy)
            elif statPair['region_stat'] == AREA_POP_SUM_PERCENTPOP0TO4DSR:
                parksRow[1] = round(statPair['region_value'],roundBy)
            elif statPair['region_stat'] == AREA_POP_SUM_PERCENTPOP5TO14DSR:
                parksRow[2] = round(statPair['region_value'],roundBy)
            elif statPair['region_stat'] == AREA_POP_SUM_PERCENTPOP15TO19DSR:
                parksRow[3] = round(statPair['region_value'],roundBy)
            elif statPair['region_stat'] == AREA_POP_SUM_PERCENTPOP20TO24DSR:
                parksRow[4] = round(statPair['region_value'],roundBy)
            elif statPair['region_stat'] == AREA_POP_SUM_PERCENTPOP25TO34DSR:
                parksRow[5] = round(statPair['region_value'],roundBy)
            elif statPair['region_stat'] == AREA_POP_SUM_PERCENTPOP35TO44DSR:
                parksRow[6] = round(statPair['region_value'],roundBy)
            elif statPair['region_stat'] == AREA_POP_SUM_PERCENTPOP45TO54DSR:
                parksRow[7] = round(statPair['region_value'],roundBy)
            elif statPair['region_stat'] == AREA_POP_SUM_PERCENTPOP55TO64DSR:
                parksRow[8] = round(statPair['region_value'],roundBy)
            elif statPair['region_stat'] == AREA_POP_SUM_PERCENTPOP65TO74DSR:
                parksRow[9] = round(statPair['region_value'],roundBy)
            elif statPair['region_stat'] == AREA_POP_SUM_PERCENTPOP75TO84DSR:
                parksRow[10] = round(statPair['region_value'],roundBy)
            elif statPair['region_stat'] == AREA_POP_SUM_PERCENTPOPOVER85DSR:
                parksRow[11] = round(statPair['region_value'],roundBy)
        rowsTuple = rowsTuple + (parksRow,)

    # Write the data
    rowCounter = 17
    for row in rowsTuple:
        colCounter = 2
        for colText in row:
            sheet.write(rowCounter, colCounter, colText, styles['styleNormalCentred'])
            colCounter = colCounter + 1
        rowCounter = rowCounter + 1

    # sheet.write(24, 0, '* additional category added to include all parks < 0.4ha', styles['styleNormal'])

    # Add footnotes
    sheet.write(26, 0, '^ Pocket Open Space category added to DSR classification framework to include these smaller sized park areas', styles['styleNormal'])
    sheet.write(27, 0, unichr(176) + ' District Open Space category expanded from 5-15 ha to 5-19.9 ha to include parks that fall between 15-20 ha', styles['styleNormal'])

    # Publications
    r = 29
    sheet.write(r, c, 'Publications', styles['styleHead2'])
    sheet.write(r + 1, c, 'If you make use of this dataset (or POS Tool) in your research or policy planning please cite:', styles['styleNormal'])
    sheet.write(r + 3, c, 'Centre for the Built Environment and Health (2013). Public Open Space (POS) Geographic Information System (GIS) layer. University of Western Australia.', styles['styleNormal'])
    sheet.write(r + 4, c,xlwt.Formula('HYPERLINK("http://researchdata.ands.org.au/public-open-space-pos-geographic-information-system-gis-layer";"http://researchdata.ands.org.au/public-open-space-pos-geographic-information-system-gis-layer")'),styles['styleNormal'])
    sheet.write(r + 6, c, 'Centre for the Built Environment and Health (2013). Geo-Spatial Analytic tool for Public Open Space (POS).', styles['styleNormal'])
    sheet.write(r + 7, c,xlwt.Formula('HYPERLINK("http://www.postool.com.au";"http://www.postool.com.au")'),styles['styleNormal'])

# Write data to the 'DSR Catchment Population' worksheet
# def writeToDsrCatchmentSheet(sheet, styles, regionPK):
#     # Start writing the context information to the worksheet
#     region = Region.objects.get(pk=regionPK)
#     regionType = region.get_region_type_description()
#     sheet.write_merge(0, 0, 0, 12, regionType + ': ' + region.name, styles['styleHead1'])
#     sheet.write(2, 0, 'POS Type', styles['styleHead2'])
#     sheet.write(1, 2, 'Total Catchment Population', styles['styleBoldItalicCentred'])
#     sheet.write(1, 3, '0-4', styles['styleBoldItalicCentred'])
#     sheet.write(1, 4, '5-14', styles['styleBoldItalicCentred'])
#     sheet.write(1, 5, '15-19', styles['styleBoldItalicCentred'])
#     sheet.write(1, 6, '20-24', styles['styleBoldItalicCentred'])
#     sheet.write(1, 7, '25-34', styles['styleBoldItalicCentred'])
#     sheet.write(1, 8, '35-44', styles['styleBoldItalicCentred'])
#     sheet.write(1, 9, '45-54', styles['styleBoldItalicCentred'])
#     sheet.write(1, 10, '55-64', styles['styleBoldItalicCentred'])
#     sheet.write(1, 11, '65-74', styles['styleBoldItalicCentred'])
#     sheet.write(1, 12, '75-84', styles['styleBoldItalicCentred'])
#     sheet.write(1, 13, '85+', styles['styleBoldItalicCentred'])

# # Write data to the 'Attractiveness Quality' worksheet
# def writeToQualitySheet(sheet, styles, regionPK):
#     # Start writing the context information to the worksheet
#     region = Region.objects.get(pk=regionPK)
#     regionType = region.get_region_type_description()

#     sheet.write_merge(0, 0, 0, 5, regionType + ': ' + region.name, styles['styleHead1'])
#     ## No info yet in the quality score fields in POS table - left for Phase 2

# Put in Park Type code as integer, returns Park Type Description
def get_stat_type_desc(code):
    for tuple in STAT_TYPE_CHOICES:
        if tuple[0] == code:
            return tuple[1]

# Put in a code, and return True if it exists is in the POS_TYPE_C_CHOICES tuple
def check_pos_type_code(code):
    for tuple in POS_TYPE_C_CHOICES:
        if tuple[0] == code:
            return True

# Put in the abbreviated facility statistic name, return the full description
def get_facility_desc(desc):
    for tuple in (POS_FACILITY_CHOICES + POS_FACILITY_STAT_CHOICES):
        if tuple[0] == desc:
            return tuple[1]
