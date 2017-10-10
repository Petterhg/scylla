import os

def env_setup():
    setupDict = {}
    setupDict['overprovisioned'] = os.environ.get('SCYLLA_OVERPROVISIONED')
    setupDict['experimental'] = os.environ.get('SCYLLA_EXPERIMENTAL')
    setupDict['developerMode'] = os.environ.get('SCYLLA_DEVELOPER_MODE')
    return setupDict
    
def env_container():
    containerDict = {}
    containerDict['cpus'] = os.environ.get('SCYLLA_SMP')
    containerDict['mem'] = os.environ.get('SCYLLA_MEM')
    containerDict['numberOfSeeds'] = os.environ.get('SCYLLA_SEEDS')

def env_yaml():
    yamlDict = {}
    yamlDict['endpointSnitch'] = os.environ.get('SCYLLA_ENDPOINTSNITCH')
    yamlDict['cqlPort'] = os.environ.get('SCYLLA_CQL_PORT')
    yamlDict['thriftPort'] = os.environ.get('SCYLLA_THRIFT_PORT')
    yamlDict['batchWarnThreshold'] = os.environ.get('SCYLLA_BATCH_SIZE_WARN')
    yamlDict['batchFailThreshold'] = os.environ.get('SCYLLA_BATCH_SIZE_FAIL')
    yamlDict['authenticator'] = os.environ.get('SCYLLA_AUTHENTICATOR')
    yamlDict['username'] = os.environ.get('SCYLLA_USERNAME')
    yamlDict['password'] = os.environ.get('SCYLLA_PASSWORD')
    yamlDict['clientSSL'] = os.environ.get('SCYLLA_CLIENT_SSL_ENABLE')
    yamlDict['clientCertPath'] = os.environ.get('SCYLLA_CLIENT_CERT_PATH')
    yamlDict['clientKeyPath'] = os.environ.get('SCYLLA_CLIENT_KEY_PATH')
    yamlDict['nodeSSL'] = os.environ.get('SCYLLA_NODE_SSL_ENABLE')
    yamlDict['nodeLevel'] = os.environ.get('SCYLLA_NODE_LEVEL')
    yamlDict['nodeCertPath'] = os.environ.get('SCYLLA_NODE_CERT_PATH')
    yamlDict['nodeKeyPath'] = os.environ.get('SCYLLA_NODE_KEY_PATH')
    yamlDict['nodeTrustStore'] = os.environ.get('SCYLLA_NODE_TRUST_STORE')
    yamlDict['downloadKeys'] = os.environ.get('SCYLLA_DOWNLOAD_KEYS')
    yamlDict['downloadPath'] = os.environ.get('SCYLLA_DOWNLOAD_PATH')
    yamlDict['clusterName'] = os.environ.get('SCYLLA_CLUSTER_NAME')
    return yamlDict
        
def env_cassandraprop():
    cassandrapropDict = {}
    cassandrapropDict['newRack'] = os.environ.get('SCYLLA_NEW_RACK')
    cassandrapropDict['dataCenter'] = os.environ.get('SCYLLA_DATACENTER_NAME')
    return cassandrapropDict
