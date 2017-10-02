#!/usr/bin/env python3
import os
import sys
import scyllasetup
import logging
import environmentcollector 

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format="%(message)s")

try:
    #parameters = {'setup': environmentcollector.env_setup(), 'container': environmentcollector.env_container(),
    #            'yaml': environmentcollector.env_yaml(), 'cassandra': environmentcollector.env_cassandraprop()}
    #setup = scyllasetup.ScyllaSetup(parameters)
    setup = scyllasetup.ScyllaSetup() 
    setup.developerMode()
    setup.cpuSet()
    setup.io()
    setup.cqlshrc()
    setup.arguments()
    os.system("/usr/bin/supervisord -c /etc/supervisord.conf")
except:
    logging.exception('failed!')
