from collections import deque
import pandas as pd


def returnCols(line):
    '''
    Reads the first line (Line containing P T Oxides info), and sets the 
    sequence of oxides properly along with all the other thermodynamic data
    that is to be read later. 

    The default Sequence is as follows:
    Pressure Temperature Phase Mass S H V Cp Vis Structure Formula [Oxides] Mg#

    @params
    line: The first non blank line, which starts as follows :
        Pressure: ____ Temperature: ___ ....

    @return
    columns: List of variables that are to be read later in the run cycle in a
        sequenctial order. 
    '''
    line = line.split(' ')
    oxides = line[4:]
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
            'Structure',
            'Formula',
            *oxides[:-1],
            oxides[-1].strip('\n'),
            'Mg#'
    ]

    return columns


def extractData(iteration, columns):
    '''
    This function extracts all the data from the output of any given 
    alphaMelts run.

    @params:
    iteration: data from a single P T condition. It must be in the form of
        a list containing lists of all the coexisting phases and their data as
        a string
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

        # Extracting Structure
        if phasename.startswith('clinopyroxene') \
           or phasename.startswith('amphibole'):
            # (columns[9] = 'Strcture')
            values[9] = line.popleft()
        
        # Extracting the Structure of the solids
        if not phasename.startswith('liquid'):
            # (columns[10] = 'Formula')
            values[10] = line.popleft()

        # For pure minerals (line Quartz, there will be no other information)
        # So, Extract Oxide and REE Data if present
        if len(line) != 0:
            for i in range(len(oxideList)):
                values[11+i] = line.popleft()

        # If the the phase is liquid, there will be Mg# left
        if len(line) == 1:
            values[-1] = line.popleft()

        currentEnv.append(values)

        # reset list of Values
        values = [None] * len(columns)
    
    return pd.DataFrame(data=currentEnv, columns=columns)


if __name__ == '__main__':
    with open(r"F:\windows_alphamelts_1-8\links\Phase_main_tbl.txt", 'r') as f:
        output = deque(f.readlines())
        iteration = []

        Title = output.popleft().split(" ")[1]
        _ = output.popleft()                    # Deleting the blank line
        
        columns = returnCols(output[0])         # Passing the first non-Blank 
        #                                         Line
        
        DF = pd.DataFrame(columns=columns)

        while(len(output) > 0):
            
            line = output.popleft().strip("\n")

            if line.split(" ")[0] != "Pressure":
                iteration.append(line)
            elif line.split(" ")[0] == "Pressure":
                if len(iteration) != 0:
                    # Read the data and fill No data Values with None
                    currentEnv = extractData(iteration, columns)

                    # Convert this to pandas DataFrame
                    DF = DF.append(currentEnv)
                iteration = [line]

    with open(r'f:\windows_alphamelts_1-8\links\Scripts\out.csv', 'w') as out:
        DF.to_csv(out)