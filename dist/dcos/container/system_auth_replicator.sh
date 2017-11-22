#!/bin/bash
success=1
while [ $success -ne 0 ]; do
        cqlsh -u cassandra -p cassandra -e "ALTER KEYSPACE system_auth WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : $SCYLLA_NODES};" 2> /dev/null
        success=$?
        sleep 30
done
nodetool repair system_auth
exit
