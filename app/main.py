#
# Web application for the Tide Gate Optimization Tool
#
# John Conery
# University of Oregon
# (conery@uoregon.edu)
#
# The top level file defines paths to static pages, the web app (implemented
# in Panel), and web services that provide data files and run the optimizer.

from fastapi import FastAPI, Response
from pathlib import Path

# from .optipass import run_optipass

app = FastAPI()

###
# Global variables.
#
# A project defines which data set to use.  Valid project names are the
# names of subfolders under static/barriers.
#
# Region names are the names of rivers in a barrier file for a project.
#
# Target files have descriptions of restoration targets; the fields needed
# here are the names of columns that have pre- and post-restoration passage
# values

BARRIERS = 'static/barriers'
BARRIER_FILE = 'barriers.csv'

project_names = [p.stem for p in Path(BARRIERS).iterdir()]

region_names = { }
for project in project_names:
    barrier_file = Path(BARRIERS) / project / BARRIER_FILE
    with open(barrier_file) as f:
        f.readline()     # skip the header
        region_names[project] = { rec.split(',')[1] for rec in f }

TARGETS = 'static/targets'

target_files = { }
for project in project_names:
    target_dir = Path(TARGETS) / project
    target_files[project] = [ f.parts[-1] for f in target_dir.glob('*.csv') ]

MAPS = 'static/maps'

map_files = { }
for project in project_names:
    map_dir = Path(MAPS) / project
    map_files[project] = [ f.parts[-1] for f in map_dir.glob('*.csv') ]

###
# Utilities for reading data files for a project

def target_file_name(project, climate):
    if climate is None:
        return Path(TARGETS) / project / target_files[project][0]
    elif climate+'.csv' in target_files[project]:
        return Path(TARGETS) / project / climate+'.csv'
    else:
        return ''
    
def read_csv_file(project, area, fn):
    p = Path(area) / project / fn
    with open(p) as f:
        return f.read().rstrip()
    
def read_target_file(project, climate):
    if climate is None:
        targets = read_csv_file(project, TARGETS, target_files[project][0])
    elif climate+'.csv' in target_files[project]:
        targets = read_csv_file(project, TARGETS, climate+'.csv')
    else:
        targets = None
    return targets

###
# Return a list of project names.
        
@app.get("/projects")
async def projects():
    '''Return a list of project names (dataset names)'''
    return project_names

###
# Return a list of regions for a project.
        
@app.get("/regions/{project}")
async def regions(project: str):
    '''Return a list of regions (river names) for a project'''
    return {'project': project, 'regions': region_names.get(project)}

###
# Return the barrier file for a project.

@app.get("/barriers/{project}")
async def barriers(project: str):
    '''Return barrier data for a project'''
    if project in project_names:
        barriers = read_csv_file(project, BARRIERS, BARRIER_FILE)
    else:
        barriers = None
    return {'project': project, 'barriers': barriers}

###
# Return the restoration target descriptions

@app.get("/targets/{project}")
async def targets(project: str, climate: str | None = None):
    '''Return restoration target descriptions for a project'''

    if project in project_names:
        targets = read_target_file(project, climate)

    return {'project': project, 'targets': targets}

###
# Run OptiPass.  Load the target and barrier data for the project, pass those
# and other parameters to the function that runs OP.

@app.get("/optipass/{project}")
async def optipass(project: str, regions: str, targets: str, bmin: int, bcount: int, bdelta: int, climate: str | None = None, weights: str | None = None):
    '''
    Run OptiPass for a set of budget values.  Parameters:
    - **project**:  the name of the project (path to target and barrier files)
    - **regions**:  comma-separated string of region names
    - **targets**:  comma-separated string of 2-letter target IDs
    - **weights**:  comma-separated list of ints, one for each target (optional)
    - **bmin**:  first budget value
    - **bcount**:  number of budgets (_i.e._ number of times to run OptiPass)
    - **bdelta**:  distance between budget values (_i.e._ step size)
    - **climate**:  climate scenario, either `current` or `future` (optional)

    Returns a token that can be used to fetch results (output tables and plots).
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
    '''Return output tables from a previous run'''

    try:
        with open(Path(OUTPUTS) / token / 'matrix.txt') as f:
            matrix = f.read()
        with open(Path(OUTPUTS) / token / 'summary.txt') as f:
            summary = f.read()
        result = {'status': 'ok', 'matrix': matrix, 'summary': summary}
    except Exception as err:
        result = {'status': 'fail', 'message': f'error reading results for {token}: {str(err)}'}

    return result
