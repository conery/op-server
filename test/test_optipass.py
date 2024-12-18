#
# Unit tests for functions in the optipass module
#

from importlib import import_module

TestClient = import_module("fastapi.testclient").TestClient

main = import_module("app.main","ip-server")
app = main.app

op = import_module("app.optipass","ip-server")
OptiPass = op.OptiPass

import pytest

import os
import pandas as pd
from pathlib import Path

@pytest.fixture
def barriers():
    return Path(os.path.dirname(__file__)) / 'fixtures'

@pytest.fixture
def targets():
    return Path(os.path.dirname(__file__)) / 'fixtures' / 'targets.csv'

@pytest.fixture
def colnames():
    return Path(os.path.dirname(__file__)) / 'fixtures' / 'colnames.csv'


def test_OP(barriers, targets, colnames):
    '''
    Test the OP constructor. Make an instance, make sure all instance vars set
    to defaults.
    '''
    op = OptiPass(barriers, targets, colnames, [], [])
    assert len(op.barriers) == 0
    assert len(op.passability) == 0
    assert len(op.targets) == 0
    assert len(op.mapping) == 0
    assert op.weighted == False
    assert op.input_frame is None
    assert op.paths is None
    assert op.summary is None
    assert op.matrix is None
    assert op.tmpdir is None

def test_OP_with_existing_data(barriers, targets, colnames):
    '''
    Test the OP constructor when a path to existing data is passed
    '''
    p = Path(os.path.dirname(__file__)) / 'fixtures' / 'Example_1'
    op = OptiPass(barriers, targets, colnames, [], [], tmpdir =p)
    assert op.tmpdir == p

def test_region_and_target_names(barriers, targets, colnames):
    '''
    Verify region and target names
    '''
    op = OptiPass(barriers, targets, colnames, ['Trident', 'Red Fork'], ['T1','T2'])
    assert len(op.barriers) == 6
    assert len(op.passability) == 6
    assert len(op.targets) == 2
    assert len(op.mapping) == 2
    assert list(op.mapping.index) == list(op.targets.index)

def test_one_region_and_one_target(barriers, targets, colnames):
    '''
    Check barrier frame when only one region and one target is used
    '''
    op = OptiPass(barriers, targets, colnames, ['Trident'], ['T1'])
    assert len(op.barriers) == 4
    assert len(op.passability) == 4
    assert len(op.targets) == 1
    assert len(op.mapping) == 1
    assert list(op.mapping.index) == list(op.targets.index)

def test_one_target_input(barriers, targets, colnames):
    '''
    Make an input file for single target.
    '''
    op = OptiPass(barriers, targets, colnames, ['Trident', 'Red Fork'], ['T1'])
    op.create_input_frame()
    df = op.input_frame
    assert len(df) == 6
    assert list(df.columns) == ['ID', 'REG', 'FOCUS', 'DSID', 'HAB_T1', 'PRE_T1', 'NPROJ', 'ACTION', 'COST', 'POST_T1']
    assert df.FOCUS.sum() == 6
    assert df.ACTION.sum() == 0
    assert df.COST.sum() == 590000

def test_two_target_input(barriers, targets, colnames):
    '''
    Make an input file for two targets
   '''
    op = OptiPass(barriers, targets, colnames, ['Trident', 'Red Fork'], ['T1','T2'])
    op.create_input_frame()
    df = op.input_frame
    assert len(df) == 6
    assert list(df.columns) == ['ID', 'REG', 'FOCUS', 'DSID', 'HAB_T1', 'HAB_T2', 'PRE_T1', 'PRE_T2', 'NPROJ', 'ACTION', 'COST', 'POST_T1', 'POST_T2']
    assert df.FOCUS.sum() == 6
    assert df.ACTION.sum() == 0
    assert df.COST.sum() == 590000

def test_unweighted(barriers, targets, colnames):
    '''
    Make sure weights are initialized to 1s, one per target
    '''
    op = OptiPass(barriers, targets, colnames, ['Trident', 'Red Fork'], ['T1','T2'])
    assert op.weights == [1,1]

def test_weighted(barriers, targets, colnames):
    '''
    Make sure weights are initialized with specified settings
   '''
    op = OptiPass(barriers, targets, colnames, ['Trident', 'Red Fork'], ['T1','T2'], weights=[1,2])
    assert op.weights == [1,2]

def test_paths(barriers, targets, colnames):
    '''
    Verify the paths downstream from gates
    '''
    op = OptiPass(barriers, targets, colnames, ['Trident', 'Red Fork'], ['T1'])
    op.create_input_frame()
    op.create_paths()
    assert op.paths['F'] == ['F','D','A']
    assert op.paths['C'] == ['C','B','A']
    assert op.paths['B'] == ['B','A']
    assert op.paths['A'] == ['A']

def test_output_parser_one_target(barriers, targets, colnames):
    '''
    Parse an output file with only one target
    '''
    p = Path(os.path.dirname(__file__)) / 'fixtures' / 'Example_1' / 'output_5.txt'
    cols = { x: [] for x in ['budget', 'habitat', 'gates']}
    op = OptiPass(barriers, targets, colnames, ['Test1'], ['T1'])
    op.parse_output(p, cols)
    assert len(cols['budget']) == 1 and round(cols['budget'][0]) == 500000
    assert len(cols['habitat']) == 1 and round(cols['habitat'][0], 2) == 8.52
    assert len(cols['gates']) == 1 and cols['gates'][0] == ['A', 'B', 'C', 'F']

