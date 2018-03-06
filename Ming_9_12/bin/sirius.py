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
    #adduct = "auto-charge"



    #if params_obj["adduct"][0] == "use MS1 information":
        #adduct = "guession [M+H]+,[M+Na]+,[M+K]+,[M+NH4]+"

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
        tree_number = str(50)
    try:
        precursor= params_obj["precursor"][0]
    except:
        precursor = str(500)
    try:
        element= params_obj["element"][0]
    except:
        element = 'None'
    try:
        timeout= params_obj["timeout"][0]
    except:
        timeout = -1
    try:
        processor= params_obj["processor"][0]
    except:
        processor = 16




    #writing batch file
    execute_script_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
    cmd = "export GUROBI_HOME=%s" % (args.gurobi_path)
    execute_script_file.write(cmd + "\n")

    cmd = "%s --quiet --initial-compound-buffer 0 --profile %s --candidates %s --processors %s --maxmz %s --ppm-max %s --%s "%(p_sirius, profile,tree_number,processor,precursor,ppm,i_mode)
    if int(timeout) >0:
        cmd =cmd+"--compound-timeout %s " %(timeout)
    if element != 'None':
        cmd = cmd+"--elements %s " %(element)
    else:
        cmd = cmd +"--database %s "%(DB)
    
    cmd = cmd+"--sirius %s %s" %(p_out_sirius, p_mgf)
    execute_script_file.write(cmd + "\n")
    print (cmd)

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
    


    #unzip the sirius
    cmd2 = "zip -d %s version.txt" %(p_output)
    cmd1 = "mv sirius %s"%(p_output)
    os.system(cmd1)
    os.system(cmd2)

    fLog.close()










if __name__ == "__main__":
    main()
