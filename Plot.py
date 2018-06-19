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
    reqDF = reqDF.set_index('Temperature')

    # Y Data
    yData = reqDF.index.drop_duplicates()

    # For X Data, which is basically the melt fraction
    xData = []
    for temp in yData:
        F = reqDF.loc[temp, 'F']
        if isinstance(F, np.float64):
            xData.append(F)
        else:
            xData.append(F.values[0])
    
    phases = []
    deltaT = []    

    for temp in reqDF.index:
        avlP = reqDF.loc[temp, 'Phase']
        if isinstance(avlP, str):
            avlP = set([avlP])
        else:
            avlP = set(avlP.values)
            
        if len(phases) == 0:
            phases.append(avlP)
        elif avlP != phases[-1]:
            phases.append(avlP)
            deltaT.append(temp)    

    # Appending last temperature Value
    deltaT.append(reqDF.index[-1])

    polygons = []
    currentPolygon = [
        (0, yData[0]), 
        (xData[0], yData[0])
    ]

    for temperature, F in zip(yData, xData):
        if temperature in deltaT:
            currentPolygon.extend([
                (F, temperature),
                (0, temperature)
            ])
            
            polygons.append(currentPolygon)
            # print("Created Polygon: ", temperature)
            currentPolygon = [
                (0, temperature),
                (F, temperature)
            ]
        else:
            # print("Here: ", temperature)
            currentPolygon.append((F, temperature))

    return xData, yData, phases, deltaT, polygons
    

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


def phasePlot(mainpath, title, outputpath=None):
    filename = "phase_main.csv"
    DF = pd.read_csv(os.path.join(mainpath, filename))

    xData, yData, phases, deltaPhase, polygons = extractData(DF)

    if not title:
        title = input("\nEnter Title for Graph: ")

    phases = mapPhases(phases)

    fig, ax = plt.subplots(figsize=(6, 8))

    plt.axis([0, 1.1, min(yData), max(yData)])
    plt.xlabel('Melt fraction (f)')
    plt.ylabel('Temperature ()')

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

    choice = input("\nDo you want to save? (Y/N): ")
    if choice.upper() == 'Y' and outputpath is None:
        outputpath = input("Where do you want to save (relative path): ")

    if outputpath and choice.upper() == 'Y':
        print("[+] Saving Plot at: {}".format(outputpath))
        if not os.path.exists(outputpath):
            try:
                os.makedirs(outputpath)
            except Exception as e:
                print(e.args)
                sys.exit(2)

        fpath = outputpath + 'phasePlot.svg'
        fig.savefig(fpath, bbox_inches='tight')
        fig.savefig(fpath.split('.')[0]+'.jpg', format='jpg', bbox_inches='tight')


def askAxes(DF):
    columns = list(DF.columns.values)
    options = dict(zip(list(range(len(columns))), columns))

    for key in options.keys():
        print(key, ": ", options[key])
    
    choice = int(input("\nSelect Column (Enter the number against required Data): "))

    if choice in options.keys():
        column = options[choice]
    
    return column


def _plotfractionationScheme(DF, xCol, yCol):
    fig, ax = plt.subplots()

    DF[DF[xCol] is None] = 0.0
    DF[DF[yCol] is None] = 0.0
    
    xData, yData = DF[xCol], DF[yCol]

    plt.plot(xData.values, yData.values)
    plt.scatter(xData[0], yData[0], marker='+', linewidth=20)
    plt.xlabel(xCol)
    plt.ylabel(yCol)
    plt.show()


def fractionationScheme(mainpath, outputpath):
    print("\nChoose DataFrame containing Data")
    DF = askFile("Choose DataFrame")
    
    DF = readDf(DF)

    xData = None
    yData = None
    
    xCol = askAxes(DF)
    yCol = askAxes(DF)

    _plotfractionationScheme(DF, xCol, yCol)


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
    root.destroy()

    return f


def readDf(path):
    DF = pd.read_csv(path)
    return DF


if __name__ == '__main__':
    mainpath, outputpath = askDir()

    choice = welcomeScreen()

    while choice != '0':
        if choice == '1':
            phasePlot(mainpath, "test", outputpath)
        elif choice == '2':
            fractionationScheme(mainpath, outputpath)

        choice = welcomeScreen()