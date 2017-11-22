#!/bin/bash

. /usr/lib/scylla/scylla_prepare

export SCYLLA_HOME SCYLLA_CONF

echo $SCYLLA_ARGS $SEASTAR_IO $DEV_MODE $CPUSET $SCYLLA_DOCKER_ARGS > ~/arguments.txt

LEADER=$(curl -q http://leader.mesos:8080/v2/apps/$MARATHON_APP_ID/tasks | jq '.tasks[0].host' | sed 's/\"//g')

if [ $SCYLLA_AUTHENTICATOR == "PasswordAuthenticator" ] && [ $LEADER == $HOST ]; then
    nohup /usr/bin/scylla $SCYLLA_ARGS $SEASTAR_IO $DEV_MODE $CPUSET $SCYLLA_DOCKER_ARGS &
    exec /system_auth_replicator.sh
else
    exec /usr/bin/scylla $SCYLLA_ARGS $SEASTAR_IO $DEV_MODE $CPUSET $SCYLLA_DOCKER_ARGS
fi 
