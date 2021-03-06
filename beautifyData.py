from collections import deque
import pandas as pd
import sys 
import os
from datetime import datetime as dt

# From local file
from utils import getArgs, \
                  extractDirName,\
                  writeCSV, \
                  moveTables, \
                  figureoutTable, \
                  _separatePhaseFiles 


def returnCols(tbl, line1, line2):
    """Returns the appropriate columns based on the table which is currently 
    being read
    
    Arguments:
        tbl{int} -- takes a value between 1-8 based on the convention used to
            represent the various table files
        line1 {str} -- First non blank Line
        line2 {str} -- Second non blank Line
    """
    # Guide:
    # 1. phase_main_tbl.txt (type 1) -- Starts with liquid_0 thermodynamic..
    # 2. phase_main_tbl.txt (type 2) -- Starts with P T ...
    # 3. phase_mass_tbl.txt -- starts with Phase Masses
    # 4. phase_vol_tbl.txt -- starts with Phase Volumes
    # 5. solid_comp_tbl.txt -- starts with Solid Composition
    # 6. system_mail_tbl.txt -- starts with System Thermodynamic data
    # 7. trace_main_tbl.txt -- starts as P Pval T Tval
    # 8. bulk_comp_tbl.txt -- starts with Bulk Composition

    if tbl == 1:
        line2 = [x.strip() for x in line2.split(' ')]
        columns = line2
        columns.remove('mass')
        columns.insert(2, 'Mass')
        columns.insert(2, "Phase")
        columns.insert(9, "F")
    elif tbl == 2:
        line1 = line1.split(' ')
        oxides = line1[4:]
        columns = [
                'Pressure',
                'Temperature',
                'Phase',
                'Mass',
                'S',
                'H',
                'V',
                'Cp',
                'Vis',
                'F',
                'Structure',
                'Formula',
                *oxides[:-1],
                oxides[-1].strip('\n'),
                'Mg#',
        ]
    elif tbl in (3, 4, 5, 6, 8):
        line2 = [x.strip() for x in line2.split(' ')]
        columns = line2
        columns = list(filter(lambda x: x != '', columns))
    elif tbl == 7:
        print("Trace Elements not implemented yet")

    return columns


def _extractPhaseMainT1(phase, f):
    """For any particular phase data, which will be passed as a deque object,
    this function will extract all the necessary columns and return a DataFrame
    object.
    
    Arguments:
        phase {deque object} -- for one phase, whole table from output, as a 
            deque object
        f {list} -- list of the Melt Fraction remaining data for each 
            temperature
    """

    phaseName = phase[0].split(" ")[0]
    
    line1 = phase.popleft()
    line2 = phase.popleft()
    
    columns = returnCols(1, line1, line2)
    
    rawData = []
    
    for line, F in zip(phase, f):
        PTcond = [x.strip() for x in line.split(" ")]
        PTcond.insert(2, phaseName)
        PTcond.insert(9, None)
        rawData.append(PTcond)
    
    DF = pd.DataFrame(data=rawData, columns=columns)
    
    return DF


def _extractPhaseDataT2(iteration, f, columns):
    """extracts the data from a single PT condition and returns a dataframe object containing the data
    
    Arguments:
        iteration {list} -- List of lists containing all the coexisting phases
         and their data for any given PT conditions
        f {list} -- List of F (melt remaining data)
        columns {list} -- Columns of the DataFrame that are present
    """

    # Initialising blank list where all the phases will be appended
    currentEnv = []

    # Initialising blank dict, where the data will be populated
    values = [None] * len(columns)

    # Extracting 1st line, as it is different from the rest of the lines
    line1 = iteration[0].split(' ')         

    # Extracting P from line1 (columns[0] = 'Pressure')
    P = line1[1]
    
    # Extracting T from line1 (columns[1] = 'Temperature')
    T = line1[3]

    # Extracting the list of oxides
    oxideList = line1[4:]

    for line in iteration[1:]:
        # Inserting P-T values
        values[0] = P
        values[1] = T

        # Converting the string to queue for better accessibility
        line = deque([x for x in line.split(' ') if x is not ''])
        
        # Extracting phase name (columns[2] = 'Phase')
        values[2] = line.popleft()
        phasename = values[2]

        # Extracting Mass (columns[3] = 'Mass')
        values[3] = line.popleft()

        # Extracting S (columns[4] = 'S')
        values[4] = line.popleft()

        # Extracting H (columns[5] = 'H)
        values[5] = line.popleft()

        # Extracting V (columns[6] = 'V')
        values[6] = line.popleft()

        # Extracting Cp (columns[7] = 'Cp')
        values[7] = line.popleft()

        # Extracting Viscosity, if phase is liquid
        if phasename.startswith('liquid'):
            # (columns[8] = 'Vis')
            values[8] = line.popleft()

        # Inputting melt remaining value (f)
        values[9] = f

        # Extracting Structure
        if phasename.startswith('clinopyroxene') \
           or phasename.startswith('amphibole'):
            # (columns[10] = 'Strcture')
            values[10] = line.popleft()
        
        # Extracting the Structure of the solids
        if not phasename.startswith('liquid'):
            # (columns[11] = 'Formula')
            values[11] = line.popleft()

        # For pure minerals (line Quartz, there will be no other information)
        # So, Extract Oxide and REE Data if present
        if len(line) != 0:
            for i in range(len(oxideList)):
                values[12+i] = line.popleft()

        # If the the phase is liquid, there will be Mg# left
        if len(line) == 1:
            values[-1] = line.popleft()

        currentEnv.append(values)

        # reset list of Values
        values = [None] * len(columns)
    
    return pd.DataFrame(data=currentEnv, columns=columns)


