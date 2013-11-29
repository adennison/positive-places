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
source "$scriptdir"/env/environment_$env_tag.sh

# Activate the virtual environment
source "$VIRTUAL_ENV_HOME"/bin/activate

cd "$PROJECT_HOME"
python manage.py flush --noinput
#python manage.py syncdb
#python manage.py createcachetable $CACHE_TABLENAME

# Clean up the virtual environment
deactivate

popd
