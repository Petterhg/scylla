import subprocess
import logging
import yaml
import os
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
            with open("%s/.cassandra/.cqlshrc" % home, "w") as cqlshrc:
                cqlshrc.write("[authentication]\nusername = %s\npassword = %s\n" 
                %(self.env_yaml['username'], self.env_yaml['password']))
            if self.env_yaml['clientSSL']:
                with open("%s/.cassandra/.cqlshrc" % home, "a") as cqlshrc:
                    cqlshrc.write("[connection]\nhostname = %s\nport = %s\nfactory = %s\n" %(hostname
                
            
        if self.env_yaml['clientSSL']:
        with open("%s/.cassandra/.cqlshrc" % home, "w") as cqlshrc:
            cqlshrc.write("[connection]\nhostname = %s\n" % hostname)

    def arguments(self):
        args = []
        if self._memory is not None:
            args += [ "--memory %s" % self._memory ]
        if self._smp is not None:
            args += [ "--smp %s" % self._smp ]
        if self._overprovisioned == "1":
            args += [ "--overprovisioned" ]

        if self._listenAddress is None:
            self._listenAddress = subprocess.check_output(['hostname', '-i']).decode('ascii').strip()
        if self._seeds is None:
            if self._broadcastAddress is not None:
                self._seeds = self._broadcastAddress
            else:
                self._seeds = self._listenAddress

        args += [ "--listen-address %s" %self._listenAddress,
                  "--rpc-address %s" %self._listenAddress,
                  "--seed-provider-parameters seeds=%s" % self._seeds ]

        if self._broadcastAddress is not None:
            args += ["--broadcast-address %s" %self._broadcastAddress ]
        if self._broadcastRpcAddress is not None:
            args += [ "--broadcast-rpc-address %s" %self._broadcastRpcAddress ]

        if self._apiAddress is not None:
            args += ["--api-address %s" %self._apiAddress ]

        if self._experimental == "1":
            args += [ "--experimental=on" ]

        args += ["--blocked-reactor-notify-ms 999999999"]

        with open("/etc/scylla.d/docker.conf", "w") as cqlshrc:
            cqlshrc.write("SCYLLA_DOCKER_ARGS=\"%s\"\n" % " ".join(args))
