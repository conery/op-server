#
# Interface to OptiPass.exe (command line version of OptiPass)
#

from math import prod
import networkx as nx
import numpy as np
import os
import pandas as pd
from pathlib import Path
import platform
import subprocess
import tempfile

def optipass_is_installed():
    '''
    Make sure OptiPass is installed.

    Returns:
       True if OptiPass is installed and this host can run it.
    '''
    return Path('./bin/OptiPassMain.exe') and ((platform.system() == 'Windows') or os.environ.get('WINEARCH'))

def run_optipass(
        barrier_path: str, 
        target_file: str,
        mapping_file: str, 
        regions: list[str],
        budgets: list[int],
        targets: list[str], 
        weights: list[int],
    ):
    '''
    Run OptiPass using the specified arguments.  Instantiates an OP object
    with paths to data files, calls methods that create the input file,
    run the optimizer, and gather the results.

    Arguments:
        barrier_path: name of directory with CSVs files for tide gate data
        target_file: name of a CSV file with restoration target descriptions
        mapping_file: name of CSV file with barrier passabilities
        regions: a list of geographic regions (river names) to use
        budgets: a list with starting budget, budget increment, and number of budgets
        targets: a list of IDs of targets to use
        weights: a list of target weights

    Returns:
        a token that can be used to retrieve results
    '''
    op = OptiPass(barrier_path, target_file, mapping_file, regions, targets, weights)
    op.create_input_frame()
    op.create_paths()
    op.run(*budgets)
    op.collect_results()
    op.save_results()

    return Path(op.tempdir).stem

