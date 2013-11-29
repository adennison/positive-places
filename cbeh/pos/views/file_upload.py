from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.template import RequestContext, loader
from django import forms
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.context_processors import csrf
from django.core.files.uploadedfile import UploadedFile
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib import messages
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.gdal import DataSource, OGRGeometry, SpatialReference, CoordTransform
from django.contrib.gis.gdal.field import *
from django.conf import settings
from pos.models import *
from pos.constants import *
from pos.views import user_region
from pos.loader import pos_data_loader
from pos.statistics import build_stats
import os, shutil, tempfile, zipfile, csv

# File Upload View

# Uploaded File Keys in request.FILES[key], to get the Zip file name
POS_ZIP_FILE = 'POSs_Shapefile'
SUBURB_ZIP_FILE = 'Suburbs_Shapefile'
LGA_ZIP_FILE = 'LGAs_Shapefile'
METRO_ZIP_FILE = 'Metro_Regions_Shapefile'
CITY_ZIP_FILE = 'Cities_Shapefile'
FACILITY_CSV_FILE = 'Facilities_CSV'
AREA_POP_STATS_FILE = 'Area_Pop_Stats_CSV'
FACILITIES_STATS_FILE = 'Facilities_Stats_CSV'
SA1_ZIP_FILE = 'SA1s_Shapefile'
CATCHMENTS_ZIP_FILE = 'Catchments_Shapefile'
USER_REGION_ZIP_FILE = 'User_Region_Shapefile'
LGA_POPULATION_CSV = 'LGAs_Population_CSV'
SUBURB_POPULATION_CSV = 'Suburbs_Population_CSV'
DATA_CURRENCY_PDF = 'Data_Currency_PDF'

# SRS
SRS_1 = 'GDA94_MGA_zone_50'
SRS_2 = 'GDA_1994_MGA_Zone_50'
SRS_3 = 'GCS_WGS_1984'

# Function to open the 'upload data' web page
#@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/cbeh/pos/login/admin/')
def upload_file(request):
    c = {}
    c.update(csrf(request))
    return render_to_response('pos/data_upload/details.html',
        c,
        context_instance=RequestContext(request)
        )

# Function to handle the data upload and database population
#@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/cbeh/pos/login/admin/')
def load_data(request):
    # Call check_uploaded_files to give user feedback if no file uploaded
    feedbackFileChosen = check_uploaded_files(request)
    messageStorage = feedbackFileChosen.get_messages(request)
    if messageStorage:
        return render_to_response('pos/data_upload/details.html', locals(), context_instance=RequestContext(request))

    # Check the uploaded files have acceptable format prior to updating database
    extensionsBool = get_extensions(request)
    if extensionsBool == False:
        messages.error(request, "Please ZIP shapefiles before uploading, or check spreadsheets are CSV.")
        return render_to_response('pos/data_upload/details.html', locals(), context_instance=RequestContext(request))

    # Validate uploaded shapefiles / CSV, drop old data, load new into database
    feedbackValidation = validate_uploaded_data(request)
    messageStorage = feedbackValidation.get_messages(request)
    if feedbackValidation:
        return render_to_response('pos/data_upload/details.html', locals(), context_instance=RequestContext(request))
    else:
        messages.error(request, "There may be a problem with the data you uploaded.")
        return render_to_response('pos/data_upload/details.html', locals(), context_instance=RequestContext(request))

