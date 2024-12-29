#
# REST server for OptiPass
#
# John Conery
# University of Oregon
# (conery@uoregon.edu)
#
# The top level file defines paths to static pages and RESTful 
# web services that provide data files and run the optimizer.

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Annotated

import logging
from rich.logging import RichHandler

from .optipass import run_optipass

def init():
    '''
    Define global variables used in the rest of the application:
    paths to static data and names of static data files, a list of 
    names of projects, a dictionary of region names for each project.
    '''

    global BARRIERS, BARRIER_FILE
    global MAPS, MAPINFO_FILE
    global TARGETS, TARGET_FILE, LAYOUT_FILE
    global COLNAMES, COLNAME_FILE
    global HTMLDIR, IMAGEDIR

    MAPS = 'static/maps'
    MAPINFO_FILE = 'mapinfo.json'

    BARRIERS = 'static/barriers'
    BARRIER_FILE = 'barriers.csv'

    TARGETS = 'static/targets'
    TARGET_FILE = 'targets.csv'
    LAYOUT_FILE = 'layout.txt'

    COLNAMES = 'static/colnames'
    COLNAME_FILE = 'colnames.csv'

    HTMLDIR = 'static/html'
    # IMAGEDIR = 'static/images'

    global project_names, region_names

    logging.basicConfig(
        level=logging.INFO,
        style='{',
        format='{message}',
        handlers = [RichHandler(markup=True, rich_tracebacks=True)],
    )

    project_names = [p.stem for p in Path(BARRIERS).iterdir()]
    logging.info(f'projects: {project_names}')

    region_names = { }
    for project in project_names:
        barrier_file = Path(BARRIERS) / project / BARRIER_FILE
        with open(barrier_file) as f:
            f.readline()     # skip the header
            region_names[project] = { rec.split(',')[1] for rec in f }
    logging.info(f'regions: {region_names}')

def read_text_file(project: str, area: str, fn: str) -> str:
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
    if not p.exists():
        raise FileNotFoundError(p)
    logging.info(f'reading text file: {p}')
    
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
async def projects() -> list[str]:
    '''
    Respond to GET requests of the form `/projects`.
    
    Returns:
        a list of the names of the projects (datasets) managed by the server.
    '''
    return project_names

###
# Return an HTML page for a project

@app.get("/html/{project}/{filename}")
async def html(project: str, filename: str) -> str:
    if project not in project_names:
        raise HTTPException(status_code=404, detail=f'html: unknown project: {project}')
    try:
        return read_text_file(project, HTMLDIR, filename)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f'file not found: {filename}')
    except Exception as err:
        raise HTTPException(status_code=500, detail=f'server error: {err}')

###
# Return the barrier file for a project.

@app.get("/barriers/{project}")
async def barriers(project: str) -> dict:
    '''
    Respond to GET requests of the form `/barriers/P` where P is a project name.

    Returns:
        the barrier data file for a project, as one long string.
    '''
    if project not in project_names:
        raise HTTPException(status_code=404, detail=f'barriers: unknown project: {project}')
    try:
        barriers = read_text_file(project, BARRIERS, BARRIER_FILE)
        return {'project': project, 'barriers': barriers}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f'file not found: {BARRIERS}/{BARRIER_FILE}')
    except Exception as err:
        raise HTTPException(status_code=500, detail=f'server error: {err}')

###
# Return the settings for displaying a map for a project.

@app.get("/mapinfo/{project}")
async def mapinfo(project: str) -> dict:
    '''
    Respond to GET requests of the form `/mapinfo/P` where P is a project name.

    Returns:
        a dictionary (JSON format) with settings for displaying the map for a project.
    '''
    if project not in project_names:
        raise HTTPException(status_code=404, detail=f'mapinfo: unknown project: {project}')
    try:
        info = read_text_file(project, MAPS, MAPINFO_FILE)
        return {'project': project, 'mapinfo': info}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f'file not found: {MAPS}/{MAPINFO_FILE}')
    except Exception as err:
        raise HTTPException(status_code=500, detail=f'server error: {err}')


###
# Return a static map (image file) for a project

@app.get("/map/{project}/{filename}")
async def map(project: str, filename: str) -> FileResponse:
    p = Path(MAPS) / project / filename
    if not p.exists():
        raise HTTPException(status_code=404, detail=f'map: file not found: {p}')
    try:
        resp = FileResponse(p)
        return resp
    except Exception as err:
        raise HTTPException(status_code=500, detail=f'server error: {err}')

