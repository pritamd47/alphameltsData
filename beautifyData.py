from collections import deque
import pandas as pd
from datetime import datetime as dt
import os
import sys
import getopt


def returnCols(line1, line2):
    """Reads the first two lines and determines the columns that the DataFrame 
    object will have
    
    Arguments:
        line1 {str} -- First non blank Line
        line2 {str} -- Second non blank Line
    """
    '''
    Reads the first line (Line containing P T Oxides info), and sets the 
    sequence of oxides properly along with all the other thermodynamic data
    that is to be read later. 

    The default Sequence is as follows:
    Pressure Temperature Phase Mass S H V Cp Vis Structure Formula [Oxides] Mg#

    @params
    line1: The first non blank line
    line2: The Second non blank line. None can be passed in case where columns
        being extracted are for the main phase table

    @return
    columns: List of variables that are to be read later in the run cycle in a
        sequenctial order. 
    '''
    # Stripping extra characters from line string
    line1 = line1.strip()

    if "System Thermodynamic Data" in line1 or "Bulk Composition" in line1:
        line2 = [x.strip() for x in line2.split(' ')]
        columns = line2
    else:
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

    return columns


def _extractPhaseData(iteration, f, columns):
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


def extractSystemMain(inputfiles):
    """Reads the file System_main_tbl.txt and returns a fataframe object 
    containing the information
    
    Arguments:
        inputfiles {dict} -- Dictionary of all the input files
    """
    
    phase_main = inputfiles['phase_main']
    system_main = inputfiles['system_main']
    values = []

    with open(system_main) as f:
        output = deque(f.readlines())

        System = output.popleft().split(' ')[1]
        _ = output.popleft()                    # Deleting blank line
        columns = returnCols(
            output.popleft(),                   # Passing first two Non Blank
            output.popleft()                    # lines
        )

        for line in output:
            values.append([value.strip() for value in line.split()])
        
    DF = pd.DataFrame(data=values, columns=columns)
    return DF


def extractPhaseMain(inputfiles, F):
    """Extracts the Phase Data, and also adds remaining melt data to the 
    DataFrame
    
    Arguments:
        inputfiles {dict} -- Dictionary of the input files.
        F {list} -- List of F (remaining melt fraction) values for all the 
            temperatures
    """

    phase_main = inputfiles['phase_main']
    system_main = inputfiles['system_main']

    with open(phase_main, 'r') as f:
        output = deque(f.readlines())
        iteration = []

        Title = output.popleft().split(" ")[1]
        _ = output.popleft()                    # Deleting the blank line
        
        columns = returnCols(output[0], None)   # Passing the first non-Blank 
        #                                         Line
        
        DF = pd.DataFrame(columns=columns)      # Empty Dataframe with required
        #                                         columns

        # Getting the values for Melt Remaining (f), Expecting a list of values
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
                    currentEnv = _extractPhaseData(
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


def extractBulkComp(inputfiles):
    """Extracts the data from Bulk_comp_tbl.txt file
    
    Arguments:
        inputfiles {dict} -- dict containing all the input file paths
    """
    bulk_comp = inputfiles["bulk_comp"]

    values = []
    
    with open(bulk_comp, 'r') as f:
        output = deque(f.readlines())
        Title = output.popleft().split(' ')[1]
        _ = output.popleft()

        columns = returnCols(
            output.popleft(),
            output.popleft()
        )

        for line in output:
            values.append([value.strip() for value in line])

    DF = pd.DataFrame(data=values, columns=columns)
    return DF


def extractData(inputfiles):
    """Wrapper function which calls all the required Data Extraction funcitons 
    with required parameterse and returns all the necessary DataFrame
    
    Arguments:
        inputfiles {dict} -- Dictionary of all the input files
    """

    SystemMain = extractSystemMain(inputfiles)
    F = SystemMain['F'].values

    PhaseMain = extractPhaseMain(inputfiles, F)
    
    BulkMain = extractBulkComp(inputfiles)

    return (PhaseMain, SystemMain, BulkMain)


def extractDirName(filepath):
    """Extracts the name of the Directory in which a file exists for its
     file path.
    
    Arguments:
        filepath {str} -- the path of the file, for which directory is to be
            found
    """
    dir = '/'.join(filepath.split('/')[:-1])
    return dir


def moveTables(mainpath, outputDir):
    """Moves the output files of the alphaMelts program to another directory,
    hence achieving a more cleaner main working directory
    
    Arguments:
        mainpath {str} -- Path of the main working direcotry
        outputDir {str} -- Path where the output files are to be stored
    """
    files = os.listdir(mainpath)
    files = filter(lambda x: '_tbl.txt' in x, files)

    Dir = outputDir + "Tables/"

    if not os.path.exists(Dir):
        os.makedirs(Dir)
    
    for f in files:
        origin = mainpath + f
        destination = Dir + f
        print("Moving {} to {}".format(origin, destination))
        os.rename(origin, destination)


def writeCSV(filepath, DF):
    """Writes a DataFrame file to the filepath given as a csv file
    
    Arguments:
        filepath {str} -- Complete path of the csv file
        DF {pandas.DataFrame} -- The DataFrame object that is to be saved
    """
    if not os.path.isdir(extractDirName(filepath)):
        os.makedirs(extractDirName(filepath))
    with open(filepath, 'w') as out:
        print("Writing CSV at: {}".format(filepath))
        DF.to_csv(out)


def getArgs():
    """Reads the arguments and returns the path of the directory where all the 
    output files are present
    """
    try:
        opts, args = getopt.getopt(sys.argv[1:], "io", ["ifile=", "ofile="])
    except getopt.GetoptError:
        print('{} -i <inputfile>'.format(sys.argv[0]))
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print('{} -i <inputfile>'.format(sys.argv[0]))
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = args[0]

    return inputfile


if __name__ == '__main__':
    # Input the location where the data files are present
    if len(sys.argv) > 1:
        mainpath = getArgs()
    else:
        mainpath = input("Enter path to output files (Leave blank for default): ")
        if mainpath == '':
            mainpath = '../'
    
    outputpath = mainpath + "output/{}/".format(
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
        system_main,
        bulk_comp,
        solid_comp,
        trace_main
    )
    inputnames = (
        'phase_main',
        'system_main',
        'bulk_comp',
        'solid_comp',
        'trace_main'
    )

    inputfiles = dict(zip(inputnames, inputpaths))
   
    phaseOutput = outputpath + 'Phase_main_tbl.csv'
    systemOutput = outputpath + 'System_main_tbl.csv'
    bulkOutput = outputpath + 'Bulk_comp_tbl.csv'
    
    PhaseMain, SystemMain, BulkComp = extractData(inputfiles)

    writeCSV(phaseOutput, PhaseMain)
    writeCSV(systemOutput, SystemMain)
    writeCSV(bulkOutput, BulkComp)

    # Cleaning the directory
    moveTables(mainpath, outputpath)