# Function to handle uploading the Data Currency PDF
@user_passes_test(lambda u: u.is_superuser, login_url='/cbeh/pos/login/admin/')
def load_data_currency(request):
    if request.method == 'POST':
        # Call check_uploaded_files to give user feedback if no file uploaded
        feedbackFileChosen = check_uploaded_files(request)
        messageStorage = feedbackFileChosen.get_messages(request)
        if messageStorage:
            return render_to_response('pos/data_upload/data_currency_upload.html', locals(), context_instance=RequestContext(request))

        # Check the uploaded file has acceptable format prior to updating database
        extensionsBool = get_data_currency_extension(request)
        if extensionsBool == False:
            messages.error(request, "Wrong file type. Please try again and make sure you are uploading a PDF file.")
            return render_to_response('pos/data_upload/data_currency_upload.html', locals(), context_instance=RequestContext(request))

        # Store the file
        try:
            data_currency_file = request.FILES[DATA_CURRENCY_PDF]
            media_location = settings.MEDIA_ROOT + '/data_currency_document/'
            old_file_renamed = 'old_file.pdf'
            temp_file_name = 'temp_file_name.pdf'
            file_output_name = 'POS_Tool_Data_Currency_Guide.pdf'
            default_storage.save(media_location + temp_file_name, ContentFile(data_currency_file.read()))
            # Delete the old file
            try:
                os.rename(media_location + file_output_name, media_location + old_file_renamed)
                os.rename(media_location + temp_file_name, media_location + file_output_name)
                os.remove(media_location + old_file_renamed)
                messages.success(request, "Data Currency PDF successfully saved to the server.")
            except OSError as os_error:
                messages.error(request, "There was a problem either removing the old file or renaming the uploaded file.")
                messages.error(request, os_error)
        except Exception as e:
            messages.error(request, "There was a problem saving the file to the server.")
            messages.error(request, e)
        return render_to_response('pos/data_upload/data_currency_upload.html', locals(), context_instance=RequestContext(request))

    else:
        # Just load the page ready for the user to upload the file
        return render_to_response('pos/data_upload/data_currency_upload.html', locals(), context_instance=RequestContext(request))

# Function to handle uploading the custom user region shapefile
@login_required
def upload_region(request):
    # Get PK of the user region
    pk = request.POST['pk']
    # Call check_uploaded_files to give user feedback if no file uploaded
    feedbackFileChosen = check_uploaded_files(request)
    messageStorage = feedbackFileChosen.get_messages(request)
    if messageStorage:
        return HttpResponseRedirect(reverse('upload_user_region', args=(pk,)))

    # Check the uploaded ZIP file has acceptable format prior to reading data
    extensionsBool = get_extensions(request)
    if extensionsBool == False:
        messages.error(request, "Please ZIP the shapefile before uploading.")
        return HttpResponseRedirect(reverse('upload_user_region', args=(pk,)))

    # Validate uploaded shapefile
    feedbackValidation = validate_uploaded_data(request)
    messageStorage = feedbackValidation.get_messages(request)
    if feedbackValidation:
        return HttpResponseRedirect(reverse('upload_user_region', args=(pk,)))
    else:
        messages.error(request, "There may be a problem with the data you uploaded.")
        return HttpResponseRedirect(reverse('upload_user_region', args=(pk,)))

