#!/bin/bash
pushd .

# Load the environment.
if [ ! -n "$1" ]
then
    env_tag=$HOSTNAME
else
    env_tag=$1
fi

echo Environment Tag \'$env_tag\'
# The complexity allows us to run the script from any directory.
scriptdir=$(cd `dirname $0` && pwd)
echo scriptdir \'$scriptdir\'
source "$scriptdir"/env/environment_$env_tag.sh

# Activate the virtual environment
source "$VIRTUAL_ENV_HOME"/bin/activate

cd "$PROJECT_HOME"
host_ip=$(ifconfig eth1 | awk '/inet addr/ {split ($2,A,":"); print A[2]}')
python manage.py runserver $host_ip:$WEBSERVER_PORT

# Clean up the virtual environment
deactivate


popd