class OptiPass:
    '''
    The entry point that runs OptiPass (OP) has parameters that specify how many 
    budget levels to explore.  We need to run OptiPass.exe once for each budget
    level, then collect the results.

    The general workflow is:
    * create an instance of this class, passing the constructor the parameter
      values for the regions, targets, and budget levels
    * call a method to generate the input file (called a "barrier file" in the
      OP documentation) that will be read as input each time OP runs
    * call the method that finds downstream barriers
    * call the method that runs OP
    * collect the results from the output files
    * compute the estimated benefits at each budget level
    * generate the output tables and plots

    All of the intermediate data needed for these steps is saved in instance vars
    of the object.
    '''

    def __init__(self, barriers, tfile, mfile, rlist, tlist, weights=None, tmpdir=True):
        '''
        Instantiate a new OP object, creating the temp directory where OP will save
        results (unless tmpdir is False).

        Arguments:
          barriers: folder with barrier definitions
          tfile: name of file with target descriptions
          mfile: name of file with target benefits
          rlist: list of region names
          tlist: list of target names
          weights:  list of target weights (optional)
          tmpdir:  path to output files (optional, used by unit tests)
        '''
        self.tempdir = tempfile.mkdtemp(prefix='op', dir='tmp') if tmpdir else 'tmp'

        bf = pd.read_csv(barriers/'barriers.csv')
        self.barriers = bf[bf.region.isin(rlist)]

        pf = pd.read_csv(barriers/'passability.csv')
        self.passability = pf[pf.ID.isin(self.barriers.ID)]

        tf = pd.read_csv(tfile).set_index('abbrev')
        assert all(t in tf.index for t in tlist), f'unknown target name in {tlist}'
        self.targets = tf[tf.index.isin(tlist)]

        mf = pd.read_csv(mfile).set_index('abbrev')
        self.mapping = mf[mf.index.isin(tlist)]

        self.set_target_weights(weights)
       
        self.input_frame = None
        self.paths = None
        self.summary = None
        self.matrix = None

    def create_input_frame(self):
        '''
        Build a data frame that has the rows that will be passed to OptiPass. This
        frame is basically a subset of the columns of the barrier frame, using column
        names defined in the targets frame.
        '''

        # Initialize the output frame (df) with the ID and region columns 
        # from the data set 
        df = self.barriers[['ID','region']]
        header = ['ID','REG']

        # The FOCUS column is all 1's
        df = pd.concat([df, pd.Series(np.ones(len(self.barriers)), name='FOCUS', dtype=int)], axis=1)
        header.append('FOCUS')

        # Copy the downstream ID column
        df = pd.concat([df, self.barriers['DSID']], axis=1)
        header.append('DSID')

        # Add habitat column for each target.  The name of the column to copy is
        # in the mapping frame, the column to copy is in the passability frame
        for t in self.targets.index:
            col = self.passability[self.mapping.loc[t,'habitat']]
            df = pd.concat([df,col], axis=1)
            header.append('HAB_'+t)

        # Same, but for pre-mitigation passage values
        for t in self.targets.index:
            col = self.passability[self.mapping.loc[t,'prepass']]
            df = pd.concat([df,col], axis=1)
            header.append('PRE_'+t)

        # Copy the NPROJ column (1 if a gate is used, 0 if not)
        df = pd.concat([df, self.barriers['NPROJ']], axis=1)
        header.append('NPROJ')

        # The ACTION column is always all 0 (we consider only one scenario)
        df = pd.concat([df, pd.Series(np.zeros(len(self.barriers)), name='ACTION', dtype=int)], axis=1)
        header.append('ACTION')

        # Copy the cost to fix a gate
        df = pd.concat([df, self.barriers['cost']], axis=1)
        header += ['COST']

        # Same logic as above, copy the post-mitigation passage for each target
        for t in self.targets.index:
            col = self.passability[self.mapping.loc[t,'postpass']]
            df = pd.concat([df,col], axis=1)
            header.append('POST_'+t)

        # All done making the data -- use the new column headers and save the frame
        df.columns = header
        self.input_frame = df

    def create_paths(self):
        '''
        Create paths downstream from each gate (the paths will be 
        used to compute cumulative passability)
        '''
        df = self.input_frame

        G = nx.from_pandas_edgelist(
            df[df.DSID.notnull()], 
            source='ID', 
            target='DSID', 
            create_using=nx.DiGraph
        )

        for x in df[df.DSID.isnull()].ID:
            G.add_node(x)
        self.paths = { n: self._path_from(n,G) for n in G.nodes }

    def _path_from(self, x, graph):
        '''
        Helper function used to create paths -- return a list of nodes in the path 
        from `x` to a downstream barrier that has no descendants.
        '''
        return [x] + [child for _, child in nx.dfs_edges(graph,x)]

    def set_target_weights(self, weights):
        '''
        Create the target weight values that will be passed on the command line when
        OptiPass is run
        '''
        if weights:
            self.weights = weights
            self.weighted = True
        else:
            self.weights = [1] * len(self.targets)
            self.weighted = False

    def run(self, bmin, bdelta, bcount):
        '''
        Create a folder to run OptiPass in, write the barrier file, run OP
        for each budget level.
        '''
        barrier_file = Path(self.tempdir) / 'input.txt'
        self.input_frame.to_csv(barrier_file, index=False, sep='\t', lineterminator=os.linesep, na_rep='NA')

        template = 'bin\\OptiPassMain.exe -f {bf} -o {of} -b {n}'

        budget = bmin
        for i in range(bcount):
            outfile = Path(self.tempdir) / f'output_{i}.txt'
            cmnd = template.format(bf=barrier_file, of=outfile, n=budget)
            if (num_targets := len(self.targets)) > 1:
                cmnd += ' -t {}'.format(num_targets)
                cmnd += ' -w ' + ', '.join([str(n) for n in self.weights])
                res = subprocess.run(cmnd, shell=True, capture_output=True)
            # print(cmnd)
            budget += bdelta

    def collect_results(self, tmpdir=None):
        '''
        OptiPass makes one output file for each budget level.  Iterate
        over those files to gather results into a data frame.  
        
        Normally tmpdir is None, and the method gets data files from the directory
        created by the constructor, but unit tests pass the name of a
        directory that has test fixtures.
        '''
        cols = { x: [] for x in ['budget', 'habitat', 'gates']}
        output_dir = Path(tmpdir) if tmpdir else Path(self.tempdir)
        for fn in sorted(output_dir.glob('output_*.txt')):
            self.parse_output(fn, cols)
        self.summary = pd.DataFrame(cols)
        
        dct = {}
        for i in range(len(self.summary)):
            b = int(self.summary.budget[i])
            dct[b] = [ 1 if g in self.summary.gates[i] else 0 for g in self.input_frame.ID]
        self.matrix = pd.DataFrame(dct, index=self.input_frame.ID)
        self.matrix['count'] = self.matrix.sum(axis=1)
        self.add_potential_habitat()

    def save_results(self):
        matrix_file = Path(self.tempdir) / 'matrix.txt'
        self.matrix.to_csv(matrix_file, lineterminator=os.linesep, na_rep='NA')

        summary_file = Path(self.tempdir) / 'summary.txt'
        self.summary.to_csv(summary_file, index=False, lineterminator=os.linesep, na_rep='NA')

    def parse_output(self, fn, dct):
        '''
        Parse an output file, appending results to the lists in dct.  We need to 
        handle two different formats, depending on whether there was one target 
        or more than one.
        '''

        def parse_header_line(line, tag):
            tokens = line.strip().split()
            if not tokens[0].startswith(tag):
                return None
            return tokens[1]

        with open(fn) as f:
            amount = parse_header_line(f.readline(), 'BUDGET')
            dct['budget'].append(float(amount))
            if parse_header_line(f.readline(), 'STATUS') == 'NO_SOLN':
                raise RuntimeError('No solution')
            f.readline()                        # skip OPTGAP
            line = f.readline()
            if line.startswith('PTNL'):
                # this file has only one target
                hab = parse_header_line(line, 'PTNL_HABITAT')
                dct['habitat'].append(float(hab))
                f.readline()                    # skip NETGAIN
            else:
                # multiple targets; skip past individual weights and targets
                while line := f.readline():
                    if line.startswith('WT_PTNL_HAB'):
                        break
                hab = parse_header_line(line, 'WT_PTNL_HAB')
                dct['habitat'].append(float(hab))
                f.readline()                    # skip WT_NETGAIN
            f.readline()                        # skip blank line
            f.readline()                        # skip header
            lst = []
            while line := f.readline():
                name, action = line.strip().split()
                if action == '1':
                    lst.append(name)
            dct['gates'].append(lst)

    def add_potential_habitat(self):
        '''
        Compute the potential habitat available after restoration, using
        the original unscaled habitat values.  Adds a new table named summary:
        one column for each target, showing the potential habitat gain at each 
        budget level, then the weighted potential habitat over all targets, and
        finally the net gain.
        '''
        # make a copy of the barrier data with NaN replaced by 0s and using the
        # barrier ID as the index
        df = self.barriers.fillna(0).set_index('BARID')
        wph = np.zeros(len(self.summary))
        for i in range(len(self.targets)):
            t = self.targets.iloc[i]
            cp = self._ah(t, df)
            wph += (self.weights[i] * cp)
            col = pd.DataFrame({self.targets.index[i]: cp})
            self.summary = pd.concat([self.summary, col], axis=1)
            gain = self._gain(self.targets.index[i], t, df)
            self.matrix = pd.concat([self.matrix, df[t.unscaled], gain], axis=1)
        self.summary = pd.concat([self.summary, pd.DataFrame({'wph': wph})], axis = 1)
    #    self.summary['netgain'] = self.summary.habitat - self.summary.habitat[0]
 
    # Private method: compute the available habitat for a target, in the form of
    # a vector of habitat values for each budget level

    def _ah(self, target, data):
        budgets = self.summary.budget
        m = self.matrix
        res = np.zeros(len(budgets))
        for i in range(len(res)):
            action = m.iloc[:,i]
            pvec = data[target.postpass].where(action == 1, data[target.prepass])
            habitat = data[target.unscaled]
            res[i] = sum(prod(pvec[x] for x in self.paths[b]) * habitat[b] for b in m.index)
        return res
    
    def _gain(self, colname, target, data):
        col = (data[target.postpass] - data[target.prepass]) * data[target.unscaled]
        return col.to_frame(name=f'GAIN_{colname}')