# Unzip shapefiles, store data in temp dir, check its contents
def validate_uploaded_data(userRequest):
    tempDir = ''
    # Validate shapefiles / CSV
    if POS_ZIP_FILE in userRequest.FILES: # check for a POS upload
        posDataDict = validate_shapefile(userRequest, POS_ZIP_FILE, POS_FIELDS, "POS")
        messages = posDataDict['Messages']
        tempDir = posDataDict['TempDir']
        if tempDir != '' :
            shutil.rmtree(tempDir)
    if SUBURB_ZIP_FILE in userRequest.FILES: # check for a Suburb upload
        posDataDict = validate_shapefile(userRequest, SUBURB_ZIP_FILE, SUBURB_FIELDS, "SUB")
        messages = posDataDict['Messages']
        tempDir = posDataDict['TempDir']
        if tempDir != '' :
            shutil.rmtree(tempDir)
    if LGA_ZIP_FILE in userRequest.FILES: # check for a LGA upload
        posDataDict = validate_shapefile(userRequest, LGA_ZIP_FILE, LGA_FIELDS, "LGA")
        messages = posDataDict['Messages']
        tempDir = posDataDict['TempDir']
        if tempDir != '' :
            shutil.rmtree(tempDir)
    if METRO_ZIP_FILE in userRequest.FILES: # check for a Metro Area upload
        posDataDict = validate_shapefile(userRequest, METRO_ZIP_FILE, METRO_AREA_FIELDS, "METRO")
        messages = posDataDict['Messages']
        tempDir = posDataDict['TempDir']
        if tempDir != '' :
            shutil.rmtree(tempDir)
    if CITY_ZIP_FILE in userRequest.FILES: # check for a City upload
        posDataDict = validate_shapefile(userRequest, CITY_ZIP_FILE, CITY_FIELDS, "CITY")
        messages = posDataDict['Messages']
        tempDir = posDataDict['TempDir']
        if tempDir != '' :
            shutil.rmtree(tempDir)
    if SA1_ZIP_FILE in userRequest.FILES: # check for a SA1 upload
        posDataDict = validate_shapefile(userRequest, SA1_ZIP_FILE, SA1_ABS_STATS_FIELDS, "SA1")
        messages = posDataDict['Messages']
        tempDir = posDataDict['TempDir']
        if tempDir != '' :
            shutil.rmtree(tempDir)
    if CATCHMENTS_ZIP_FILE in userRequest.FILES: # check for a Catchments upload
        posDataDict = validate_shapefile(userRequest, CATCHMENTS_ZIP_FILE, CATCHMENTS_FIELDS, "CATCHMENTS")
        messages = posDataDict['Messages']
        tempDir = posDataDict['TempDir']
        if tempDir != '' :
            shutil.rmtree(tempDir)
    if USER_REGION_ZIP_FILE in userRequest.FILES: # check for a user region upload
        posDataDict = validate_user_region_shapefile(userRequest, USER_REGION_ZIP_FILE, "USER_REGION")
        messages = posDataDict['Messages']
        tempDir = posDataDict['TempDir']
        if tempDir != '' :
            shutil.rmtree(tempDir)
    if FACILITY_CSV_FILE in userRequest.FILES: # check for a Facility upload
        messages = validate_csv_file(userRequest, FACILITY_CSV_FILE, FACILITY_FIELDS, "FACILITY")
    if AREA_POP_STATS_FILE in userRequest.FILES: # check for an Area and population stats upload
        messages = validate_csv_file(userRequest, AREA_POP_STATS_FILE, AREA_POP_STATS_FIELDS, "AREA_POP_STATS")
    if FACILITIES_STATS_FILE in userRequest.FILES: # check for a Facilities stats upload
        messages = validate_csv_file(userRequest, FACILITIES_STATS_FILE, FACILITIES_STATS_FIELDS, "FACILITIES_STATS")
    if LGA_POPULATION_CSV in userRequest.FILES: # check for an LGAs population csv file
        messages = validate_csv_file(userRequest, LGA_POPULATION_CSV, LGA_ABS_STATS_FIELDS, "LGA_POPULATION")
    if SUBURB_POPULATION_CSV in userRequest.FILES: # check for a Suburbs population csv file
        messages = validate_csv_file(userRequest, SUBURB_POPULATION_CSV, SUBURB_ABS_STATS_FIELDS, "SUBURB_POPULATION")

    # Return messages to the load_data function
    return messages

