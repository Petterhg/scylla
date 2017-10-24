#!/usr/bin/env python3
import os
import sys
import scyllasetup
import logging

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format="%(message)s")

try:
    setup = scyllasetup.ScyllaSetup() 
    setup.developerMode()
    setup.io()
    setup.cqlshrc()
    setup.scyllaYaml()
    setup.cassandraProperties()
    os.system("/usr/bin/supervisord -c /etc/supervisord.conf")
except:
    logging.exception('failed!')
