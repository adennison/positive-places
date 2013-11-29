#!/bin/bash

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

$WORKSPACE_HOME/bin/setup_scripts/setup_ubuntu.sh $env_tag
$WORKSPACE_HOME/bin/setup_scripts/setup_dev.sh $env_tag
