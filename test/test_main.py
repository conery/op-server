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
    assert header[0] == 'ID' and header[-1] == 'comment'
    gates = { line.split(',')[0] for line in contents[1:] }
    assert gates == {'A','B','C','D','E','F'}

def test_barriers_unknown():
    '''
    Test the barriers entry point with an unknown project name
    '''
    resp = client.get('/barriers/foo')
    assert resp.status_code == 404

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
    layout = dct['layout']
    assert layout == 'T1 T2'

def test_targets_unknown():
    '''
    Test the targets entry point with an unknown project name
    '''
    resp = client.get('/targets/foo')
    assert resp.status_code == 404

### Tests for the colnames entry point

def test_colnames_demo():
    resp = client.get('colnames/demo')
    dct = resp.json()
    assert 'name' in dct
    assert dct['name'] is None
    assert 'files' in dct
    assert dct['files'] == ['colnames.csv']

def test_colnames_unknown():
    '''
    Test the colnames entry point with an unknown project name
    '''
    resp = client.get('/colnames/foo')
    assert resp.status_code == 404
