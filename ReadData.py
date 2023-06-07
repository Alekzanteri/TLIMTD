from mtpy.core.mt import MT
import mtpy.core.z as mtz
import os
import numpy as np
import pandas as pd
import glob

class ReadData:
    """ This class contains tools for reading data to mtpy using dataformats that doesn't work with mtpy normally.
    Class can also be used to convert other data types to .edi format. AH 06/2023
    
    Supported file formats atm are:
    - mtf
    - ide
    Feel free to make more! These are easy but time consuming to make.
    
    """
    
    
    def __init__(makeMTobj, site, lat, lon, imp, tip, save_edi, savepath=None, original=None, print_texts=True):
        """
        This makes mtpy mt object from data. AH 06/2023
        """
        
        
        if(imp['ROT'].max()!=0 or imp['ROT'].min()!=0 or tip['ROT'].max()>0 or tip['ROT'].min()<0):
            if (print_texts):
                print(f'{site} is rotated. This reader can not handle rotation! \nMT object is returned anyway, but remember the rotation it is not saved anywhere! Data will stay rotated.')
            else:
                raise ValueError('Data is rotated! This reader can not handle rotation!')
                
        mt_obj=MT()#new mt-object is created and data is added to it
        mt_obj.lat=lat
        mt_obj.lon=lon
        mt_obj.station=site
        mt_obj.elev=0


        z=[]
        z_error=[]
        for i in range (0, len(imp)): #data is reshaped to mtpy frienly form
            z.append([[imp['ReXX'][i]-1j*imp['ImXX'][i], imp['ReXY'][i]-1j*imp['ImXY'][i]], 
                            [imp['ReYX'][i]-1j*imp['ImYX'][i], imp['ReYY'][i]-1j*imp['ImYY'][i]]])
            z_error.append([[imp['VAR_XX'][i], imp['VAR_XY'][i]], 
                            [imp['VAR_YX'][i], imp['VAR_YY'][i]]])
        mt_obj.Z=mtz.Z(np.array(z), np.array(z_error), np.array(imp['freq'])) #z object is created and added to mt object

        if(len(tip)>0):#tipper is only done if it exits
            t=[]
            t_error=[]
            for i in range (0, len(tip)):
                t.append([[tip['ReXX'][i]-1j*tip['ImXX'][i], tip['ReXY'][i]-1j*tip['ImXY'][i]]])
                t_error.append([[tip['VAR_XX'][i], tip['VAR_XY'][i]]])
            mt_obj.Tipper=mtz.Tipper(np.array(t), np.array(t_error), np.array(tip['freq']))

        if(save_edi):
            mt_obj.write_mt_file(save_dir=savepath,
                                file_type='edi',
                                longitude_format='LON',
                                latlon_format='dd')

        makeMTobj.mtpy=mt_obj
        makeMTobj.original_type=original
        
        if(print_texts):
            if(save_edi==True):
                print(f'{mt_obj.station} is now converted to mtpy object and edi file is saved to {savepath}' )
            else:
                print(f'{mt_obj.station} is now converted to mtpy object. No edi saved')

    
    def mtf(file, save_edi, savepath=None, encoding='utf8'):
        """
        This function reads mtf file and converts it to mtpy object. AH 06/2023
        """
  
        lines=[] #With function opens the file and reads the file line by line to a list.
        with open(file, encoding=encoding) as f:
            for line in f:
                lines.append(line.strip())
        imp=pd.DataFrame(columns=['T,s', 'ROT', 'ReXX', 'ImXX', '|XX|_err', 'ReXY', 'ImXY', '|XY|_err', 'ReYX', 'ImYX', '|YX|_err',
                                  'ReYY','ImYY','|YY|_err'])#imp values
        tip=pd.DataFrame(columns=['T,s', 'ROT', 'ReXX', 'ImXX', '|XX|_err', 'ReXY', 'ImXY', '|XY|_err'])#tip values
        for i in range(0, len(lines)):
            if ">SITE_NAME" in lines[i]:#if line contains sitename
                if(len(lines[i].split(': '))>1):#if site name exits (split list is longer than 1) it is added.
                    site=lines[i].split(': ')[-1]
                else:
                    site=file.split('\\')[-1].split('.')[-2] #otherwise file name is used.
            elif '>LATITUDE'in lines[i]:
                lat=float(lines[i].split(':')[-1])
            elif '>LONGITUDE' in lines[i]:
                lon=float(lines[i].split(':')[-1])
            elif lines[i]=='//SECTION=IMP':#Data starts with this command
                y=i+1
                while y<len(lines) and lines[y]!='//SECTION=TIP': #New loop thoug periods when next section is not 
                                                                  #started and lines are not ended.
                    list=[x for x in lines[y].split(' ')if x!='']#line is splitted to numbers and empy values are removed.    
                    imp.loc[len(imp)]=list #data is added to imp panda.
                    y=y+1
                break #after data is added to the panda already red lines are skipped
        for i in range(y, len(lines)):#next loop is started where last left
            if lines[i]=='//SECTION=TIP':
                for c in range(i+1, len(lines)):
                    list=[x for x in lines[c].split(' ')if x!='']    
                    tip.loc[len(tip)]=list


        for column in imp: #IMP to float
            imp[column]=imp[column].astype(float)
        for column in tip:#tip to float
            tip[column]=tip[column].astype(float)
        imp['freq']=1/imp['T,s']
        tip['freq']=1/tip['T,s']
        #errors are calculated to right form
        imp['VAR_XX']=imp['|XX|_err']**2
        imp['VAR_XY']=imp['|XY|_err']**2
        imp['VAR_YX']=imp['|YX|_err']**2
        imp['VAR_YY']=imp['|YY|_err']**2
        tip['VAR_XX']=tip['|XX|_err']**2
        tip['VAR_XY']=tip['|XY|_err']**2
        mt_obj=ReadData(site, lat, lon, imp, tip, save_edi, savepath, original='.mtf')
        return(mt_obj.mtpy)
    
    
    def mtf_folder(folder, save_edi, savepath=None, encoding='utf8'):
        """
        This function reads folder mtf files and converts them to mtpy objects. AH 06/2023
        """
        mtf_files=glob.glob(folder+r'\*.mtf')
        mtpyObjects=[]
        for i in range (0, len(mtf_files)):
            mtpyObjects.append(ReadData.mtf(mtf_files[i], save_edi, savepath, encoding))
        return(mtpyObjects)
    
    
    def ide(file, save_edi, savepath=None, encoding='utf8'):
        """
        This function reads ide file and converts it to mtpy object. AH 06/2023
        """
        
        lines=[] #With function opens the file and reads the file line by line to a list.
        with open(file, encoding=encoding) as f:
            for line in f:
                lines.append(line.strip())
                
        imp=pd.DataFrame(columns=['freq', 'ROT', 'ReXX', 'ImXX', 'VAR_XX', 'ReXY', 'ImXY', 'VAR_XY', 'ReYX', 'ImYX', 'VAR_YX',
                                  'ReYY','ImYY','VAR_YY'])#imp values
        tip=pd.DataFrame(columns=['freq', 'ROT', 'ReXX', 'ImXX', 'VAR_XX', 'ReXY', 'ImXY', 'VAR_XY'])
        site=file.split('\\')[-1].split('.')[0]#site
        lat=float(lines[0].split("LAT:")[1].split("LONG:")[0].strip())#lat
        lon=float(lines[0].split("LONG:")[1].split("S")[0].strip())#lon

        for i in range(1, len(lines)):
            if lines[i]==('>>DATA'):
                a=0
                for c in range(i+1, len(lines)):
                        list=[x for x in lines[c].split(' ')if x!='']    
                        imp.loc[len(imp)]=list[0:14]
                        if len(list)>14:
                            tip.loc[a, ['freq', 'ROT']]=list[0:2]
                            tip.loc[a, ['ReXX', 'ImXX', 'VAR_XX', 'ReXY', 'ImXY', 'VAR_XY']]=list[14:20]
                        a=a+1
                break

        for column in imp: #IMP to float
            imp[column]=imp[column].astype(float)

        for column in tip: #TIP to float
            tip[column]=tip[column].astype(float)

        mt_obj=ReadData(site, lat, lon, imp, tip, save_edi, savepath, original='.ide')
        return(mt_obj.mtpy)
    
    
    def ide_folder(folder, save_edi, savepath=None, encoding='utf8'):
        """
        This function reads folder mtf files and converts them to mtpy objects. AH 06/2023
        """
        
        ide_files=glob.glob(folder+r'\*.ide')
        
        mtpyObjects=[]
        for i in range (0, len(ide_files)):
            mtpyObjects.append(ReadData.ide(ide_files[i], save_edi, savepath, encoding))
        return(mtpyObjects)