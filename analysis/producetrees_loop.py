# Looper over producetrees.py


# external imports
import os
import sys
import six
import subprocess
import argparse

# local imports
thisdir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(thisdir)
import tools.condortools as ct
from producetrees import read_samplelist


if __name__ == '__main__':

    # read command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True, nargs='+',
      help='Input .root files, OR path to a .txt file listing input .root files (one per line)')
    parser.add_argument('-o', '--outputdir', required=True,
      help='Output directory')
    parser.add_argument('-r', '--runmode', default='local', choices=['local', 'condor'])
    args = parser.parse_args()

    # find input files
    input_files = []
    for el in args.input:
        if el.endswith('.root'): input_files.append(el)
        elif el.endswith('.txt'):
            input_files += read_samplelist(el)
    print(f'Found following input files ({len(input_files)}):')
    for f in input_files: print(f'  - {f}')

    # compile makentuples
    cmd_compile = "g++ -o makentuples makentuples.cpp `root-config --cflags --libs` -Wall"
    print('Compiling makentuples...')
    subprocess.check_call(cmd_compile, shell = True, stdout=None, stderr=None)

    # make output directory
    if os.path.exists(args.outputdir):
        msg = f'Output directory {args.outputdir} already exists; clean? (y/n)'
        print(msg)
        go = six.moves.input()
        if go!='y': sys.exit()
        os.system(f'rm {os.path.join(args.outputdir, "*")}')
    else: os.makedirs(args.outputdir)

    # make commands
    cmds = []
    for idx, input_file in enumerate(input_files):
        outputfile = os.path.join(args.outputdir, f'output_{idx}.root')
        cmd = 'python producetrees.py'
        cmd += f' -i {input_file}'
        cmd += f' -o {outputfile}'
        cmd += ' --no-compile'
        cmds.append(cmd)

    # run or submit commands
    if args.runmode == 'local':
        for cmd in cmds:
            print(cmd)
            os.system(cmd)
    elif args.runmode=='condor':
        env_script = os.path.abspath('../setup.sh')
        env_cmd = f'source {env_script}'
        ct.submitCommandsAsCondorCluster('cjob_producetrees', cmds,
          jobflavour='workday', conda_activate=env_cmd) 
