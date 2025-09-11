import sys
import os
import multiprocessing as mp
import subprocess
from subprocess import Popen,PIPE
from datetime import date
import time


def ntuplizer(cmd_stagentuple_train, cmd_stagentuple_test, f_stdout, f_stderr):

    start2_time = time.time()
    subprocess.check_call(cmd_stagentuple_train, shell = True, stdout=f_stdout, stderr=f_stderr)
    subprocess.check_call(cmd_stagentuple_test, shell = True, stdout=f_stdout, stderr=f_stderr)
    end2_time = time.time()
    f_stdout.write("Stage_ntuple time (run only): {} \n".format(end2_time - end1_time))


if __name__ == '__main__':

    # set input and output paths
    inDIR='/eos/experiment/fcc/ee/generation/DelphesEvents/pre_fall2022_training/IDEA/'
    outDIR = "output_test/"

    # make output directory
    if not os.path.exists(outDIR): os.makedirs(outDIR)

    # set total number of events
    N = 100
    
    # set fraction used for training
    frac_split = 0.9
    N_split = int(frac_split * N)

    # set samples to use
    #samples = [ 'bb', 'cc', 'ss', 'gg', 'qq']
    samples = ['bb']
    mods = ['train', 'test']

    # setup of the environment
    cmd_compile = "g++ -o makentuples makentuples.cpp `root-config --cflags --libs` -Wall"
    print('Compiling makentuples...')
    subprocess.check_call(cmd_compile, shell = True, stdout=None, stderr=None)

    # create basic command for stage 1
    cmdbase_stage1 = 'fccanalysis run analysis.py'
    cmdbase_stage1 += ' --nevents {}'.format(N)
    opt1_out = " --output {}stage1_ee_ZH_vvCLASS.root ".format(outDIR)
    opt1_in = " --files-list {}p8_ee_ZH_Znunu_HCLASS_ecm240/*.root ".format(inDIR)
    cmd_stage1 = cmdbase_stage1 + opt1_out + opt1_in
    
    cmdbase_stagentuple = "./makentuples DIRstage1_ee_ZH_vvCLASS.root  DIRntuple_MOD_ee_ZH_vvCLASS.root "
    cmd_stagentuple = cmdbase_stagentuple.replace('DIR', outDIR)

    # create files storing stdout and stderr
    list_stdout = [open(outDIR + "{}_stdout.txt".format(sample), "w") for sample in samples]
    list_stderr = [open(outDIR + "{}_stderr.txt".format(sample), "w") for sample in samples]

    # RUN STAGE 1
    for i,sample in enumerate(samples):

        # make command
        if(sample == 'qq'):
            cmd_stage1_f = (cmdbase_stage1
                              + opt1_out.replace('CLASS', 'qq')
                              + " --files-list {}p8_ee_ZH_Znunu_Huu_ecm240/*.root".format(inDIR)
                              + " {}p8_ee_ZH_Znunu_Hdd_ecm240/*.root".format(inDIR))
        else:
            cmd_stage1_f = cmd_stage1.replace('CLASS',sample)

        # run stage 1
        print(f'Now running stage 1 for sample {sample}')
        print(cmd_stage1_f)
        start1_time = time.time()
        subprocess.check_call(cmd_stage1_f, shell = True, stdout=list_stdout[i], stderr=list_stderr[i])
        end1_time = time.time()
        list_stdout[i].write("Stage1 time: {} \n".format(end1_time - start1_time))

    # RUN STAGE NTUPLE
    threads = []
    for i,sample in enumerate(samples):
        
        # make command
        cmd_stagentuple_train = cmd_stagentuple.replace('CLASS',sample).replace('MOD', mods[0]) + " {} {} ".format(0, N_split)
        cmd_stagentuple_test = cmd_stagentuple.replace('CLASS',sample).replace('MOD', mods[1]) + " {} {} ".format(N_split, N)

        # run stage 2
        print(f'Now running stage 2 for sample {sample}')
        print(cmd_stagentuple_train)
        print(cmd_stagentuple_test)
        thread = mp.Process(target=ntuplizer, args=(cmd_stagentuple_train, cmd_stagentuple_test, list_stdout[i], list_stderr[i]))
        thread.start()
        threads.append(thread)
        
    for proc in threads:
        proc.join()

    for i in range(len(list_stdout)):
        list_stdout[i].close()
        list_stderr[i].close()