###
# Return the restoration target descriptions

@app.get("/targets/{project}")
async def targets(project: str) -> dict:
    '''
    Respond to GET requests of the form `/targets/P` where P is a project name.

    Returns:
        the CSV file containing restoration target descriptions for a project
        and a plain text file containing the layout in the GUI
    '''
    if project not in project_names:
        raise HTTPException(status_code=404, detail=f'targets: unknown project: {project}')
    try:
        targets = read_text_file(project, TARGETS, TARGET_FILE)
        layout = read_text_file(project, TARGETS, LAYOUT_FILE)
        return {'project': project, 'targets': targets, 'layout': layout}
    except FileNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f'server error: {err}')

###
# Return a description of the mappings for a project -- either a single file
# named colnames.csv, or a directory with several CSV files.

@app.get("/colnames/{project}")
async def colnames(project: str) -> dict:
    '''
    Respond to GET requests of the form `/colnames/P` where P is a project name.

    Returns:
        a dictionary with two entries, the name of the mapping and the names of the colname files
    '''
    try:
        assert project in project_names, f'unknown project: {project}'
        cname_dir = Path(COLNAMES) / project
        cname_file = cname_dir / COLNAME_FILE
        if cname_file.is_file():
            return { 'name': None, 'files': [COLNAME_FILE]}
        elif cname_dir.is_dir():
            alts = list(cname_dir.iterdir())
            assert len(alts) == 1, f'colnames/{project} should have exactly one folder'
            alt_name = alts[0]
            assert alt_name.is_dir(), f'no directory for {alt_name}'
            cnames = [p.stem for p in alt_name.iterdir() if p.suffix == '.csv']
            return { 'name': alt_name.name, 'files': cnames }
        else:
            assert False, f'file not found: {cname_file}'
    except Exception as err:
        raise HTTPException(status_code=404, detail=f'colnames: {err}')


###
# Run OptiPass.  Load the target and barrier data for the project, pass those
# and other parameters to the function that runs OP.

@app.get("/optipass/{project}")
async def optipass(
    project: str, 
    regions: Annotated[list[str], Query()], 
    budgets: Annotated[list[int], Query()],
    targets: Annotated[list[str], Query()], 
    weights: Annotated[list[int] | None, Query()] = None, 
    mapping: Annotated[list[str] | None, Query()] = None,
    tempdir: Annotated[str | None, Query()] = None,
)-> dict:
    '''
    A GET request of the form `/optipass/project?ARGS` runs OptiPass using the parameter 
    values passed in the URL.
    
    Args:
        project:  the name of the project (used to make path to static files)
        regions:  comma-separated string of region names
        targets:  comma-separated string of 2-letter target IDs
        budgets:  a list with starting budget, increment, and count
        weights:  list of ints, one for each target (optional)
        mapping:  project-specific target names, e.g. `current` or `future` (optional)
        tempdir:  directory that has existing results (optional, used in testing)

    Returns:
        a dictionary with a status indicator and a token that can be used to fetch results.
    '''
    logging.debug(f'project {project}')
    logging.debug(f'regions {regions}')
    logging.debug(f'budgets {budgets}')
    logging.debug(f'targets {targets}')
    logging.debug(f'weights {weights}')
    logging.debug(f'mapping {mapping}')
    logging.debug(f'tempdir {tempdir}')

    try:
        assert project in project_names, f'unknown project: {project}'

        barrier_path = Path(BARRIERS) / project
        target_file = Path(TARGETS) / project / TARGET_FILE

        cname_dir = Path(COLNAMES) / project
        if mapping is None:
            cname_file = cname_dir / COLNAME_FILE
        else:
            cname_file = cname_dir / mapping[0] / f'{mapping[1]}.csv'
 
        summary, matrix = run_optipass(
            barrier_path, 
            target_file,
            cname_file,
            regions,
            budgets,
            targets, 
            weights,
            tempdir,
        )

        return {
            'summary': summary.to_csv(),
            'matrix': matrix.to_csv(),
        }

    except AssertionError as err:
        raise HTTPException(status_code=404, detail=f'optipass: {err}')
    except NotImplementedError:
        raise HTTPException(status_code=501, detail=f'OptiPassMain.exe not found')
    except RuntimeError as err:
        raise HTTPException(status_code=500, detail=str(err))
    except Exception as err:
        logging.exception(err)
        raise HTTPException(status_code=500, detail=f'server error: {err}')