def extractPhaseMain(phase_main, F):
    """Extracts the Phase Data, and also adds remaining melt data to the 
    DataFrame
    
    Arguments:
        phase_main -- path to the input file containing Phase related Data
        F {list} -- List of F (remaining melt fraction) values for all the 
            temperatures
    """
    tbl = figureoutTable(phase_main)

    with open(phase_main, 'r') as f:
        output = deque(f.readlines())
        title = output.popleft()
        _ = output.popleft()
        
        if tbl == 1:
            # List for storing all the DataFrames
            phaseDFs = []
            phase = deque()
            
            while len(output) > 0:
                currentLine = output.popleft()
                if currentLine.strip() != '':
                    phase.append(currentLine)
                else:
                    phaseDFs.append(_extractPhaseMainT1(phase, F))
                    phase = deque()
        
            DF = pd.concat(phaseDFs, join='outer', sort=False)
            DF = DF.sort_values('Temperature', ascending=False)
            DF = DF.reset_index()
            DF = DF.drop(columns=['index'], errors='ignore')

            temp = 0
            previousTemp = None

            for i, currentTemp in enumerate(DF['Temperature'].values):
                if currentTemp == previousTemp:
                    DF.loc[i, 'F'] = DF.loc[i-1, 'F']
                else:
                    DF.loc[i, 'F'] = F[temp]
                    temp += 1
                    previousTemp = currentTemp

        elif tbl == 2:
            iteration = []
            
            columns = returnCols(tbl, output[0], None)
            
            DF = pd.DataFrame(columns=columns)

            # Getting the values for Melt Remaining (f)
            fvals = F

            # With every append, this goes up by one, hence can be effectively used 
            # for accessing the correct f value fro the given PT condition
            faccessor = 0

            while(len(output) > 0):
                
                line = output.popleft().strip("\n")

                if line.split(" ")[0] != "Pressure":
                    iteration.append(line)
                elif line.split(" ")[0] == "Pressure":
                    if len(iteration) != 0:
                        # Read the data and fill No data Values with None
                        currentEnv = _extractPhaseDataT2(
                            iteration,
                            fvals[faccessor],
                            columns
                        )
                        # Convert this to pandas DataFrame
                        DF = DF.append(currentEnv)
                    # Next iteration
                    iteration = [line]
                    faccessor += 1

        return DF


def extractSolidComp(path):
    """Reads a table file which as a generic column layout. Where, adter the
    name of the table, data is written as column names followed by data
    
    Arguments:
        path {str} -- Path to the table file
    """

    tbl = figureoutTable(path)

    values = []
    
    with open(path, 'r') as f:
        output = deque(f.readlines())

        title = output.popleft()
        _ = output.popleft()

        columns = returnCols(
            tbl,
            output.popleft(),
            output.popleft()
        )

        for line in output:
            value = [x.strip() for x in line.split(' ')]
            if value[-1] == '---':
                _ = value.pop()
                zerosToAdd = len(columns) - len(value)

                value.extend([0.00]*zerosToAdd)

            values.append(value)

    DF = pd.DataFrame(data=values, columns=columns)
    return DF


def extractGeneric(path):
    """Reads a table file which as a generic column layout. Where, adter the
    name of the table, data is written as column names followed by data
    
    Arguments:
        path {str} -- Path to the table file
    """

    tbl = figureoutTable(path)

    values = []
    
    with open(path, 'r') as f:
        output = deque(f.readlines())

        title = output.popleft()
        _ = output.popleft()

        columns = returnCols(
            tbl,
            output.popleft(),
            output.popleft()
        )

        for line in output:
            values.append([value.strip() for value in line.split(' ') if value.strip()])

    DF = pd.DataFrame(data=values, columns=columns)
    return DF


