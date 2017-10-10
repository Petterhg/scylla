import subprocess
import logging
import yaml
import os
import http.client
import json
import sys
import socket

import environmentcollector

class ScyllaSetup:
    def __init__(self):
        self.env_setup = environmentcollector.env_setup()
        self.env_container = environmentcollector.env_container()
        self.env_yaml = environmentcollector.env_yaml()
        self.env_cassandra = environmentcollector.env_cassandraprop()

    def _run(self, *args, **kwargs):
        logging.info('running: {}'.format(args))
        subprocess.check_call(*args, **kwargs)

    def developerMode(self):
        self._run(['/usr/lib/scylla/scylla_dev_mode_setup', '--developer-mode', self.env_setup['developerMode'])

    def io(self):
        self._run(['/usr/lib/scylla/scylla_io_setup'])

    def cqlshrc(self):
        home = os.environ['HOME']
        hostname = os.environ['HOST']
        if self.env_yaml['authentication'] is 'PasswordAuthenticator':
            with open("%s/.cqlshrc" % home, "w") as cqlshrc:
                cqlshrc.write("[authentication]\nusername = %s\npassword = %s\n" 
                %(self.env_yaml['username'], self.env_yaml['password']))
        
        if self.env_yaml['authentication'] is not 'PasswordAuthenticator':
            with open("%s/.cqlshrc" % home, "w") as cqlshrc:
                cqlshrc.write("# No username and password set")
        
        if self.env_yaml['clientSSL']:
            with open("%s/.cqlshrc" % home, "a") as cqlshrc:
                cqlshrc.write("[connection]\nhostname = %s\nport = %s\nfactory = cqlshlib.ssl.ssl_transport_factory\n"                          %(hostname, self.env_yaml['cqlPort']))
            if not self.env_yaml['downloadKeys']:
                with open("%s/.cqlshrc" % home, "a") as cqlshrc:
                    cqlshrc.write("[ssl]\ncertfile = %s\n" % self.env_yaml['clientCertPath'])
            elif self.env_yaml['downloadKeys']:
                with open("%s/.cqlshrc" % home, "a") as cqlshrc:
                    cqlshrc.write("[ssl]\ncertfile = %s\n" % self.env_yaml['downloadPath']) 
        if not self.env_yaml['clientSSL']:
            with open("%s/.cqlshrc" % home, "a") as cqlshrc:
                cqlshrc.write("[connection]\nhostname = %s\nport = %s\n" %(hostname, self.env_yaml['cqlPort']))

    def setSeeds(self):
        seedString = ""
        masterIp = socket.gethostbyname('leader.mesos')
        marathonPort = 8080
        numOfSeeds = int(self.env_container['numberOfSeeds'])
        conn = http.client.HTTPConnection(masterIp, marathonPort)
        serviceName = os.environ['MARATHON_APP_ID']
        conn.request("GET", "/v2/apps%s/tasks" %serviceName)
        resp = conn.getresponse()
        data = json.loads(r.read().decode('utf-8'))['tasks']
        if numOfSeeds >= len(data):
            print("Number of seeds must be less than total number of nodes")
            sys.exit()
        else:
            for i in range(0, numOfSeeds)):
                seedString += data[i]['ipAddresses'][0]['ipAddress']
                if i < numOfSeeds-1:
                    seedString += ","
        return seedString

    def setRack(self):
        if self.env_cassandraprop['newRack']:
            hostname = os.environ['HOST']
            masterIp = socket.gethostbyname('leader.mesos')
            marathonPort = 8080
            conn = http.client.HTTPConnection(masterIp, marathonPort)
            serviceName = os.environ['MARATHON_APP_ID']
            conn.request("GET", "/v2/apps%s/tasks" %serviceName)
            resp = conn.getresponse()
            data = json.loads(r.read().decode('utf-8'))['tasks']
            for i in range(0, len(data)):
                if data[i]['ipAddresses'][0]['ipAddress'] == hostname:
                   rackId = "rack"+str(i)
        else:
            rackId = "rack0"
 
        return rackId
             
    def scyllaYaml(self):
        yamlDict = {}
        hostname = os.environ['HOST']
        yamlDict['cluster_name'] = self.env_yaml['clusterName']
        yamlDict['num_tokens'] = 256
        yamlDict['data_file_directories'] = ['/var/lib/scylla/data']
        yamlDict['commitlog_directories'] = ['/var/lib/scylla/commitlog'] 
        yamlDict['commitlog_sync'] = 'periodic'
        yamlDict['commitlog_sync_period_in_ms'] = 10000
        yamlDict['commitlog_segment_size_in_mb'] = 32
        seedString = self.setSeeds()
        yamlDict['seed_provider'] = [{'class_name': 'org.apache.cassandra.locator.SimpleSeedProvider', 
                                        'parameters': [{'seeds': seedString}]}]
        yamlDict['listen_address'] = 'localhost'
        yamlDict['broadcast_address'] = hostname
        yamlDict['native_transport_port'] = 9042
        yamlDict['read_request_timeout_in_ms'] = 5000
        yamlDict['write_request_timeout_in_ms'] = 2000
        yamlDict['endpoint_snitch'] = self.env_yaml['endpointSnitch']
        yamlDict['rpc_address'] = 'localhost'
        yamlDict['rpc_port'] = 9160
        yamlDict['api_port'] = 10000
        yamlDict['api_address'] = '127.0.0.1'
        yamlDict['batch_size_warn_threshold_in_kb'] = self.env_yaml['batchWarnThreshold']
        yamlDict['batch_size_fail_threshold_in_kb'] = self.env_yaml['batchFailThreshold']
        yamlDict['authenticator'] = self.env_yaml['authenticator']
        yamlDict['broadcast_rpc_address'] = hostname
        yamlDict['experimental'] = self.env_setup['experimental']
        
        stream = file('/etc/scylla/scylla.yaml', 'w')
        yaml.dump(yamlDict, stream)        

    def cassandraProperties(self):
        rackId = self.setRack()
        with open('/etc/scylla/cassandra-rackdc.properties', 'w') as outfile:
            outfile.write("dc=%s\nrack=%s\nprefer_local=false" 
                %(self.env_cassandraprop['dataCenter'], rackId))
             
