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

echo Dropping database \'$PROJECT_DATABASE_NAME\'
echo Please enter the PostgreSQL password
#sudo -u postgres dropdb $PROJECT_DATABASE_NAME
echo Creating database \'$PROJECT_DATABASE_NAME\'
sudo -u postgres createdb -T template_postgis $PROJECT_DATABASE_NAME

# Activate the virtual environment
echo VirtualEnv Home \'$VIRTUAL_ENV_HOME\'
source "$VIRTUAL_ENV_HOME"/bin/activate

echo Project Home directory \'$PROJECT_HOME\'
cd "$PROJECT_HOME"
python manage.py syncdb --noinput
#python manage.py syncdb
#python manage.py createcachetable $CACHE_TABLENAME

# Clean up the virtual environment
deactivate

popd
