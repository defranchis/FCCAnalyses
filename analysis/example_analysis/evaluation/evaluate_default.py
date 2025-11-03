import os
import sys

thisdir = os.path.abspath(os.path.dirname(__file__))
topdir = os.path.abspath(os.path.join(thisdir, '../'))
sys.path.append(topdir)

import tools.condortools as ct
import tools.slurmtools as st


if __name__=='__main__':

    # settings
    model = os.path.abspath('models/output_20251101_ipfix/model.onnx')
    preprocess = model.replace('.onnx', '_preprocess.json')
    samples = [f'/eos/user/l/llambrec/aleph-data/ntuples_eventlevel_new/mc/output_qqb_[0,1,2,3,4,5].root']
    outputdir = 'output_test2'
    runmode = 'condor'

    cmds = []
    
    if True: 

        # set object and event selection
        objectselection = 'selections/selection_jets.json'
        eventselection = 'selections/selection.json'

        # make the command
        cmd = 'python evaluate.py'
        cmd += ' -s {}'.format(' '.join(samples))
        cmd += f' -m {model}'
        cmd += f' -p {preprocess}'
        cmd += f' -o {outputdir}'
        cmd += ' -t events'
        cmd += f' --objectselection {objectselection}'
        cmd += f' --eventselection {eventselection}'
        cmd += ' --translation translations/translations.json'
        cmds.append(cmd)

    # run commands
    if runmode=='local':
        for cmd in cmds:
            print(cmd)
            os.system(cmd)
    elif runmode=='condor':
        env_script = os.path.abspath('../../../setup.sh')
        env_cmd = f'source {env_script}'
        ct.submitCommandsAsCondorCluster('cjob_evaluate', cmds,
          jobflavour='workday', conda_activate=env_cmd)
    elif runmode=='slurm':
        env_cmds = ([
          'source /blue/avery/llambre1.brown/miniforge3/bin/activate',
          'conda activate weaver',
          f'cd {thisdir}'
        ])
        slurmscript = 'sjob_evaluate.sh'
        job_name = os.path.splitext(slurmscript)[0]
        st.submitCommandsAsSlurmJobs(cmds, script=slurmscript,
                job_name=job_name, env_cmds=env_cmds,
                memory='16G', time='05:00:00', constraint='el9')
