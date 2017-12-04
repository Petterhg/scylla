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
        if self.env_setup['developerMode']:
            mode = '1'
        else:
            mode = '0'
        self._run(['/usr/lib/scylla/scylla_dev_mode_setup', '--developer-mode', mode])

    def io(self):
        subprocess.Popen(["mkdir", "/var/lib/scylla/data"])        
        subprocess.Popen(["mkdir", "/var/lib/scylla/commitlog"])        
        self._run(['/usr/lib/scylla/scylla_io_setup'])

    def cqlshrc(self):
        logging.info("Setting up cqlshrc file...")
        home = os.environ['HOME']
        hostname = subprocess.check_output(['hostname', '-i']).decode('ascii').strip() 
        if self.env_yaml['authenticator'] == 'PasswordAuthenticator':
            with open("%s/.cqlshrc" % home, "w") as cqlshrc:
                cqlshrc.write("[authenticator]\nusername = %s\npassword = %s\n" 
                %(self.env_yaml['username'], self.env_yaml['password']))
        
        if self.env_yaml['authenticator'] != 'PasswordAuthenticator':
            with open("%s/.cqlshrc" % home, "w") as cqlshrc:
                cqlshrc.write("# No username and password set\n")
        
        if self.env_yaml['clientSSL']:
            with open("%s/.cqlshrc" % home, "a") as cqlshrc:
                cqlshrc.write("[connection]\nhostname = %s\nport = 9042\nfactory = cqlshlib.ssl.ssl_transport_factory\n" % hostname)
            if not self.env_yaml['downloadKeys']:
                with open("%s/.cqlshrc" % home, "a") as cqlshrc:
                    cqlshrc.write("[ssl]\ncertfile = /etc/scylla/keys/client/scylladb.crt\n")
            elif self.env_yaml['downloadKeys']:
                mesosSandbox = os.environ['MESOS_SANDBOX']
                with open("%s/.cqlshrc" % home, "a") as cqlshrc:
                    cqlshrc.write("[ssl]\ncertfile = %s/scylladb.crt\n" %mesosSandbox) 
        if not self.env_yaml['clientSSL']:
            with open("%s/.cqlshrc" % home, "a") as cqlshrc:
                cqlshrc.write("[connection]\nhostname = %s\nport = 9042\n" %hostname)

    def setSeeds(self):
        logging.info("Determining seed nodes...")
        seedString = ""
        masterIp = socket.gethostbyname('leader.mesos')
        marathonPort = 8080
        numOfSeeds = self.env_container['numberOfSeeds']
        conn = http.client.HTTPConnection(masterIp, marathonPort)
        serviceName = os.environ['MARATHON_APP_ID']
        conn.request("GET", "/v2/apps%s/tasks" %serviceName)
        resp = conn.getresponse()
        data = json.loads(resp.read().decode('utf-8'))['tasks']
        if numOfSeeds > len(data):
            logging.info("Number of seeds must be less than total number of nodes, exiting...")
            sys.exit()
        else:
            for i in range(0, numOfSeeds):
                seedString += data[i]['host']
                if i < numOfSeeds-1:
                    seedString += ","
        return seedString

    def setRack(self):
        logging.info("Assigning rack id's to nodes...")
        if self.env_cassandra['newRack']:
            hostname = os.environ['HOST']
            masterIp = socket.gethostbyname('leader.mesos')
            marathonPort = 8080
            conn = http.client.HTTPConnection(masterIp, marathonPort)
            serviceName = os.environ['MARATHON_APP_ID']
            conn.request("GET", "/v2/apps%s/tasks" %serviceName)
            resp = conn.getresponse()
            data = json.loads(resp.read().decode('utf-8'))['tasks']
            for i in range(0, len(data)):
                if data[i]['host'] == hostname:
                   rackId = "rack"+str(i)
        else:
            rackId = "rack0"
 
        return rackId
             
    def scyllaYaml(self):
        logging.info("Starting the scylla.yaml configuration...")
        args = []
        yamlDict = {}
        hostname = os.environ['HOST']
        mesosSandbox = os.environ['MESOS_SANDBOX']
        seedString = self.setSeeds()
         
        # --------- TO YAML ---------
        yamlDict['cluster_name'] = self.env_yaml['clusterName']
        yamlDict['data_file_directories'] = ['/var/lib/scylla/data']
        yamlDict['commitlog_directory'] = '/var/lib/scylla/commitlog'
        yamlDict['endpoint_snitch'] = self.env_yaml['endpointSnitch']
        yamlDict['batch_size_warn_threshold_in_kb'] = self.env_yaml['batchWarnThreshold']
        yamlDict['batch_size_fail_threshold_in_kb'] = self.env_yaml['batchFailThreshold']
        yamlDict['authenticator'] = self.env_yaml['authenticator']
        yamlDict['authorizer'] = 'AllowAllAuthorizer'
    
        if self.env_yaml['authenticator'] == 'PasswordAuthenticator':
            yamlDict['authorizer'] = 'CassandraAuthorizer'
 
        if self.env_yaml['nodeSSL']:
            if self.env_yaml['downloadKeys']:
                yamlDict['server_encryption_options'] = {'internode_encryption': self.env_yaml['nodeLevel'],
                                                        'certificate': '%s/scylladb.crt' %mesosSandbox,
                                                        'keyfile': '%s/scylladb.key' %mesosSandbox,
                                                        'truststore': '%s/ca-scylladb.pem' %mesosSandbox
                                                        }
            else:
                yamlDict['server_encryption_options'] = {'internode_encryption': self.env_yaml['nodeLevel'],
                                                        'certificate': '/etc/scylla/keys/node/scylladb.crt',
                                                        'keyfile': '/etc/scylla/keys/node/scylladb.key',
                                                        'truststore': '/etc/scylla/keys/node/ca-scylladb.pem'
                                                        }
        if self.env_yaml['clientSSL']:
            if self.env_yaml['downloadKeys']:
                yamlDict['client_encryption_options'] = {'enabled': 'true',
                                                        'certificate': '%s/scylladb.crt' %mesosSandbox,
                                                        'keyfile': '%s/scylladb.key' %mesosSandbox
                                                        }
            else:
                yamlDict['client_encryption_options'] = {'enabled': 'true',
                                                        'certificate': '/etc/scylla/keys/client/scylladb.crt',
                                                        'keyfile': '/etc/scylla/keys/client/scylladb.key'
                                                        }
        yamlDict['commitlog_sync'] = 'periodic'
        yamlDict['commitlog_sync_period_in_ms'] = 10000
        yamlDict['commitlog_segment_size_in_mb'] = 32
        yamlDict['native_transport_port'] = 9042
        yamlDict['read_request_timeout_in_ms'] = 5000
        yamlDict['write_request_timeout_in_ms'] = 2000
        yamlDict['api_port'] = 10000
        yamlDict['api_address'] = '127.0.0.1'
        yamlDict['murmur3_partitioner_ignore_msb_bits'] = 12
        yamlDict['api_ui_dir'] = '/usr/lib/scylla/swagger-ui/dist/'
        yamlDict['api_doc_dir'] = '/usr/lib/scylla/api/api-doc/'
        stream = open('/etc/scylla/scylla.yaml', 'w')
        yaml.dump(yamlDict, stream)
        
        # --------- TO CMD ---------
        listen_address = subprocess.check_output(['hostname', '-i']).decode('ascii').strip()
        args += ["--listen-address %s" %listen_address]
        args += ["--rpc-address %s" %listen_address]

        if self.env_setup["overprovisioned"]:
            args += ["--overprovisioned"]
       
        args += ["--smp %d" % int(self.env_container["cpus"])]
        args += ["--memory %dM" % int(self.env_container["mem"])]         
        args += ["--seed-provider-parameters seeds=%s" % seedString]
        args += ["--broadcast-address %s" % hostname]
        args += ["--broadcast-rpc-address %s" % hostname]
 
        if self.env_setup['experimental']:
            args += ["--experimental=on"]
        
        args += ["--blocked-reactor-notify-ms 999999999"]
              
        with open("/etc/scylla.d/docker.conf", "w") as cqlshrc:
            cqlshrc.write("SCYLLA_DOCKER_ARGS=\"%s\"\n" % " ".join(args))

    def cassandraProperties(self):
        print("Setting up cassandra-properties file...")
        rackId = self.setRack()
        with open('/etc/scylla/cassandra-rackdc.properties', 'w') as outfile:
            outfile.write("dc=%s\nrack=%s\nprefer_local=false" 
                %(self.env_cassandra['dataCenter'], rackId))

             
