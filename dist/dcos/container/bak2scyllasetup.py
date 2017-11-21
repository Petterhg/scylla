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
        self._run(['/usr/lib/scylla/scylla_io_setup'])

    def cqlshrc(self):
        logging.info("Setting up cqlshrc file...")
        home = os.environ['HOME']
        hostname = os.environ['HOST']
        if self.env_yaml['authenticator'] is 'PasswordAuthenticator':
            with open("%s/.cqlshrc" % home, "w") as cqlshrc:
                cqlshrc.write("[authenticator]\nusername = %s\npassword = %s\n" 
                %(self.env_yaml['username'], self.env_yaml['password']))
        
        if self.env_yaml['authenticator'] is not 'PasswordAuthenticator':
            with open("%s/.cqlshrc" % home, "w") as cqlshrc:
                cqlshrc.write("# No username and password set\n")
        
        if self.env_yaml['clientSSL']:
            with open("%s/.cqlshrc" % home, "a") as cqlshrc:
                cqlshrc.write("[connection]\nhostname = %s\nport = %s\nfactory = cqlshlib.ssl.ssl_transport_factory\n"                          %(hostname, self.env_yaml['cqlPort']))
            if not self.env_yaml['downloadKeys']:
                with open("%s/.cqlshrc" % home, "a") as cqlshrc:
                    cqlshrc.write("[ssl]\ncertfile = %s\n" % self.env_yaml['clientCertPath'])
            elif self.env_yaml['downloadKeys']:
                mesosSandbox = os.environ['MESOS_SANDBOX']
                with open("%s/.cqlshrc" % home, "a") as cqlshrc:
                    cqlshrc.write("[ssl]\ncertfile = %s/scylladb.crt\n" %mesosSandbox) 
        if not self.env_yaml['clientSSL']:
            with open("%s/.cqlshrc" % home, "a") as cqlshrc:
                cqlshrc.write("[connection]\nhostname = %s\nport = %s\n" %(hostname, self.env_yaml['cqlPort']))

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
        hostname = os.environ['HOST']
        mesosSandbox = os.environ['MESOS_SANDBOX']
        seedString = self.setSeeds()

        args += ["--cluster-name %s" % self.env_yaml['clusterName']] 
        args += ["--endpoint-snitch %s" % self.env_yaml['endpointSnitch']]
        args += ["--seed-provider-parameters seeds=%s" % seedString]
        args += ["--batch-size-warn-threshold-in-kb %s" % self.env_yaml['batchWarnThreshold']]
        args += ["--batch-size-fail-threshold-in-kb %s" % self.env_yaml['batchFailThreshold']]
        args += ["--broadcast-address %s" % hostname]
        args += ["--partitioner %s" % self.env_yaml['partitioner']]
        args += ["--broadcast-rpc-address %s" % hostname]
        args += ["--authenticator %s" % self.env_yaml['authenticator']]       
 
        if self.env_setup['experimental']:
            args += ["--experimental 1"]
        else:
            args += ["--experimental 0"]
        
        if self.env_yaml['nodeSSL']:
            if self.env_yaml['downloadKeys']:
                args += ["--server-encryption-options internode_encryption=%s certificate=%s/scylladb.crt keyfile=%s/scylladb.key truststore=%s/ca-scylladb.pem"
                            %(self.env_yaml['nodeLevel'], mesosSandbox, mesosSandbox, mesosSandbox)]
            else:
                args += ["--server-encryption-options internode_encryption=%s certificate=%s keyfile=%s truststore=%s"
                            %(self.env_yaml['nodeLevel'], self.env_yaml['nodeCertPath'], self.env_yaml['nodeKeyPath'], 
                                self.env_yaml['nodeTrustStore'])]

        if self.env_yaml['clientSSL']:
            if self.env_yaml['downloadKeys']:
                args += ["--client-encryption-options enabled=true certificate=%s/scylladb.crt keyfile=%s/scylladb.key"
                            %(mesosSandbox, mesosSandbox)]
            else:
                args += ["--client-encryption-options enabled=true certificate=%s/scylladb.crt keyfile=%s/scylladb.key"
                            %(self.env_yaml['clientCertPath'], self.env_yaml['clientKeyPath'])]

        args += ["--load-balance %s" % self.env_yaml['cqlLoadBalance']]
        args += ["--blocked-reactor-notify-ms 999999999"]
        
        if self.env_setup["overprovisioned"]:
            args += ["--overprovisioned 1"]
        else:
            args += ["--overprovisioned 0"]
        
        args += ["--smp %d" % int(self.env_container["cpus"])]
        args += ["--memory %dM" % int(self.env_container["mem"])]         
              
        with open("/etc/scylla.d/docker.conf", "w") as cqlshrc:
            cqlshrc.write("SCYLLA_DOCKER_ARGS=\"%s\"\n" % " ".join(args))

    def cassandraProperties(self):
        print("Setting up cassandra-properties file...")
        rackId = self.setRack()
        with open('/etc/scylla/cassandra-rackdc.properties', 'w') as outfile:
            outfile.write("dc=%s\nrack=%s\nprefer_local=false" 
                %(self.env_cassandra['dataCenter'], rackId))

             
