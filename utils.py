from collections import deque
import pandas as pd
from datetime import datetime as dt
import os
import sys
import getopt
import re
from tkinter import filedialog
from tkinter import *


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
        print("[+] Moving {} to {}".format(origin, destination))
        os.rename(origin, destination)


def writeCSV(data, outputDir):
    """
    Takes in a dictionary of DataFrames with the names of their proposed file
    nanmes as the keys to the DataFrame
    
    Arguments:
        data: dictionary of DataFrames with the names of their files as the
            keys
        outputDir: Path to the directory where the CSV files are to saved
    """

    if not os.path.isdir(outputDir):
        os.makedirs(outputDir)

    for key in data.keys():
        filename = key + ".csv"
        outputPath = os.path.join(outputDir, filename)
    
        with open(outputPath, 'w') as out:
            print("[+] Writing CSV at: {}".format(outputPath))
            data[key].to_csv(out)


def figureoutTable(filepath):
    """Figures out whoch table is this. Reads the file, and using regex mathes,
    returns the value corresponding to the type of table the file contains
    
    Arguments:
        filepath {str} -- path of the file containing the table
    """
    with open(filepath) as f:
        output = deque(f.readlines())
        Title = output.popleft()

        _ = output.popleft()

        # Guide:
        # 1. phase_main_tbl.txt (type 1) -- Starts with liquid_0 thermodynamic..
        # 2. phase_main_tbl.txt (type 2) -- Starts with P T ...
        # 3. phase_mass_tbl.txt -- starts with Phase Masses
        # 4. phase_vol_tbl.txt -- starts with Phase Volumes
        # 5. solid_comp_tbl.txt -- starts with Solid Composition
        # 6. system_mail_tbl.txt -- starts with System Thermodynamic data
        # 7. trace_main_tbl.txt -- starts as P Pval T Tval
        # 8. bulk_comp_tbl.txt -- starts with Bulk Composition

        tbl = None
        if bool(re.search(r'[a-z]+_[0-9] ([a-z]+[ |:])+', output[0])):
            # phase_main_tbl (type 1)
            tbl = 1
        elif bool(re.search(r'^([A-Za-z]+ [0-9]+\.?[0-9]{2}? ){2}\b', output[0])):
            # phase_main_tbl (type 2)
            tbl = 2
        elif bool(re.search(r'Phase Masses:',output[0])):
            # phase_mass_tbl
            tbl = 3
        elif bool(re.search(r'Phase Volumes:', output[0])):
            # phase_vol_tbl
            tbl = 4
        elif bool(re.search(r'Solid Composition:', output[0])):
            # solid_comp_tbl
            tbl = 5
        elif bool(re.search(r'System Thermodynamic Data:', output[0])):
            # system_main_tbl
            tbl = 6
        elif bool(re.search(r'^([A-Za-z]+ [0-9]+\.?[0-9]{2}? ?){2}$', output[0])):
            tbl = 7
        elif bool(re.search(r'Bulk Composition:', output[0])):
            tbl = 8
        else:
            tbl = 0

    return tbl


def _separatePhaseFiles(phaseMainDF):
    Data = dict()
    for phase in phaseMainDF['Phase'].unique():
        Data[phase] = phaseMainDF[phaseMainDF['Phase'] == phase]
    
    return Data


## Plot.py

def askDir(lookfor='Working Directory'):
    print("Please select the Working Directory")

    if lookfor:
        title = 'Select the {}'.format(lookfor)
    else:
        title = 'Select Folder'
    
    # Make a top-level instance and hide since it is ugly and big.
    root = Tk()
    root.withdraw()

    # Make it almost invisible - no decorations, 0 size, top left corner.
    root.overrideredirect(True)
    root.geometry('0x0+0+0')

    # Show window again and lift it to top so it can get focus,
    # otherwise dialogs will end up behind the terminal.
    root.deiconify()
    root.lift()
    root.focus_force()

    dir = filedialog.askdirectory(
        initialdir=os.getcwd(),
        title=title
    )
    root.withdraw()
    root.destroy()

    dir += '/'
    outputpath = dir + 'plots/'

    return dir, outputpath


def _choice(ask):
    choice = input("\n" + ask + " (Y/N): ")
    if choice.capitalize() == 'Y':
        return True
    else:
        return False


def askFile(lookfor=None):
    if lookfor:
        title = lookfor
    else:
        title = "Select File"
    
    # Make a top-level instance and hide since it is ugly and big.
    root = Tk()
    root.withdraw()

    # Make it almost invisible - no decorations, 0 size, top left corner.
    root.overrideredirect(True)
    root.geometry('0x0+0+0')

    # Show window again and lift it to top so it can get focus,
    # otherwise dialogs will end up behind the terminal.
    root.deiconify()
    root.lift()
    root.focus_force()

    f = filedialog.askopenfilename(title=title)
    root.destroy()

    return f
