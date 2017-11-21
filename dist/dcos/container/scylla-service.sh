#!/bin/bash

. /usr/lib/scylla/scylla_prepare

export SCYLLA_HOME SCYLLA_CONF

echo $SCYLLA_ARGS $SEASTAR_IO $DEV_MODE $CPUSET $SCYLLA_DOCKER_ARGS > ~/arguments.txt

exec /usr/bin/scylla $SCYLLA_ARGS $SEASTAR_IO $DEV_MODE $CPUSET $SCYLLA_DOCKER_ARGS