# Validate the contents of the uploaded CSV file
def validate_csv_file(userRequest, fileKeyBinding, fieldsToCheck, type):
    # Again check this file is a CSV before continuing
    file = userRequest.FILES[fileKeyBinding]
    extension = get_extension(file.name)
    if extension == "csv":
        dataReader = csv.reader(file) # Create a CSV reader object
        fieldsList = dataReader.next() # Read the Header containing field names
        fieldsList = [fieldName.lower() for fieldName in fieldsList] # Make all fields from the Header lowercase before checking
        fieldsToCheckList = [fieldName.lower() for fieldName in fieldsToCheck] # Make the mapped fields to check lowercase before checking
        if len(fieldsList) == 1:
            messages.error(userRequest, "The " + fieldsToCheck['description'] + " is incorrectly formatted. Please fix the file before uploading again.")
        else:
            # Check field names
            countMatchFieldNames = 1
            for fieldName in fieldsList:
                if fieldName in fieldsToCheckList:
                    countMatchFieldNames = countMatchFieldNames + 1
            # Update the database table if CSV fields are all correct
            if countMatchFieldNames == len(fieldsToCheckList):
                # Drop previous database table records
                dataLoader = pos_data_loader.PosDataLoader()
                dataLoader.del_db_table_rows(type)
                # Add this table
                dataLoader.load_csv_file(file, type)
                messages.success(userRequest, fieldsToCheck['description'] + " - successfully loaded into the database.")
            else:
                # Find the field names that don't match, for user feedback
                missingFieldsList = []
                for fieldName in fieldsToCheckList:
                    if (fieldName not in fieldsList) and fieldName != 'description':
                        missingFieldsList.append(fieldName)
                if len(missingFieldsList) == 1:
                    messages.error(userRequest, "The " + fieldsToCheck['description'] + " is missing the field: " + str(missingFieldsList)[1:-1] + ". Please check the data model specifications.")
                else:
                    messages.error(userRequest, "The " + fieldsToCheck['description'] + " has missing fields: " + str(missingFieldsList)[1:-1] + ". Please check the data model specifications.")
    else:
        messages.error(userRequest, "The " + fieldsToCheck['description'] + " must be a CSV file. Please check the data model specifications.")
    return messages


# Validate the contents of the uploaded shapefile
def validate_user_region_shapefile(userRequest, fileKeyBinding, type):
    file = userRequest.FILES[fileKeyBinding]
    # try to open the zipfile
##    if zipfile.is_zipfile(file): ## Confirm it has been zipped - doesn't work in Python 2.6 (on Gaia's NS5 server)
    if check_zipfile(file) == True: ## Workaround check for Python 2.6 (on server)
        zipfileObject = zipfile.ZipFile(file, 'r') # create zipfile object
        #list = zipfileObject.namelist() # list of filenames in the zip folder
        tempDir = tempfile.mkdtemp() # make temp folder to store unZipped contents
        zipfileObject.extractall(tempDir) # extract to temp folder
        # Check if data is in subfolders and move to root temp folder
        check_for_subfolders(tempDir)
        shapeExists = check_for_shapefile(tempDir)
        # Check if there's actually a shapefile existing in the zipfile
        if shapeExists == True:
            # Use 'GDAL ogrinfo' to check contents
            try:
                ds = DataSource(tempDir + "/" + get_shapefile_name(tempDir))
            except:
                messages.error(userRequest, "Cannot open the shapefile. Please check it is not corrupted.")
                return {'TempDir' : tempDir, 'Messages' : messages}
            layer = ds[0]
            # Check it's a polygon shapefile
            if layer.geom_type == 'Polygon' or layer.geom_type == 'MultiPolygon':
                # Check the Spatial Reference System (i.e. MGA zone 50 or WGS84)
                if (layer.srs.name == SRS_1) or (layer.srs.name == SRS_2) or (layer.srs.name == SRS_3):
                    # Check how many records are in the shapefile - must be only 1
                    if layer.num_feat == 1:

                        # Get data from the request
                        pk = userRequest.POST['pk']
                        if layer.srs.name == SRS_3:
                            mgaz50 = CoordTransform(SpatialReference(4326), SpatialReference(28350))
                        else:
                            mgaz50 = SpatialReference(28350)

                        for feat in layer:
                            geom = GEOSGeometry(feat.geom.transform(mgaz50, True).wkt)
                            user_region_obj = Region.objects.get(pk=pk)

                            multiPolygon = MultiPolygon(geom)
                            multiPolygon_area_ha = multiPolygon.area / 10000

                            # Validate the geometry
                            if multiPolygon_area_ha > user_region.MAXIMUM_AREA_HA:
                                messages.error(userRequest, "Your area of %.2f hectares is greater than the maximum allowed of %.0f hectares. Please modify your region." % (multiPolygon_area_ha, user_region.MAXIMUM_AREA_HA))
                            elif geom.valid == False:
                                messages.error(userRequest, 'Your region has invalid geometry. Please modify your region before uploading again.')
                            else:
                                # Save geometry into database
                                if geom and isinstance(geom, Polygon):
                                    user_region_obj.mpoly = MultiPolygon(geom)
                                elif geom and isinstance(geom, MultiPolygon):
                                    user_region_obj.mpoly = geom
                                user_region_obj.save()
                                # Calculate the area and population statistics for the new/edited polygon
                                user_region.calculate_population(user_region_obj)
                                build_stats.areaPosStats_userRegion(pk)
                                # Calculate the Facility statistics
                                build_stats.getFacilityStats(user_region_obj)
                                # Build the initial scenario modelling area and population statistics
                                user_region.create_user_stats(user_region_obj.project, True, True)
                                messages.success(userRequest, " Region shapefile has been saved!")
                    else:
                        messages.error(userRequest, "Shapefile may contain only 1 region polygon. It currently has " + str(layer.num_feat) + ". Please try again.")
                else:
                    messages.error(userRequest, "Projection needs to be in MGA zone 50, not '" + layer.srs.name + "'. Please try again.")
            else:
                messages.error(userRequest, "Shapefile needs to be Polygon, not " + layer.geom_type + ". Please try again.")
        else:
            messages.error(userRequest, "A shapefile was not found in the ZIP file. Please try again.")
    else:
        messages.error(userRequest, "The shapefile needs to be zipped properly before uploading. Please try again.")
        tempDir = ""
    return {'TempDir' : tempDir, 'Messages' : messages}


