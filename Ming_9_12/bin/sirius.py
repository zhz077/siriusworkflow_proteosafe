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
    parser.add_argument('input_csv_file', help='input_csv_file')
    parser.add_argument('workflow_parameters', help='workflow_parameters')
    parser.add_argument('fpt_folder', help='fpt_folder')
    parser.add_argument('summary', help='summary')
    parser.add_argument('mf_folder', help='mf_folder')
    parser.add_argument('dir_zip', help='dir_zip')
    parser.add_argument('log', help='log')
    parser.add_argument('sirius_jar', help='sirius_jar')
    parser.add_argument('gurobi_path', help='gurobi_path')
    parser.add_argument('canopus_path', help='canopus_path')


    args = parser.parse_args()
    param = args.workflow_parameters
    p_mf = args.mf_folder
    p_mgf = os.path.abspath(args.input_mgf_file)
    p_c = args.canopus_path
    p_out = p_mgf.split(p_mgf.split("/")[-2])[0]
    p_out_sirius = p_out+"sirius"
    p_out_fingerid = p_out+"fingerid"
    p_out_zodiac = p_out+"zodiac"
    p_sirius = args.sirius_jar
    fpt_folder = args.fpt_folder

    #read csv file if not empty
    empty_exp = True
    if args.input_csv_file != '':
        p_csv_folder = os.path.abspath(args.input_csv_file) 
        for root,dirs,files in os.walk(p_csv_folder):
            if len(files) == 1:
                empty_exp = False
            for name in files:
                p_csv = os.path.join(root,name)


    dir_zip = args.dir_zip
    summary = args.summary
    log = args.log

    #start the log file
    fLog = open(log,"w")

    #Match the parameters
    params_obj = ming_proteosafe_library.parse_xml_file(open(param))
    #runFID = False
    adduct = " "
    annot = True
    #runZodiac = True
    #only use "useSirius" to indicate which output to use for fid
    useSirius = True
    i_mode = "--auto-charge" 

    if params_obj["adduct"][0] == "use MS1 information":
        adduct = "--trust-ion-prediction"

    try:
        if params_obj["spectral_annotation"][0] == "on":
            annot = True
    except:
            annot = False
    '''try:
        if params_obj["FingerID_run"][0] == "on":
             runFID = True
    except:
            runFID = False'''
            
    try:
        if params_obj["runzodiac"][0] == "on":
            useSirius = False
    except:
            useSirius = True
            
    '''try:
        if params_obj["usesirius"][0] == "on":
             useSirius = True
    except:
            useSirius = False'''

    if params_obj["Ionisation_mode"][0] != "":
        i_mode = "--ion "+ params_obj["Ionisation_mode"][0] 

    profile = params_obj["Profile_param"][0]
    DB = params_obj["DataBase"][0]
    FID_DB = params_obj["DataBase_FingerID"][0]
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
        connections= params_obj["minLocalConnections"][0]
    except:
        connections = str(10)
        
    try:
        processor= params_obj["processor"][0]
    except:
        processor= str(16)
    try:
        filter= params_obj["filter"][0]
    except:
        filter= str(0.9)

    try:
        element= params_obj["element"][0]
    except:
        element = 'None'
    try:
        timeout= params_obj["timeout"][0]
    except:
        timeout = -1

    #writing batch file
    execute_script_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
    cmd = "export GUROBI_HOME=%s" % (args.gurobi_path)
    execute_script_file.write(cmd + "\n")
    cmd = 'export SIRIUS_OPTS="-Xmx15G"'
    execute_script_file.write(cmd + "\n")
    # step1
    cmd = "%s --quiet --initial-compound-buffer 0 --profile %s --candidates %s --processors %s --maxmz %s --ppm-max %s %s %s "%(p_sirius,profile,tree_number,processor,precursor,ppm,adduct,i_mode)
    if int(timeout) >0:
        cmd =cmd+"--compound-timeout %s " %(timeout)
    if element != 'None':
        cmd = cmd+"--elements %s " %(element)
    else:
        cmd = cmd +"--database %s "%(DB)
    
    if useSirius:
        cmd = cmd + "--fingerid --fingerid-db %s --experimental-canopus=%s -o %s %s" %(FID_DB,p_c,p_out_fingerid,p_mgf)
        execute_script_file.write(cmd + "\n")

    else:
        cmd = cmd+"--output %s %s" %(p_out_sirius, p_mgf)
        execute_script_file.write(cmd + "\n")

        #step 2
        if annot and not empty_exp:
            cmd = "%s --zodiac  --sirius %s --spectral-hits %s --thresholdfilter %s --minLocalConnections %s --output %s --processors %s --spectra %s" %(p_sirius,p_out_sirius,p_csv,filter,connections,p_out_zodiac,processor,p_mgf)
            execute_script_file.write(cmd + "\n")
        else:
            cmd = "%s --zodiac --sirius %s --thresholdfilter %s --minLocalConnections %s --output %s --processors %s --spectra %s" %(p_sirius,p_out_sirius,filter,connections,p_out_zodiac,processor,p_mgf)
            execute_script_file.write(cmd + "\n")

        #step3:
        cmd = "%s --fingerid --fingerid-db %s --experimental-canopus=%s -o %s %s" %(p_sirius,FID_DB,p_c,p_out_fingerid,p_out_zodiac)
        execute_script_file.write(cmd + "\n")

    #execution
    execute_script_file.close()
    cmd = "sh %s" % (execute_script_file.name)
    #os.system(cmd)
    #os.unlink(execute_script_file.name)
    err = subprocess.run(['sh',execute_script_file.name],stderr=subprocess.PIPE)
    stderror = err.stderr.decode(sys.stderr.encoding)
    if stderror != None:
        fLog.write("Sirius process has errors and/or warnings. Please see the following message.\n")
        fLog.write(stderror)
        fLog.write('\n')


    #zip the output to one dir_zip
    runSirius=False
    run_FID = False
    runZodiac=False
    
    cmd ="zip -r %s sirius"%(os.path.join(dir_zip,"sirius.zip"))
    try:
        subprocess.check_output(["zip","-r",os.path.join(dir_zip,"sirius.zip"),"sirius"])
        os.system(cmd)
        runSirius = True
    except subprocess.CalledProcessError as e:
        fLog.write("step 1 (sirius computation) did not proceed successfully. \n")
    cmd ="zip -r %s zodiac"%(os.path.join(dir_zip,"zodiac.zip"))
    try:
        subprocess.check_output(["zip","-r",os.path.join(dir_zip,"zodiac.zip"),"zodiac"])
        os.system(cmd)
        runZodiac = True
    except subprocess.CalledProcessError as e:
        fLog.write("step 2 (zodiac computation) did not proceed successfully and there won't be zodiac summary file. \n")
    cmd ="zip -r %s fingerid"%(os.path.join(dir_zip,"fingerid.zip"))
    try: 
        subprocess.check_output(["zip","-r",os.path.join(dir_zip,"fingerid.zip"),"fingerid"])
        os.system(cmd)
        run_FID = True
    except subprocess.CalledProcessError as e:
        fLog.write("step 3 (CSI:fingerid search) did not proceed successfully and there won't be finger id summary file. \n")
		
	


    #try to find all the ftp files and label them with feature ids
    extension='.fpt'
    ex_mf = '.csv'
    with tempfile.TemporaryDirectory() as p_fpt:
        if run_FID:
            for root, dirs, files in os.walk(p_out_fingerid):
                for name in files:
            	    if os.path.splitext(name)[-1] == extension:
            	        #canopus and fingerprints
            	        filepath = os.path.join(root, name)
            	        sendpathset = str(filepath).split("/")
            	        sendpath = sendpathset[-3].split("_")[-1]
            	        foldername = str(filepath).split("/")[-2]
            	        fullname = sendpathset[-1]
            	        sendpath = p_fpt+"/"+sendpath+"_"+foldername+"_"+fullname
            	        cmd = "cp %s %s" %(filepath,sendpath)
            	        os.system(cmd)
            	    if os.path.splitext(name)[-1] == ex_mf:
            	        filepath = os.path.join(root, name)
            	        cmd = "cp %s %s" %(filepath,p_mf)
            	        os.system(cmd)

            cmd ="zip -r %s %s" %(os.path.join(fpt_folder,"fpt.zip"),p_fpt)
            try: 
                subprocess.check_output(["zip","-r",os.path.join(fpt_folder,"fpt.zip"),p_fpt])
                os.system(cmd)
            except subprocess.CalledProcessError as e:
                fLog.write("step 3 (CSI:fingerid search) did not proceed successfully and there won't be fpt files. \n")

    if runZodiac:
        cmd = "cp %s %s" %(os.path.join(p_out_zodiac,'zodiac_summary.csv'),summary)
        try: 
            subprocess.check_output(["cp",os.path.join(p_out_zodiac,'zodiac_summary.csv'),summary])
            os.system(cmd)
        except subprocess.CalledProcessError as e:
            fLog.write("step 2 (zodiac) did not proceed successfully and there won't be fpt files. \n")
    if run_FID:
        cmd = "cp %s %s" %(os.path.join(p_out_fingerid,'summary_csi_fingerid.csv'),summary)
        try: 
            subprocess.check_output(["cp",os.path.join(p_out_fingerid,'summary_csi_fingerid.csv'),summary])
            os.system(cmd)
        except subprocess.CalledProcessError as e:
            fLog.write("step 3 (fingerid) did not proceed successfully and there won't be fpt files. \n")
    fLog.close()







if __name__ == "__main__": 
    main()
