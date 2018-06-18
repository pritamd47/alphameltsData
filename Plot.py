import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.patches import Polygon
import matplotlib
from matplotlib.ticker import MultipleLocator
import numpy as np
from tkinter import filedialog
from tkinter import *
import os


def extractData(DF):
    reqDF = DF[['Temperature', 'Phase', 'Mass', 'F']]

    yData = reqDF['Temperature'].drop_duplicates().values.tolist()

    # For X Data, which is basically the melt fraction
    xData = list(pd.unique(reqDF['F']))

    # list for listing the phases
    phases = []

    # list for storing the temperatures where the phases change
    deltaPhase = []

    for temperature in yData:
        
        currentT = reqDF[reqDF['Temperature'] == temperature]
        
        currentPhases = tuple(currentT['Phase'].values)
        
        if len(phases) == 0:
            phases.append(currentPhases)
            
        if phases[-1] != currentPhases:
            deltaPhase.append(temperature)
            phases.append(currentPhases)

    polygons = []
    currentPolygon = [
        (0, yData[0]), 
        (xData[0], yData[0])
    ]

    for temperature, F in zip(yData, xData):
        if temperature in deltaPhase:
            currentPolygon.extend([
                (F, temperature),
                (0, temperature)
            ])
            
            polygons.append(currentPolygon)
            currentPolygon = [
                (0, temperature),
                (F, temperature)
            ]
        else:
            currentPolygon.append((F, temperature))

    return xData, yData, phases, deltaPhase, polygons
    

def mapPhases(phases):
    shorthands = {
        'liquid': 'Lq',
        'feldspar': 'Fs',
        'kfeldspar': 'KFs',
        'quartz': 'Qtz',
        'orthopyroxene': 'Opx',
        'clinopyroxene': 'Cpx',
        'garnet': 'Grt',
        'spinel': 'Spi',
        'aenigmatite': 'Angmt',
        'olivine': 'Ol'
    }

    beautifulPhases = []
    for env in phases:
        envPhases = []
        for phase in env:
            envPhases.append(shorthands.get(phase.split('_')[0], phase))
        
        beautifulPhases.append(tuple(envPhases))

    return tuple(beautifulPhases)


def phasePlot(DF, title, outputpath=None):
    xData, yData, phases, deltaPhase, polygons = extractData(DF)

    title = input("\nEnter Title for Graph: ")

    phases = mapPhases(phases)

    fig, ax = plt.subplots(figsize=(6, 8))

    plt.axis([0, 1.1, min(yData), max(yData)])
    plt.xlabel('Melt fraction (f)')
    plt.ylabel('Temperature (T)')

    minorLocator = MultipleLocator(5)
    majorLocator = MultipleLocator(20)
    ax.yaxis.set_minor_locator(minorLocator)

    plt.grid(alpha=0.5, linestyle='--')
    plt.title(title)

    # Colors
    cmap = matplotlib.cm.get_cmap('Wistia')
    colors = np.linspace(0, 1, len(phases))
    colors = [cmap(color) for color in colors]

    for polygon, phase, color in zip(polygons, phases, colors):
        pltPoly = Polygon(
            polygon,
            facecolor=color,
            edgecolor='0.1',
            label=" + ".join(phase)
        )
        ax.add_patch(pltPoly)

    lgd = ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
    
    choice = input("\nDo you want to see the plot? (Y/N): ")

    if choice.upper() == 'Y':
        plt.show()

    choice("\nDo you want to save? (Y/N): ")
    if choice.upper() == 'Y' and outputpath == None:
        outputpath = input("Where do you want to save (relative path): ")

    if outputpath:
        print("[+] Saving Plot at: {}".format(outputpath))
        if not os.path.exists(outputpath):
            try:
                os.makedirs(outputpath)
            except Exception as e:
                print(e.args)
                sys.exit(2)

        fpath = outputpath + 'phasePlot.svg'
        plt.savefig(fpath, bbox_inches='tight')
        plt.savefig(fpath.split('.')[0]+'.jpg', format='jpg', bbox_inches='tight')


def askAxes(DF):
    columns = list(DF.columns.values)

    options = dict(zip(list(range(len(columns))), columns))

    print(options)


def fractionationScheme(mainpath, outputpath):
    print("\nChoose DataFrame for X Data")
    DF1 = askFile("Choose DataFrame for X Data")

    choice = input("\nIs the Y Data in the same Dataframe? (Y/N): ")

    if choice.upper() == 'Y':
        DF2 = DF1
    else:
        DF2 = askFile("Choose DataFrame for Y Data")
    
    DF1, DF2 = readDf(DF1), readDf(DF2)

    xData = askAxes(DF1)



def welcomeScreen():
    screenTxt = (
        'Welcome\n'
        'Choose option:\n'
        '\t1. Plot Coexisting Phases\n'
        '\t2. Plot Fractionation Scheme\n'
        '\t0. Exit\n'
        '\nEnter Your Choice: '
    )
    choice = input(screenTxt)

    return str(choice)


def askDir(lookfor='Working Directory'):
    print("Please select the Working Directory")

    if lookfor:
        title = 'Select the {}'.format(lookfor)
    else:
        title = 'Select Folder'

    root = Tk()
    dir = filedialog.askdirectory(
        initialdir=os.getcwd(),
        title=title
    )
    root.withdraw()
    root.destroy()

    dir += '/'
    outputpath = dir + 'plots/'

    return dir, outputpath


def askFile(lookfor=None):
    if lookfor:
        title = lookfor
    else:
        title = "Select File"
    
    root = Tk()
    f = filedialog.askopenfilename(title=title)

    return f


def readDf(path):
    DF = pd.read_csv(path)
    return DF


if __name__ == '__main__':
    mainpath, outputpath = askDir()

    choice = welcomeScreen()

    while choice != '0':
        if choice == '1':
            phasePlot(DF, outputpath)
        elif choice == '2':
            fractionationScheme(mainpath, outputpath)

        choice = welcomeScreen()