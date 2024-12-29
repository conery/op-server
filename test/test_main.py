from importlib import import_module
import json

TestClient = import_module("fastapi.testclient").TestClient
main = import_module("app.main","ip-server")
app = main.app

#
# Unit tests for Tidegates web services
#

client = TestClient(app)

def test_projects():
    '''
    Make sure the demo project is one of the projectes.
    '''
    resp = client.get('/projects')
    lst = resp.json()
    assert 'demo' in lst

def test_html_demo():
    '''
    Fetch the welcome message for the demo project, look for key words
    '''
    resp = client.get('/html/demo/welcome.html')
    s = resp.json()
    assert s.count('<p>') == 11
    assert s.count('OptiPass') == 9
    assert s.count('FastAPI') == 1
  
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
   
def test_mapinfo_demo():
    '''
    Test the mapinfo entry point
    '''
    resp = client.get('/mapinfo/demo')
    dct = resp.json()
    info = json.loads(dct['mapinfo'])
    assert type(info) == dict
    assert info['map_type'] == 'StaticMap'
    assert info['map_file'] == 'Riverlands.png'

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

def test_colnames_demo():
    resp = client.get('colnames/demo')
    dct = resp.json()
    assert 'name' in dct
    assert dct['name'] is None
    assert 'files' in dct
    assert dct['files'] == ['colnames.csv']

def test_unknown_project():
    '''
    Each of the paths should check for an unknown project name
    '''
    paths = [
        '/html/foo/welcome.html',
        '/barriers/foo',
        '/mapinfo/foo',
        '/targets/foo',
        '/colnames/foo',
    ]
    for p in paths:
        resp = client.get(p)
        assert resp.status_code == 404

def test_unknown_files():
    '''
    Paths that fetch file should return 404 not found responses 
    '''
    paths = [
        '/html/demo/xxx.html',
        '/map/demo/xxx.png',
    ]
    for p in paths:
        resp = client.get(p)
        dct = resp.json()
        assert resp.status_code == 404
        assert 'not found' in dct['detail']

