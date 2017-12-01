#!/usr/bin/python
import sys
import os
import argparse
import tempfile
import ming_proteosafe_library
import subprocess


def main():

    # parse the arguments
    parser = argparse.ArgumentParser(description='Running sirius wrapper')
    parser.add_argument('input_mgf_file', help='input_mgf_file')
    parser.add_argument('workflow_parameters', help='workflow_parameters')
    parser.add_argument('siriusoutput', help = 'siriusoutput')
    parser.add_argument('log', help='log') 
    parser.add_argument('sirius_jar', help='sirius_jar')
    parser.add_argument('gurobi_path', help='gurobi_path')



    args = parser.parse_args()
    param = args.workflow_parameters
    p_mgf = os.path.abspath(args.input_mgf_file)
    p_output = args.siriusoutput
    p_log = args.log
    p_sirius = args.sirius_jar 
    p_out = p_mgf.split(p_mgf.split("/")[-2])[0]
    p_out_sirius = p_out+"sirius"

    #start the log file
    fLog = open(p_log,"w")

    #Match the parameters
    params_obj = ming_proteosafe_library.parse_xml_file(open(param))
    i_mode = "ion [M+H]+"
    adduct = "auto-charge"



    if params_obj["adduct"][0] == "use MS1 information":
        adduct = "guession [M+H]+,[M+Na]+,[M+K]+,[M+NH4]+"

    if params_obj["Ionisation_mode"][0] == "Negative":
        i_mode = "ion [M+H]-"


    profile = params_obj["Profile_param"][0]
    DB = params_obj["DataBase"][0]
    try:
        ppm = params_obj["ppm"][0]
    except:
        ppm = str(10)

    try:
        tree_number = params_obj["tree_number"][0]
    except:
        tree_number = str(20)
    try:
        precursor= params_obj["precursor"][0]
    except:
        precursor = str(500)



    #writing batch file
    execute_script_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
    cmd = "export GUROBI_HOME=%s" % (args.gurobi_path)
    execute_script_file.write(cmd + "\n")


    # step1
    cmd = "%s -p %s --isotope both --ppm-max %s --candidates %s --maxmz %s --database %s --beautifytrees --%s --%s -o %s %s" % (p_sirius, profile, ppm,tree_number, precursor,DB,adduct,i_mode,p_out_sirius, p_mgf)
    execute_script_file.write(cmd + "\n")

    #execution
    execute_script_file.close()
    cmd = "sh %s" % (execute_script_file.name)
    err = subprocess.run(['sh',execute_script_file.name],stderr=subprocess.PIPE)
    stderror = err.stderr.decode(sys.stderr.encoding)
    if stderror != None:
        fLog.write("Sirius process has errors and/or warnings. Please see the following message.\n")
        fLog.write(stderror)
        fLog.write('\n')

    os.unlink(execute_script_file.name)

    #benchmarking
    for root, dirs, files in os.walk('sirius'):
        for name in files:
            if len(name.split('version.txt')) !=1:
                cmd = "rm %s"%(os.path.join(root, name))
                os.system(cmd)
            if len(name.split('.progress')) !=1:
                cmd = "rm %s"%(os.path.join(root, name))
                os.system(cmd)
        for folder in dirs:
            if len(folder.split('_mgf')) !=1:
                print (folder)
                firstcounter = folder.split('_')[-1]
                newname = '%s_mgf-00000_%s' %(firstcounter,firstcounter)
                try:
                    os.rename(os.path.join(root,folder),os.path.join(root,newname))
                except:
                    print('notright')
                    continue
                print('benchmarking')
                print(folder)

    #zip the output to one dir_zip
    runSirius=False
    cmd ="zip -r %s sirius"%(p_output)
    try:
        subprocess.check_output(["zip","-r",p_output,"sirius"])
        os.system(cmd)
        runSirius = True
    except subprocess.CalledProcessError as e:
        fLog.write("step 1 (sirius computation) did not proceed successfully. \n")

    fLog.close()







if __name__ == "__main__":
    main()
