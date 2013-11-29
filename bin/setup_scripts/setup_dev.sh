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


# Remember the current directory
pushd .

cd "$WORKSPACE_HOME"

# OK now we are going to get into our virtual environment
virtualenv "$VIRTUAL_ENV_HOME"
source "$VIRTUAL_ENV_HOME"/bin/activate
sudo apt-get install freetype2 wbritish-large
pip install psycopg2 coverage docutils django xlwt pillow django-simple-captcha
deactivate
