#!/usr/bin/python
import sys
import os
import argparse
import tempfile
import ming_proteosafe_library
import subprocess
#import xml.etree.ElementTree as ET

def transFiles(infolder,extension,outfolder):
    f_name=extension
    for f in os.listdir(infolder):
        if f.split("/")[-1] == f_name:
            filepath = infolder+"/"+f
            sendpath = outfolder+"/"+f_name
            cmd = "cp %s %s" %(filepath,sendpath)
            try: 
                subprocess.check_output(["cp",filepath,sendpath])
                os.system(cmd)
            except subprocess.CalledProcessError as e:
                #fLog.write("step 3 (CSI:fingerid search) did not proceed successfully and there won't be csv summary files. \n")
                return


def main():

    # parse the arguments
    parser = argparse.ArgumentParser(description='Running sirius wrapper')
    parser.add_argument('input_mgf_file', help='input_mgf_file')
    parser.add_argument('input_csv_file', help='input_csv_file')
    parser.add_argument('workflow_parameters', help='workflow_parameters')
    parser.add_argument('siriusoutput', help = 'siriusoutput')
    parser.add_argument('summary', help = 'summary')
    parser.add_argument('zodiaclog', help = 'zodiaclog') 
    parser.add_argument('mf', help = 'mf')   
    parser.add_argument('fpt', help = 'fpt')  
    parser.add_argument('sirius_jar', help='sirius_jar')
    #parser.add_argument('gurobi_path', help='gurobi_path')
    parser.add_argument('canopus_path', help='canopus_path')
    parser.add_argument('sirius_zip', help = 'sirius_zip')  
    parser.add_argument('zodiac_zip', help = 'zodiac_zip')
    parser.add_argument('fingerid_zip', help = 'fingerid_zip')



    args = parser.parse_args()
    param = args.workflow_parameters
    p_mf = args.mf
    p_mgf = os.path.abspath(args.input_mgf_file)
    p_c = args.canopus_path
    p_out = p_mgf.split(p_mgf.split("/")[-2])[0]
    p_out_fingerid = p_out+"fingerid"
    p_out_zodiac = p_out+"zodiac"
    p_out_sirius = p_out+"sirius"
    p_sirius = args.sirius_jar
    fpt_folder = args.fpt



    #check csv is a directory or a file
    empty_exp = True
    if args.input_csv_file != '':  
        if(os.path.isfile(args.input_csv_file)):
            empty_exp = False
            p_csv = os.path.abspath(args.input_csv_file)


    sirius_zip = args.sirius_zip
    zodiac_zip = args.zodiac_zip
    fingerid_zip = args.fingerid_zip
    log = args.zodiaclog

    #start the log file
    fLog = open(log,"w")

    #Match the parameters
    params_obj = ming_proteosafe_library.parse_xml_file(open(param))
    runFID = False
    i_mode = "ion [M+H]+"
    adduct = "auto-charge"
    annot = True


    if params_obj["adduct"][0] == "use MS1 information":
        adduct = "guession [M+H]+,[M+Na]+,[M+K]+,[M+NH4]+"

    try:
        if params_obj["spectral_annotation"][0] == "on":
            annot = True
    except:
            annot = False
    try:
        if params_obj["FingerID_run"][0] == "on":
             runFID = True
    except:
            runFID = False

    if params_obj["Ionisation_mode"][0] == "Negative":
        i_mode = "ion [M+H]-"


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
        tree_number = str(20)

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


    #writing batch file
    execute_script_file2 = tempfile.NamedTemporaryFile(delete=False, mode='w')
    '''cmd = "export GUROBI_HOME=%s" % (args.gurobi_path)
    execute_script_file2.write(cmd + "\n")'''



    #step 1: unzip sirius
    filecount = 0;
    for root, dirs, files in os.walk(args.siriusoutput):
        for name in files:
            if os.path.splitext(name)[-1] == ".zip":
                cmd = "unzip %s"%(os.path.join(root, name))
                os.system(cmd)
                filecount = filecount+1

    #step 2
    if annot and not empty_exp:
        cmd = "%s --zodiac  --sirius %s --spectral-hits %s --thresholdfilter %s --minLocalConnections %s --output %s --processors %s --spectra %s" %(p_sirius,p_out_sirius,p_csv,filter,connections,p_out_zodiac,processor,p_mgf)
        execute_script_file2.write(cmd + "\n")
        print(cmd)
        print("csv")
    else:
        cmd = "%s --zodiac --sirius %s --thresholdfilter %s --minLocalConnections %s --output %s --processors %s --spectra %s" %(p_sirius,p_out_sirius,filter,connections,p_out_zodiac,processor,p_mgf)
        execute_script_file2.write(cmd + "\n")
        print(cmd)
        print(annot)
        print(empty_exp)




    #step3:
    if runFID:
        cmd = "%s --fingerid --fingerid-db %s --experimental-canopus=%s -o %s %s" %(p_sirius,FID_DB,p_c,p_out_fingerid,p_out_zodiac)
    execute_script_file2.write(cmd + "\n")

    #execution
    execute_script_file2.close()
    cmd = "sh %s" % (execute_script_file2.name)

    err = subprocess.run(['sh',execute_script_file2.name],stderr=subprocess.PIPE)
    stderror = err.stderr.decode(sys.stderr.encoding)
    if stderror != None:
        fLog.write("Sirius process has errors and/or warnings. Please see the following message.\n")
        fLog.write(stderror)
        fLog.write('\n')
    os.unlink(execute_script_file2.name)





    #try to find all the ftp files and label them with feature ids
    
    extension='.fpt'
    ex_mf = '.csv'
    with tempfile.TemporaryDirectory() as p_fpt:
        if runFID:
            for root, dirs, files in os.walk(p_out_fingerid):
                for name in files:
            	    if os.path.splitext(name)[-1] == extension:
            	        filepath = os.path.join(root, name)
            	        sendpathset = str(filepath).split("/")
            	        sendpath = sendpathset[-3].split("_")[-1]
            	        fullname = sendpathset[-1]
            	        sendpath = p_fpt+"/"+sendpath+"_"+fullname
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



            #zip the sirius output
            cmd ="zip -r %s %s"%(sirius_zip,p_out_sirius)
            try:
                subprocess.check_output(["zip","-r",sirius_zip,p_out_sirius])
                os.system(cmd)
            except subprocess.CalledProcessError as e:
                fLog.write("The sirius workflow didnt proceed successfully\n")

            #zip the zodiac output
            cmd ="zip -r %s %s"%(zodiac_zip,p_out_zodiac)
            print (cmd)
            try:
                subprocess.check_output(["zip","-r",zodiac_zip,p_out_zodiac])
                os.system(cmd)
            except subprocess.CalledProcessError as e:
                fLog.write("The zodiac workflow didnt proceed successfully\n")
    
            if runFID:
                #zip the fingerid output
                cmd ="zip -r %s %s"%(fingerid_zip,p_out_fingerid)
                print(cmd)
                try:
                    subprocess.check_output(["zip","-r",fingerid_zip,p_out_fingerid])
                    os.system(cmd)
                except subprocess.CalledProcessError as e:
                    cmd = "touch %s"%(fingerid_zip)
                    os.system(cmd)
                    fLog.write("The fingerid workflow didnt proceed successfully\n")
    
            transFiles(p_out_zodiac,'zodiac_summary.csv',args.summary)
            transFiles(p_out_fingerid,'summary_csi_fingerid.csv',args.summary)

            fLog.close()







if __name__ == "__main__":
    main()
