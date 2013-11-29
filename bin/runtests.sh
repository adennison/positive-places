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
coverage run --source=$PROJECT_HOME manage.py test --verbosity=2 pos
retval=$?

coverage xml --omit /usr/,$VIRTUAL_ENV_HOME
coverage html --omit /usr/,$VIRTUAL_ENV_HOME -d /tmp/pos_coverage_report

# Clean up the virtual environment
deactivate

popd
exit $retval