# Validate the contents of the uploaded shapefile
def validate_shapefile(userRequest, fileKeyBinding, fieldsToCheck, type):
    file = userRequest.FILES[fileKeyBinding]
    # try to open the zipfile
##    if zipfile.is_zipfile(file): ## Confirm it has been zipped - doesn't work in Python 2.6 (on Gaia's NS5 server)
    if check_zipfile(file) == True: ## Workaround check for Python 2.6 (on server)
        zipfileObject = zipfile.ZipFile(file, 'r') # create zipfile object
        #list = zipfileObject.namelist() # list of filenames in the zip folder
        tempDir = tempfile.mkdtemp() # make temp folder to store unZipped contents
        zipfileObject.extractall(tempDir) # extract to temp folder
        # Check if data is in subfolders and move to root temp folder
        check_for_subfolders(tempDir)
        shapeExists = check_for_shapefile(tempDir)
        # Check if there's actually a shapefile existing in the zipfile
        if shapeExists == True:
            # Use 'GDAL ogrinfo' to check contents
            ds = DataSource(tempDir)
            layer = ds[0]
            # Check it's a polygon shapefile
            if layer.geom_type == 'Polygon' or layer.geom_type == 'MultiPolygon':
                # Check the Spatial Reference System (i.e. MGA zone 50)
                if (layer.srs.name == SRS_1) or (layer.srs.name == SRS_2):
                    # Check the correct field names and data types exist
                    # (convert shapefile's fieldnames to lowercase before checking)
                    fieldsList = [fieldName.lower() for fieldName in layer.fields]
                    # Check the field types are correct
                    fieldTypes = [ft for ft in layer.field_types]
                    fieldsDict = dict(zip(fieldsList, fieldTypes)) # map {field_name : field_type, ...}
                    fieldNames = fieldsToCheck.keys()
                    countMatchFieldNames = 1
                    countMatchFieldTypes = 1
                    for fieldName in fieldNames:
                        if fieldName.lower() in fieldsDict:
                            countMatchFieldNames = countMatchFieldNames + 1
                            if not fieldsToCheck[fieldName] == fieldsDict[fieldName]:
                                messages.error(userRequest, "'" + fieldName + "'" + " in the " + fieldsToCheck['description'] + " does not match the required datatype. Please check the data model specifications.")
                            else:
                                countMatchFieldTypes = countMatchFieldTypes + 1
                    # Update the database table if shapefile fields are all correct
                    if countMatchFieldNames == len(fieldsToCheck):
                        if countMatchFieldTypes == len(fieldsToCheck):
                            # Drop previous database table records
                            dataLoader = pos_data_loader.PosDataLoader()
                            dataLoader.del_db_table_rows(type)
                            # Add this table
                            dataLoader.load_shapefile(ds, type)
                            messages.success(userRequest, fieldsToCheck['description'] + " - successfully loaded into the database.")
                        else:
                            messages.error(userRequest, fieldsToCheck['description'] + " contains fields with the incorrect data type in the attribute table. Please check the data model specifications.")
                    else:
                        messages.error(userRequest, fieldsToCheck['description'] + " does not have all the necessary field names in the attribute table. Please check the data model specifications.")
                else:
                    messages.error(userRequest, fieldsToCheck['description'] + " projection needs to be in MGA zone 50, not '" + layer.srs.name + "'")
            else:
                messages.error(userRequest, fieldsToCheck['description'] + " needs to be Polygon, not " + layer.geom_type)
        else:
            messages.error(userRequest, fieldsToCheck['description'] + " is not found in the ZIP file. Please try again.")
    else:
        messages.error(userRequest, fieldsToCheck['description'] + " needs to be zipped properly before uploading.")
        tempDir = ""
    return {'TempDir' : tempDir, 'Messages' : messages}

