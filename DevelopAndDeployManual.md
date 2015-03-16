## Introduction ##

The install guide is tested for Ubuntu 13.04

## Install and Setup Django ##
<ol>
<li>Checkout the POS source code from Google Code<br>
<pre><code>svn co svn:<br>
</code></pre>
</li>
<li>Update setting.py in with the settings appropriate to your installation, after completing the installation of GeoServer update the GEOSERVER_URL variable with the url for your WMS service.<br>
</li>
<li>Create a new bash script in the "bin/env" directory of the checkout. The script should be named "environment_hostname.sh" where hostname is the name of your machine. You can find out the name of your machine by running<br>
<pre><code>echo $HOSTNAME<br>
</code></pre>
It is recommended that you simply copy one of the existing environment scripts and rename it as appropriate.<br>
</li>
<li>Edit the environment script and modify the first line that begins with "export WORKSPACE_HOME". Your workspace home should be the absolute path to your subversion checkout.<br>
</li>
<li>Add the ubuntugis stable packages<br>
<pre><code>sudo apt-add-repository ppa:ubuntugis/ubuntugis-stable<br>
</code></pre>
</li>
<li>Run the script "bin/setup_scripts/setup_ubuntu.sh", this will install all the required packages for POS<br>
<pre><code>cd bin/setup_scripts/<br>
chmod +x setup_ubuntu.sh<br>
./setup_ubuntu.sh<br>
</code></pre>
The script will also setup a postgis template database called "template_postgis". If you already have postgres/postgis set up on your computer, it is recommended that you modify this script so that you do not install multiple versions of postgres onto your computer. The project has been configured to expect a postgres password of "postgres". You may choose any password you like however if you do, you will also need to make the corresponding adjustment in your django settings file.<br>
</li>
<li>To install the Python virtual environment, run the script<br>
"bin/setup_scripts/setup_dev.sh"<br>
<pre><code>cd bin/setup_scripts/<br>
chmod +x setup_dev.sh<br>
./setup_dev.sh<br>
</code></pre>
</li>
<li>If you are running the project for the first time, you will need to create a spatial database for your data. Run the script "bin/syncdb.sh". This script  will drop your existing database, create a new database and create the necessary tables, sequences and indexes.<br>
<pre><code>cd bin/setup_scripts/<br>
chmod +x syncdb.sh<br>
./syncdb.sh<br>
</code></pre>
</li>
<li>Populate the database<br>
<pre><code><br>
</code></pre>
</li>
<li>To run the development webserver, use the script "bin/runserver.sh".<br>
<pre><code>cd bin/setup_scripts/<br>
chmod +x runserver.sh<br>
./runserver.sh<br>
</code></pre>
</li>
</ol>

## Install and Setup GeoServer ##
### Install Tomcat ###
```
sudo apt-get install tomcat7
```

### Install GeoServer ###
This is summarised from the GeoServer installation documentation http://docs.geoserver.org/stable/en/user/installation/war.html

<ol>
<li>Download GeoServer from <a href='http://sourceforge.net/projects/geoserver/files/GeoServer/2.4.0/geoserver-2.4.0-war.zip'>http://sourceforge.net/projects/geoserver/files/GeoServer/2.4.0/geoserver-2.4.0-war.zip</a></li>
<li>Deploy GeoServer by unzipping the war file to the tomcat webapps directory<br>
<pre><code>/var/lib/tomcat7/webapps<br>
</code></pre>
</li>

<li>Access GeoServer Admin from <a href='http://localhost:8080/geoserver'>http://localhost:8080/geoserver</a>
<pre><code>User: admin<br>
Password: geoserver<br>
</code></pre>
</li>
</ol>

### Configure GeoServer ###

#### Create Polygon Style ####
<ol>
<li>Add a new style<br>
<pre><code>Name: pos_polygons<br>
Workspace: UWA-POS<br>
SLD File: Browse to ?<br>
</code></pre>
</li>
<li>Submit</li>
</ol>

#### Configure GeoServer Layers ####
<ol>
<li>Setup Workspace</li>
<li>Add new workspace<br>
<pre><code>name: UWA-POS<br>
Namespace: www.postool.com.au<br>
Check default workspace<br>
</code></pre>
</li>
</ol>

#### Setup Data Store ####
<ol>
<li>Add new store</li>
<li>Select PostGIS<br>
<pre><code>Workspace: UWA-POS<br>
Data Source Name: uwa_pos<br>
Host: localhost<br>
Port: 5432<br>
Database: cbeh_pos<br>
Schema; public<br>
User: postgres<br>
Password: postgres<br>
</code></pre>
</li>
</ol>

#### Setup Layers ####
<ol>
<li>Add a new resource<br>
<pre><code>UWA-POS:uwa_pos<br>
</code></pre>
</li>
<li>Select the publish action for the pos_pos layer</li>
<li>Select the data tab<br>
<pre><code>Native Bounding Box - Select 'Compute from data'<br>
Lat/Lon Bounding Box - Select 'Compute from data'<br>
</code></pre>
</li>
<li>Select the publishing tab<br>
<pre><code>Default style - Select 'pos_polygons'<br>
</code></pre>
</li>
<li>Save the layer</li>
<li>Repeat the publishing process for the following layers<br>
<pre><code>pos_pos_club<br>
pos_pos_green<br>
pos_pos_natural<br>
pos_pos_park<br>
pos_pos_school<br>
</code></pre>
</li>
</ol>

#### Test Layers ####
<ol>
<li>Select Data > Layer Preview</li>
<li>Select Common Formats > OpenLayers for each created layer to preview the layer</li>
<li>If the layer has been configured correctly a map should open and display the data for the selected layer</li>
</ol>

### User Guide ###
The POS Tool user guide can be found in the
```
/CBEH/POS/Static/Documents/
```
folder of your deployment.