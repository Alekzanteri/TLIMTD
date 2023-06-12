#AddData.py

import os
import pandas as pd
from mtpy.core.mt import MT
import glob

class AddData:
    
    "This class contains tools for adding and manipulating data."
    
    def __init__(dataAdder, folder, CSVdata):
        ediList=glob.glob(folder+r'\*.edi')#List of edi files in folder
        datalist=[]#empty list for mtpy objects
        for i in range (0,len(ediList)): 
            ediFile=ediList[i]
            mt_obj=MT(ediFile)
            datalist.append(mt_obj)#mt object is read
        
        add_data=pd.read_csv(CSVdata, index_col=0)
        
        dataAdder.datalist=datalist
        dataAdder.add_data=add_data
        dataAdder.ediList=ediList
        
    
    def rename(folder, CSVdata, rmv_old=True):
        """
        This function renames edi files in a given folder. New names need to be provided as CSV file.
        The columns need to be named as "station" and "new_name". AH 06/2023
        """
        dataAdder=AddData(folder, CSVdata)
        new_names=[]#list for renamed sites
        
        for i in range (0, len(dataAdder.datalist)):
            if dataAdder.datalist[i].station in dataAdder.add_data.index:#if the station has csv data to be added.
                if pd.isnull(dataAdder.add_data['new_name'][dataAdder.datalist[i].station])==False:#empty names can not be added
                    dataAdder.datalist[i].station=dataAdder.add_data['new_name'][dataAdder.datalist[i].station]#site is renamed
                    new_names.append(dataAdder.ediList[i])
                    dataAdder.datalist[i].write_mt_file(save_dir=folder,
                                                file_type='edi',
                                                longitude_format='LON',
                                                latlon_format='dd')#edi file with new name is added.

        if(rmv_old):#old edi with old name is removed
            for i in range (0, len(new_names)):
                os.remove(new_names[i])
            
        
        return
    
    def coordinates(folder, CSVdata, save_edi=False, savepath=None):
        """
        This function adds coordinate data to edi files from CSV file.
        CSV file column names need to be ' station', 'Lat' ja 'Lon'.
        Station needs to be first but otherwise order doesn't matter. AH 03/2023.
        """
        dataAdder=AddData(folder, CSVdata)
        
        
        for i in range (0, len(dataAdder.datalist)):
            if dataAdder.datalist[i].station in dataAdder.add_data.index:#if the station has csv data to be added.

                if pd.isnull(dataAdder.add_data['Lat'][dataAdder.datalist[i].station])==False:#check if the cell for data is empty
                    dataAdder.datalist[i].lat=dataAdder.add_data['Lat'][dataAdder.datalist[i].station]

                if pd.isnull(dataAdder.add_data['Lon'][dataAdder.datalist[i].station])==False:#check if the cell for data is empty
                    dataAdder.datalist[i].lon=dataAdder.add_data['Lon'][dataAdder.datalist[i].station]
                    print(f'Coordinates added to site {dataAdder.datalist[i].station}')


                if(save_edi):
                    dataAdder.datalist[i].write_mt_file(save_dir=savepath,
                                    file_type='edi',
                                    longitude_format='LON',
                                    latlon_format='dd')
                
        return(dataAdder.datalist)