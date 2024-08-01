#
# REST server for OptiPass
#
# John Conery
# University of Oregon
# (conery@uoregon.edu)
#
# The top level file defines paths to static pages and RESTful 
# web services that provide data files and run the optimizer.

from fastapi import FastAPI, Response
from pathlib import Path

from .optipass import run_optipass

def init():
    '''
    Define global variables used in the rest of the application:
    paths to static data and names of static data files, a list of 
    names of projects, a dictionary of region names for each project.
    '''

    global BARRIERS, BARRIER_FILE, MAPINFO_FILE, TARGETS, TARGET_FILE, COLNAMES, COLNAME_FILE

    BARRIERS = 'static/barriers'
    BARRIER_FILE = 'barriers.csv'
    MAPINFO_FILE = 'mapinfo.json'

    TARGETS = 'static/targets'
    TARGET_FILE = 'targets.csv'

    COLNAMES = 'static/colnames'
    COLNAME_FILE = 'colnames.csv'

    global project_names, region_names

    project_names = [p.stem for p in Path(BARRIERS).iterdir()]

    region_names = { }
    for project in project_names:
        barrier_file = Path(BARRIERS) / project / BARRIER_FILE
        with open(barrier_file) as f:
            f.readline()     # skip the header
            region_names[project] = { rec.split(',')[1] for rec in f }
def read_text_file(project, area, fn):
    '''
    Read a text file from one of the static subdirectories.

    Args:
        project:  the project name
        area:  the data area (barriers, targets, colnames)
        fn:  the name of the file within the data area

    Returns:
        the contents of the file, as a single string
    '''
    p = Path(area) / project / fn
    with open(p) as f:
        return f.read().rstrip()
    
###
#
# Top level program -- initialize the global variables and start the app
#

init()
app = FastAPI()
    
###
# Return a list of project names.
        
@app.get("/projects")
async def projects():
    '''
    Respond to GET requests of the form `/projects`.
    
    Returns:
        a list of the names of the projects (datasets) managed by the server.
    '''
    return project_names

###
# Return a list of regions for a project.
        
@app.get("/regions/{project}")
async def regions(project: str):
    '''
    Respond to GET requests of the form `/regions/P` where P is a project name.

    Returns:
        a list of regions (river names) for a project, taken from the second column of the barrier file for the project.
    '''
    return {'project': project, 'regions': region_names.get(project)}

###
# Return the barrier file for a project.

@app.get("/barriers/{project}")
async def barriers(project: str):
    '''
    Respond to GET requests of the form `/barriers/P` where P is a project name.

    Returns:
        the barrier data file for a project, as one long string.
    '''
    if project in project_names:
        barriers = read_text_file(project, BARRIERS, BARRIER_FILE)
    else:
        barriers = None
    return {'project': project, 'barriers': barriers}

###
# Return the settings for displaying a map for a project.

@app.get("/mapinfo/{project}")
async def mapinfo(project: str):
    '''
    Respond to GET requests of the form `/mapinfo/P` where P is a project name.

    Returns:
        a dictionary (JSON format) with settings for displaying the map for a project.
    '''
    if project in project_names:
        info = read_text_file(project, BARRIERS, MAPINFO_FILE)
    else:
        info = None
    return {'project': project, 'mapinfo': info}

###
# Return the restoration target descriptions

@app.get("/targets/{project}")
async def targets(project: str):
    '''
    Respond to GET requests of the form `/targets/P` where P is a project name.

    Returns:
        the CSV file containing restoration target descriptions for a project
    '''

    if project in project_names:
        targets = read_text_file(project, TARGETS, TARGET_FILE)
    else:
        targets = None
    return {'project': project, 'targets': targets}

###
# Return a description of the mappings for a project -- either a single file
# named colnames.csv, or a directory with several CSV files.

@app.get("/colnames/{project}")
async def colnames(project: str):
    '''
    Respond to GET requests of the form `/colnames/P` where P is a project name.

    Returns:
        a dictionary with two entries, the name of the mapping and the names of the colname files
    '''
    if project not in project_names:
        return None
    cname_dir = Path(COLNAMES) / project
    if not cname_dir.is_dir():
        return None
    cname_file = cname_dir / COLNAME_FILE
    if cname_file.is_file():
        return { 'name': None, 'files': [COLNAME_FILE]}
    if not cname_dir.is_dir():
        return None
    alts = list(cname_dir.iterdir())
    if len(alts) != 1:
        return None
    alt_name = alts[0]
    if not alt_name.is_dir():
        return None
    cnames = [p.stem for p in alt_name.iterdir() if p.suffix == '.csv']
    return { 'name': alt_name.name, 'files': cnames }

###
# Run OptiPass.  Load the target and barrier data for the project, pass those
# and other parameters to the function that runs OP.

@app.get("/optipass/{project}")
async def optipass(project: str, regions: str, targets: str, bmin: int, bcount: int, bdelta: int, colnames: str | None = None, weights: str | None = None):
    '''
    A GET request of the form `/optipass/P?ARGS` runs OptiPass using the parameter values passed in the URL.
    
    Args:
        project:  the name of the project (path to target and barrier files)
        regions:  comma-separated string of region names
        targets:  comma-separated string of 2-letter target IDs
        weights:  comma-separated list of ints, one for each target (optional)
        bmin:  first budget value
        bcount:  number of budgets (_i.e._ number of times to run OptiPass)
        bdelta:  distance between budget values (_i.e._ step size)
        colnames:  climate scenario, either `current` or `future` (optional)

    Returns:
        a dictionary with a status indicator and a token that can be used to fetch results.
    '''

    try:
        assert project in project_names, f'unknown project: {project}'
        barrier_file = Path(BARRIERS) / project / BARRIER_FILE
        target_file = target_file_name(project, climate)
        assert target_file, f'no targets in project "{project}" for climate: "{climate}"'
        region_list = regions.split(',')
        assert all(r in region_names[project] for r in region_list), f'unknown region in {regions}'
        target_list = targets.split(',')
        token = run_optipass(barrier_file, target_file, region_list, target_list, weights, bmin, bcount, bdelta)
        status = 'ok'
    except AssertionError as err:
        status = 'fail'
        token = str(err)

    return {'status': status, 'token': token}

###
# Return the output tables from a previous run.  The parameter is a token
# returns from that call that ran OptiPass -- its' the name of the directory
# that has the tables.

OUTPUTS = 'tmp'

@app.get("/tables/{token}")
async def tables(token: str):
    '''
    Respond to a GET request of the form `/tables/T` where T is a token returned by an earlier call to `optipass`.

    Returns:
        a dictionary with a status code and two output tables
    '''

    try:
        with open(Path(OUTPUTS) / token / 'matrix.txt') as f:
            matrix = f.read()
        with open(Path(OUTPUTS) / token / 'summary.txt') as f:
            summary = f.read()
        result = {'status': 'ok', 'matrix': matrix, 'summary': summary}
    except Exception as err:
        result = {'status': 'fail', 'message': f'error reading results for {token}: {str(err)}'}

    return result

