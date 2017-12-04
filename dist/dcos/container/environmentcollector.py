import os

def stringToBool(s):
    if (s == 'true') or (s == 'True'):
        return True
    if (s == 'false') or (s == 'False'):
        return False

def env_setup():
    setupDict = {}
    setupDict['overprovisioned'] = stringToBool(os.environ.get('SCYLLA_OVERPROVISIONED'))
    setupDict['experimental'] = stringToBool(os.environ.get('SCYLLA_EXPERIMENTAL'))
    setupDict['developerMode'] = stringToBool(os.environ.get('SCYLLA_DEVELOPER_MODE'))
    return setupDict
    
def env_container():
    containerDict = {}
    containerDict['cpus'] = int(os.environ.get('SCYLLA_SMP'))
    containerDict['mem'] = int(os.environ.get('SCYLLA_MEM'))
    containerDict['numberOfSeeds'] = int(os.environ.get('SCYLLA_SEEDS'))
    return containerDict

def env_yaml():
    yamlDict = {}
    yamlDict['endpointSnitch'] = os.environ.get('SCYLLA_ENDPOINT_SNITCH')
    yamlDict['cqlPort'] = int(os.environ.get('SCYLLA_CQL_PORT'))
    yamlDict['thriftPort'] = int(os.environ.get('SCYLLA_THRIFT_PORT'))
    yamlDict['batchWarnThreshold'] = int(os.environ.get('SCYLLA_BATCH_SIZE_WARN'))
    yamlDict['batchFailThreshold'] = int(os.environ.get('SCYLLA_BATCH_SIZE_FAIL'))
    yamlDict['authenticator'] = os.environ.get('SCYLLA_AUTHENTICATOR')
    yamlDict['username'] = os.environ.get('SCYLLA_USERNAME')
    yamlDict['password'] = os.environ.get('SCYLLA_PASSWORD')
    yamlDict['clientSSL'] = stringToBool(os.environ.get('SCYLLA_CLIENT_SSL_ENABLE'))
    yamlDict['clientPath'] = os.environ.get('SCYLLA_CLIENT_PATH')
    yamlDict['nodeSSL'] = stringToBool(os.environ.get('SCYLLA_NODE_SSL_ENABLE'))
    yamlDict['nodeLevel'] = os.environ.get('SCYLLA_NODE_LEVEL')
    yamlDict['nodePath'] = os.environ.get('SCYLLA_NODE_PATH')
    yamlDict['downloadKeys'] = stringToBool(os.environ.get('SCYLLA_DOWNLOAD_KEYS'))
    yamlDict['downloadPath'] = os.environ.get('SCYLLA_DOWNLOAD_PATH')
    yamlDict['clusterName'] = os.environ.get('SCYLLA_CLUSTER_NAME')
    return yamlDict
        
def env_cassandraprop():
    cassandrapropDict = {}
    cassandrapropDict['newRack'] = stringToBool(os.environ.get('SCYLLA_NEW_RACK'))
    cassandrapropDict['dataCenter'] = os.environ.get('SCYLLA_DATACENTER_NAME')
    return cassandrapropDict