# Check for one level of subfolders in a directory, if exists move files to root
def check_for_subfolders(dir):
    for possibleFolder in os.listdir(dir):
        possibleDir = dir + '/' + possibleFolder
        if os.path.isdir(possibleDir):
            for file in os.listdir(possibleDir):
                fileDir = possibleDir + '/' + file
                shutil.move(fileDir, dir)

# Check the uploaded files' extensions
def get_extensions(userRequest):
    extensionsOkay = True
    forCounter = 0
    countCheck = 0
    # Pull out the filenames from the request
    for filename, file in userRequest.FILES.items():
        name = file.name
        forCounter = forCounter + 1
        # Get the extension
        if "." in name:
            extension = get_extension(name)
            if not((extension == "zip") or (extension == "csv")):
                countCheck = countCheck + 1
    if countCheck > 0:
        extensionsOkay = False
    return extensionsOkay

# Check the Data Currency file is a PDF
def get_data_currency_extension(userRequest):
    extensionsOkay = False
    # Get the filename
    filename = userRequest.FILES[DATA_CURRENCY_PDF].name
    # Get the extension
    if "." in filename:
        extension = get_extension(filename)
        if extension == 'pdf':
            extensionsOkay = True
    return extensionsOkay


# Check if zipfile is valid by trying to open it. Return boolean if okay.
def check_zipfile(file):
    fileOk = True
    try:
        zipfileObject = zipfile.ZipFile(file, 'r') # create zipfile object
    except:
        fileOk = False
    return fileOk

# Get a single file's extension
def get_extension(filename):
    numCharsFullPath = len(filename)
    fullStopIndex = filename.rfind(".")
    extension = filename[fullStopIndex+1:numCharsFullPath].lower()
    return extension

# Check if a shapefile exists in the input directory. Output a boolean.
def check_for_shapefile(dir):
    shpExists = False # Set default
    for file in os.listdir(dir):
        extension = get_extension(file)
        if extension.lower() == "shp":
            shpExists = True
    return shpExists

# Get the SHP's filename inside the input directory (assumes SHP exists)
def get_shapefile_name(dir):
    for filename in os.listdir(dir):
        extension = get_extension(filename)
        if extension.lower() == "shp":
            return filename

# Check if any file has been uploaded by the user
def check_uploaded_files(userRequest):
    # Check if they typed URL '..../load_data/' instead of uploading a file first
    if userRequest.method != "POST":
        messages.error(userRequest, 'You have been redirected to the file upload page to first upload a dataset.')
    # Check they chose a file before pressing the 'Upload' button
    elif not userRequest.FILES:
        messages.error(userRequest, 'Please browse for a file to upload.')
    # Otherwise the file has been uploaded fine by the user and messages is empty
    return messages
