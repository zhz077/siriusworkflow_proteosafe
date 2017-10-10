#!/usr/bin/python
import sys
import os
import argparse
import csv
import pandas as pd


def searchmf(foldername,mf):
	smile = ''
	smileS = ''
	sname=''
	counter=''
	
	for root, dirs, files in os.walk(foldername):
		for name in files:
			if name.split("_")[1].split(".")[0] == mf:
				csv_path =os.path.join(root, name)
				csvFile = open(csv_path,"r")
				reader2 = csv.reader(csvFile, delimiter='\t')
				counter =0;
				for row2 in reader2:
					if counter ==0:
						counter =counter+1
						continue
					if counter ==3:
						break
					if smile == '':
						smileS =  str(round(float(str(row2[4])),2))
						smile = row2[6]
						sname = row2[5]
						continue
					smileS=smileS+';'+str(round(float(str(row2[4])),2))
					smile=smile+';'+row2[6]
					sname = sname+';'+row2[5]
					counter = counter+1
				csvFile.close()
	ArraytoReturn = [str(smile),str(smileS),str(sname),counter]
	return ArraytoReturn




def sepCol(df,col):
	sep = [] 
	max_col = 0;

	for row in df[col]:
		if len(row.split(';')) > max_col:
			max_col = len(row.split(';'))	
		sep.append(row.split(';'))

	for i in range(max_col):
		col_to_write=[]
		header="%s_%d"%(col,i+1)
		for j in range(len(sep)):
			try:
				col_to_write.append(sep[j][i])
			except:
				col_to_write.append(None)
		df.insert(df.columns.get_loc(col)+i,header,col_to_write)
	df = df.drop(col,1)
	return df

	

		
def main():
	#parse in all the parameters
	parser = argparse.ArgumentParser(description='Running csvbuilder wrapper')
	parser.add_argument('mf_folder', help='mf_folder')
	parser.add_argument('summary_folder', help='summary_folder')
	parser.add_argument('gnps_folder', help='gnps_folder')
	parser.add_argument('cytoscape_folder', help='cytoscape_folder')
	args = parser.parse_args()

	#define the paths
	p_mf = args.mf_folder
	p_sum = args.summary_folder
	p_gnps = args.gnps_folder
	p_cy = args.cytoscape_folder

	
	#fill up the field names for zodiac:
	skip_zodiac= True
	for root,dirs,files in os.walk(p_sum):
		for filename in files:
			if filename == 'zodiac_summary.csv':
				skip_zodiac = False
	if not skip_zodiac:
		f = open(p_sum+'/zodiac_summary.csv','r')
		zodiac = []
		for line in f:
			value = line.split('\n')[0].split('\t')
			zodiac.append(value)
		f.close()
		max_col = 0;
		for i in zodiac:
			if len(i) > max_col:
				max_col = len(i)
		for i in range(max_col-len(zodiac[0])):
			if i%2 ==0:
				zodiac[0].append('zodiac_MF_%d'%(int(i/2)+1))
			else:
				zodiac[0].append('zodiac_score_%d'%(int(i/2)+1))
		for i in zodiac:
			for j in range(max_col-len(i)):
				i.append(' ')
		with open(p_cy+'/zodiac_summary.csv','w') as result:
			writer = csv.writer(result,delimiter='\t')
			writer.writerows(zodiac)
	
		with open(p_gnps+'/zodiac_summary.csv','w') as result:
			writer = csv.writer(result,delimiter='\t')
			writer.writerows(zodiac)

		
	#edit cyto folder first

	#removing confusing benchmark
	skip_fid= True
	for root,dirs,files in os.walk(p_sum):
		for filename in files:
			if filename == 'summary_csi_fingerid.csv':
				skip_fid = False
	if not skip_fid:
		fingerid = pd.read_csv(p_sum+'/summary_csi_fingerid.csv',sep="\t")
		for name in ['source','inchi']:
			if name in fingerid.columns:
				fingerid=fingerid.drop(name,1)
	
	    # add the rank2, rank3 strutures to each zodiac mf
		evalList = []
		for s in fingerid['score']:
			if int(s) > -10:
				evalList.append("Very Good (FDR ~5%)")
			elif int(s) >-12:
				evalList.append("Good (FDR ~10%)")
			elif int(s)>-30:
				evalList.append("Satisfactory (FDR ~20%)")
			elif int(s)>-65:
				evalList.append("Fair (FDR ~30%)")
			else:
				evalList.append("Bad ")
		fingerid['Estimate identification'] = evalList;
		
		mf_str= [] 
		mf_score=[]
		mf_name=[]
		for mf in fingerid['molecularFormula']:
			a = searchmf(p_mf,mf)
			mf_str.append(a[0])
			mf_score.append(a[1])
			mf_name.append(a[2])
		fingerid['smiles'] = mf_str
		fingerid['score'] = mf_score
		fingerid['name'] = mf_name



		fingerid.to_csv(p_cy+'/summary_csi_fingerid.csv',sep='\t',index=False)
	

		#edit dataframe into gnps
		fingerid = sepCol(fingerid,'smiles')
		fingerid = sepCol(fingerid,'score')
		fingerid = sepCol(fingerid,'name')
		fingerid.to_csv(p_gnps+'/summary_csi_fingerid.csv',sep='\t',index=False)

	

if __name__ == "__main__":
    main()