def extractSystemMain(path):
    """Reads the file System_main_tbl.txt and returns a fataframe object 
    containing the information
    
    Arguments:
        inputfiles {dict} -- Dictionary of all the input files
    """

    values = []
    
    tbl = figureoutTable(path)

    with open(path) as f:
        output = deque(f.readlines())
        
        Title = output.popleft()
        _ = output.popleft()

        columns = returnCols(tbl, output.popleft(), output.popleft())

        for line in output:
            values.append([value.strip() for value in line.split()])
    
    DF = pd.DataFrame(data=values, columns=columns)
    DF['F'] = pd.to_numeric(DF['F']).cumprod()
    return DF


def extractData(inputfiles):
    """Wrapper function which calls all the required Data Extraction funcitons 
    with required parameterse and returns all the necessary DataFrame
    
    Arguments:
        inputfiles {dict} -- Dictionary of all the input files
    """
    # Guide to keys of data
    # 'phase_main', Done
    # 'phase_mass', Done [Generic]
    # 'phase_vol', Done [Generic]
    # 'solid_comp', Done
    # 'system_main', Done
    # 'trace_main', Not Yet
    # 'bulk_comp' Done [Generic]

    print("[+] Extracting System Thermodynamic Data")
    systemMain = extractSystemMain(inputfiles['system_main'])
    F = systemMain['F'].values
    print("[+] Extracted System Thermodynamic Data Successfully")

    print("[+] Reading Phase Main Data")
    phaseMain = extractPhaseMain(inputfiles['phase_main'], F)
    print("[+] Read Phase Main Data successfully")

    print("[+] Extracting Bulk Composition Data")
    bulkComp = extractGeneric(inputfiles['bulk_comp'])
    print("[+] Extracted Bulk Composition Data Successfully")

    print("[+] Extracting Phase Mass data")
    phaseMass = extractGeneric(inputfiles['phase_mass'])
    print("[+] Extracted Phase Mass Data Successfully")

    print("[+] Extract Solid Composition Data")
    solidComp = extractSolidComp(inputfiles['solid_comp'])
    print("[+] Extracted Solid Composition Data Successfully")

    print("[+] Extracting Phase Volume Data")
    phaseVol = extractGeneric(inputfiles['phase_vol'])
    print("[+] Extracted Phase Volume Data Successfully")

    Data = {
        'phase_main': phaseMain,
        'phase_mass': phaseMass,
        'phase_vol': phaseVol,
        'solid_comp': solidComp,
        'system_main': systemMain,
        'bulk_comp': bulkComp
    }

    convertTemp = input("[?] Do you want to convert Temperatures to C from K (y/n): ")

    if convertTemp.capitalize() == 'Y':
        convertTemp = True
    else:
        convertTemp = False

    if convertTemp: 
        for key in Data.keys():
            Data[key]['Temperature'] = Data[key]['Temperature'].astype(float) - 273.15
  
    choice = input("[?] Do you want to create separate CSV files for every Phase? (y/n): ")
    if choice.capitalize() == 'Y':
        choice = True
    else:
        choice = False

    phases = _separatePhaseFiles(phaseMain)

    if phases:
        Data.update(phases)

    return Data    


if __name__ == '__main__':
    # Input the location where the data files are present
    if len(sys.argv) > 1:
        mainpath = getArgs()
    else:
        mainpath = input("[!] Enter path to Working Directory (Press ENTER for default): ")
        if mainpath == '':
            mainpath = '../'
    
    # Check if path is valid
    if not os.path.isdir(mainpath):
        print("[-] Working Directory doesn't exist; Exiting")
        sys.exit(2)

    outputpath = mainpath + "/alphameltsData/output/{}/".format(
        dt.now().strftime('%Y-%m-%d_%H-%M')
    )

    phase_main = mainpath + "Phase_main_tbl.txt"
    system_main = mainpath + "System_main_tbl.txt"
    bulk_comp = mainpath + "Bulk_comp_tbl.txt"
    liquid_comp = mainpath + "Liquid_comp_tbl.txt"  # redundant
    solid_comp = mainpath + "Solid_comp_tbl.txt"
    phase_mass = mainpath + "Phase_mass_tbl.txt"    # redundant
    phase_vol = mainpath + "Phase_vol_tbl.txt"      # redundant
    trace_main = mainpath + "Trace_main_tbl.txt"
  
    inputpaths = (
        phase_main,
        phase_mass,
        phase_vol,
        solid_comp,
        system_main,
        trace_main,
        bulk_comp
    )
    inputnames = (
        'phase_main',
        'phase_mass',
        'phase_vol',
        'solid_comp',
        'system_main',
        'trace_main',
        'bulk_comp'
    )

    inputfiles = dict(zip(inputnames, inputpaths))
    
    Data = extractData(inputfiles)

    writeCSV(Data, outputpath)

    # Cleaning the directory
    moveTables(mainpath, outputpath)
