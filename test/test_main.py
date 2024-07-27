from importlib import import_module

TestClient = import_module("fastapi.testclient").TestClient
main = import_module("app.main","ip-server")
app = main.app

#
# Unit tests for Tidegates web services
#

client = TestClient(app)

### Test the projects entry point

def test_projects():
    '''
    Make sure the demo project is one of the projectes.
    '''
    resp = client.get('/projects')
    lst = resp.json()
    assert 'demo' in lst

### Tests for the regions entry point

def test_regions():
    '''
    The demo project has one region, named Test1
    '''
    resp = client.get('/regions/demo')
    dct = resp.json()
    assert dct['project'] == 'demo'
    assert dct['regions'] == ['Test1']

def test_regions_unknown():
    '''
    Test the regions entry point with an unknown project name
    '''
    resp = client.get('/regions/foo')
    dct = resp.json()
    assert dct['project'] == 'foo'
    assert dct['regions'] == None

### Tests for the barriers entry point
    
def test_barriers_demo():
    '''
    Test the barriers entry point
    '''
    resp = client.get('/barriers/demo')
    dct = resp.json()
    assert dct['project'] == 'demo'
    contents = dct['barriers'].split('\n')
    assert len(contents) == 7
    header = contents[0].split(',')
    assert header[0] == 'BARID' and header[-1] == 'NPROJ'
    gates = { line.split(',')[0] for line in contents[1:] }
    assert gates == {'A','B','C','D','E','F'}

def test_barriers_unknown():
    '''
    Test the barriers entry point with an unknown project name
    '''
    resp = client.get('/barriers/foo')
    dct = resp.json()
    assert dct['project'] == 'foo'
    assert dct['barriers'] == None

### Tests for the targets entry point
    
def test_targets_demo():
    '''Test the targets entry point with the demo project'''
    resp = client.get('/targets/demo')
    dct = resp.json()
    assert dct['project'] == 'demo'
    contents = dct['targets'].split('\n')
    assert len(contents) == 3
    header = contents[0].split(',')
    assert header[0] == 'abbrev' and header[-1] == 'infra'
    targets = { line.split(',')[0] for line in contents[1:] }
    assert targets == {'T1','T2'}

