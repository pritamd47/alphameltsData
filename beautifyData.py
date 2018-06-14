from collections import deque
import pandas as pd


def returnCols(line1, line2):
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

    if line1 == "System Thermodynamic Data:":
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
    '''
    This function extracts all the data from the output of any given 
    alphaMelts run.

    @params:
    iteration: data from a single P T condition. It must be in the form of
        a list containing lists of all the coexisting phases and their data as
        a string
    f: the Melt Remaining value (f)
    columns: the columns that are to be extracted in the sequential order. Only 
        needed for Oxides. Rest of the columns have to be in this order:
        P T Phase Mass S H Vol Cp Vis Struct Formula [Oxides] Mg#
    
    @returns:
    DataFrame containing the values with proper column names
    ''' 

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


def extractSystemMain(inputpaths):
    '''
    Reads the file System_main_tbl.txt and returns a datafarme object 
    containing the information.

    @params
    inputpaths: sequential paths to all Input Data files

    @return:
    Dataframe containing System thermodynamic data

    '''

    phase_main, system_main = inputpaths
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


def extractPhaseMain(inputpaths, F):
    '''
    Extracts the Phase Data and also adds remaining melt data to the DataFrame

    @params
    inputpaths: sequential list of input file paths

    F: List of F (remaining melt fraction) values

    @return
    DataFrame containing Phase Related Data
    '''
    phase_main, system_main = inputpaths

    with open(phase_main, 'r') as f:
        output = deque(f.readlines())
        iteration = []

        Title = output.popleft().split(" ")[1]
        _ = output.popleft()                    # Deleting the blank line
        
        columns = returnCols(output[0], None)         # Passing the first non-Blank 
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


def extractData(inputpaths):
    '''
    Wrapper function which calls all the required Data Exraction functions with
    required parameters and returns all the DataFrames.

    @params
    inputpaths: List of file paths to extract data from in sequence.

    @returns
    List of DataFrames
    '''
    SystemMain = extractSystemMain(inputpaths)
    F = SystemMain['F'].values

    PhaseMain = extractPhaseMain(inputpaths, F)

    return [PhaseMain, SystemMain]


def writeCSV(filepath, DF):
    with open(filepath, 'w') as out:
        print("Writing CSV")
        DF.to_csv(out)


if __name__ == '__main__':
    phase_main = r"F:\windows_alphamelts_1-8\links\Phase_main_tbl.txt"
    system_main = r"F:\windows_alphamelts_1-8\links\System_main_tbl.txt"

    inputpaths = (phase_main, system_main)

    phaseOutput = r'f:\windows_alphamelts_1-8\links\Scripts\Phase_main_tbl.csv'
    
    PhaseMain, SystemMain = extractData(inputpaths)

    writeCSV(phaseOutput, PhaseMain)