def test_output_parser_two_targets(barriers, targets, colnames):
    '''
    Parse an output file with two targets
   '''
    p = Path(os.path.dirname(__file__)) / 'fixtures' / 'Example_4' / 'output_5.txt'
    cols = { x: [] for x in ['budget', 'habitat', 'gates']}
    op = OptiPass(barriers, targets, colnames, ['Trident', 'Red Fork'], ['T1','T2'])
    op.parse_output(p, cols)
    assert len(cols['budget']) == 1 and round(cols['budget'][0]) == 500000
    assert len(cols['habitat']) == 1 and round(cols['habitat'][0], 3) == 32.936
    assert len(cols['gates']) == 1 and cols['gates'][0] == ['A', 'B', 'C', 'F']

def test_example_1(barriers, targets, colnames):
    '''
    Collect all the results for Example 1 from the OptiPass User Manual.
    '''
    p = Path(os.path.dirname(__file__)) / 'fixtures' / 'Example_1'
    op = OptiPass(barriers, targets, colnames, ['Trident', 'Red Fork'], ['T1'], tmpdir=p)
    op.create_input_frame()
    op.create_paths()
    op.collect_results()

    assert type(op.summary) == pd.DataFrame
    assert len(op.summary) == 6
    assert round(op.summary.budget.sum()) == 1500000
    assert round(op.summary.habitat.sum(),2) == 23.30

    budget_cols = [col for col in op.matrix.columns if isinstance(col,int)]
    assert budget_cols == list(op.summary.budget)

    # these comprehensions make lists of budgets where a specified gate was selected,
    # e.g. gate A is in the $400K and $500K budgets and D is never selected.
    assert [b for b in op.matrix.columns if isinstance(b, int) and op.matrix.loc['A',b]] == [400000,500000]
    assert [b for b in op.matrix.columns if isinstance(b, int) and op.matrix.loc['D',b]] == [ ]
    assert [b for b in op.matrix.columns if isinstance(b, int) and op.matrix.loc['E',b]] == [100000,300000]

    assert list(op.matrix['count']) == [2,4,3,0,2,1]   # number of times each gate is part of a solution

def test_example_4(barriers, targets, colnames):
    '''
    Same as test_example_1, but using Example 4, which has two restoration targets.
    '''
    p = Path(os.path.dirname(__file__)) / 'fixtures' / 'Example_4'
    op = OptiPass(barriers, targets, colnames, ['Trident', 'Red Fork'], ['T1','T2'], tmpdir=p)
    op.create_input_frame()
    op.create_paths()
    op.collect_results()
    
    assert type(op.summary) == pd.DataFrame
    assert len(op.summary) == 6
    assert round(op.summary.budget.sum()) == 1500000
    assert round(op.summary.habitat.sum(),2) == 95.21

    # using two targets does not change the gate selections
    assert [b for b in op.matrix.columns if isinstance(b, int) and op.matrix.loc['A',b]] == [400000,500000]
    assert [b for b in op.matrix.columns if isinstance(b, int) and op.matrix.loc['D',b]] == [ ]
    assert [b for b in op.matrix.columns if isinstance(b, int) and op.matrix.loc['E',b]] == [100000,300000]

    assert list(op.matrix['count']) == [2,4,3,0,2,1]   # number of times each gate is part of a solution

def test_potential_habitat_1(barriers, targets, colnames):
    '''
    Test the method that computes potential habitat, using the results 
    genearated for Example 1 in the OptiPass manual (Box 9).
    '''
    p = Path(os.path.dirname(__file__)) / 'fixtures' / 'Example_1'
    op = OptiPass(barriers, targets, colnames, ['Trident', 'Red Fork'], ['T1'], tmpdir=p)
    op.create_input_frame()
    op.create_paths()
    op.collect_results()

    m = op.summary
    assert len(m) == 6
    assert 'T1' in m.columns and 'wph' in m.columns
    assert round(m.wph[0],3) == 1.238      # PTNL_HABITAT at $0
    assert round(m.wph[5],3) == 8.520      # PTNL_HABITAT at $500K

def test_potential_habitat_4(barriers, targets, colnames):
    '''
    Same as test_potential_habitat_1, but using Example 4, with two restoration targets
    weighted differently (Box 11)
   '''
    p = Path(os.path.dirname(__file__)) / 'fixtures' / 'Example_4'
    op = OptiPass(barriers, targets, colnames, ['Trident', 'Red Fork'], ['T1','T2'], weights=[3,1], tmpdir=p)
    op.create_input_frame()
    op.create_paths()
    op.collect_results()

    m = op.summary
    assert len(m) == 6
    assert 'T1' in m.columns and 'T2' in m.columns and 'wph' in m.columns
    assert round(m.wph[0],3) == 5.491
    assert round(m.wph[4],3) == 21.084    # PTNL_HABITAT at $400K
