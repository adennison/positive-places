#!/bin/bash

# Pull in the configurable environment variables
if [ ! -n "$1" ]
then
    env_tag=$HOSTNAME
else
    env_tag=$1
fi

echo Environment Tag \'$env_tag\'
# The complexity allows us to run the script from any directory.
scriptdir=$(cd `dirname $0` && pwd)
source "$scriptdir"/../env/environment_$env_tag.sh

# Store the original location for karma
pushd .

mkdir -p "$WORKSPACE_HOME"
cd "$WORKSPACE_HOME"


# First the binary stuff
sudo apt-get install python-dev python-pip binutils gdal-bin postgresql-9.1-postgis postgresql-server-dev-9.1
#sudo pip install setuptools
sudo pip install virtualenv

echo "Creating Postgis Template"
sudo -u postgres bash bin/setup_scripts/create_template_postgis-debian.sh

# Set the postgres password
clear
echo ============================
echo Set up the postgres password.
echo ============================
echo This script expects that the postgress password will be \'postgres\'.
echo Set the password by running the command \'\\password postgres\'
echo Enter the password twice then quit using the command \\q
sudo -u postgres psql postgres
#\password postgres
# Also consider installing pgadmin3 as a GUI front end to your database
# sudo apt-get install pgadmin3

# Back to the original location
popd