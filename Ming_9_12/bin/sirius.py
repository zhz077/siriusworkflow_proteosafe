#!/usr/bin/python
import sys
import os
import argparse
import tempfile
import ming_proteosafe_library
#import xml.etree.ElementTree as ET

def transFiles(infolder,extension,outfolder):
    f_name=extension
    for f in os.listdir(infolder):
        if f.split("/")[-1] == f_name:
            filepath = infolder+"/"+f
            sendpath = outfolder+"/"+f_name
            cmd = "cp %s %s" %(filepath,sendpath)
            os.system(cmd)


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
    parser.add_argument('sirius_jar', help='sirius_jar')
    parser.add_argument('gurobi_path', help='gurobi_path')
    parser.add_argument('canopus_path', help='canopus_path')

    args = parser.parse_args()

    param = args.workflow_parameters
    p_mf = args.mf_folder
    p_mgf = os.path.abspath(args.input_mgf_file)
    p_c = args.canopus_path
    p_out = p_mgf.split(p_mgf.split("/")[-1])[0]
    p_out_sirius = p_out+"sirius"
    p_out_fingerid = p_out+"fingerid"
    p_out_zodiac = p_out+"zodiac"
    p_sirius = args.sirius_jar
    fpt_folder = args.fpt_folder
    p_csv_folder = os.path.abspath(args.input_csv_file)
    dir_zip = args.dir_zip
    summary = args.summary


    empty_exp = True
    for root,dirs,files in os.walk(p_csv_folder):
        if len(files) == 1:
            empty_exp = False
            for name in files:
                p_csv = os.path.join(root,name)




    #Match the parameters
    params_obj = ming_proteosafe_library.parse_xml_file(open(param))
    runFID = False
    i_mode = "ion [M+H]+"
    adduct = "auto-charge"
    annot = True


    if params_obj["adduct"][0] == "use MS1 information":
        adduct = "guession [M+H]+,[M+Na]+,[M+K]+,[M+NH4]+"

    try:
        if params_obj["spectral_annotation"][0] == "off":
            annot = False
    except:
            annot = True
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

    #save it in case lib doesnt work
    '''param = sys.argv[3]
    tree = ET.parse(param)
    root = tree.getroot()



    for child in root.findall("parameter"):
        settings = child.get('name')
        content = child.text
        if settings == "DataBase":
            DB = content
        if settings == "FingerID_run":
            if child.text == "on":
                runFID = True
        if settings == "Profile_param":
            profile = content
        if settings == "DataBase_FingerID":
            FID_DB = content
        if settings == "ppm":
            if content == "":
                ppm = content
        if settings == "Ionisation_mode":
            if content == "Negative":
                i_mode = "ion [M+H]-"
        if settings == "tree_number":
            tree_number = str(int(float(content)))
        if settings == "precursor":
            precursor = content
        if settings == "adduct":
            if child.text == "use MS1 information":
                adduct = "guession [M+H]+,[M+Na]+,[M+K]+,[M+NH4]+"

        if settings == "spectral_annotation":
            if child.text == "off":
                annot = False'''


    #writing batch file
    execute_script_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
    cmd = "export GUROBI_HOME=%s" % (args.gurobi_path)
    execute_script_file.write(cmd + "\n")



    # step1
    cmd = "%s -p %s --isotope score --ppm-max %s --candidates %s --maxmz %s --database %s --beautifytrees --%s --%s -o %s %s" % (p_sirius, profile, ppm,tree_number, precursor,DB,adduct,i_mode,p_out_sirius, p_mgf)
    execute_script_file.write(cmd + "\n")

    #step 2
    if annot and not empty_exp:
        cmd = "%s --zodiac  --sirius %s --spectral-hits %s --thresholdfilter 0.96  --output %s --processors 16 --specra %s" %(p_sirius,p_out_sirius,p_csv,p_out_zodiac,p_mgf)
        execute_script_file.write(cmd + "\n")
    else:
        cmd = "%s --zodiac --sirius %s --thresholdfilter 0.96  --output %s --processors 16 --spectra %s" %(p_sirius,p_out_sirius,p_out_zodiac,p_mgf)
        execute_script_file.write(cmd + "\n")

    print(cmd)
    #step3:
    if runFID:
        cmd = "%s --fingerid --fingerid-db %s --experimental-canopus=%s -o %s %s" %(p_sirius,FID_DB,p_c,p_out_fingerid,p_out_zodiac)
        execute_script_file.write(cmd + "\n")

    #zip the output to one dir_zip
    cmd ="zip -r %s sirius"%(os.path.join(dir_zip,"sirius.zip"))
    execute_script_file.write(cmd + "\n")
    cmd ="zip -r %s zodiac"%(os.path.join(dir_zip,"zodiac.zip"))
    execute_script_file.write(cmd + "\n")
    cmd ="zip -r %s fingerid"%(os.path.join(dir_zip,"fingerid.zip"))
    execute_script_file.write(cmd + "\n")

    #execution
    execute_script_file.close()
    cmd = "sh %s" % (execute_script_file.name)
    #print(execute_script_file.name)
    os.system(cmd)
    os.unlink(execute_script_file.name)


    #try to find all the ftp files and label them with feature ids
    extension='.fpt'
    ex_mf = '.csv'
    for root, dirs, files in os.walk(p_out_fingerid):
        for name in files:
            if os.path.splitext(name)[-1] == extension:
                filepath = os.path.join(root, name)
                sendpathset = str(filepath).split("/")
                sendpath = sendpathset[-3].split("_")[-1]
                fullname = sendpathset[-1]
                sendpath = fpt_folder+"/"+sendpath+"_"+fullname
                cmd = "cp %s %s" %(filepath,sendpath)
                os.system(cmd)
            if os.path.splitext(name)[-1] == ex_mf:
                filepath = os.path.join(root, name)
                cmd = "cp %s %s" %(filepath,p_mf)
                os.system(cmd)


    transFiles(p_out_zodiac,'zodiac_summary.csv',summary)
    transFiles(p_out_fingerid,'summary_csi_fingerid.csv',summary)







if __name__ == "__main__":
    main()
