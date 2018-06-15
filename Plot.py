import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.patches import Polygon
import matplotlib
import numpy as np
from tkinter import filedialog
from tkinter import *


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
        'aenigmatite': 'Angmt'
    }

    beautifulPhases = []
    for env in phases:
        envPhases = []
        for phase in env:
            envPhases.append(shorthands.get(phase.split('_')[0], phase))
        
        beautifulPhases.append(tuple(envPhases))

    return tuple(beautifulPhases)


def phasePLot(xData, yData, phases, deltaPhases, polygons):
    fig, ax = plt.subplots(figsize=(6, 8))

    plt.axis([0, 1.1, min(yData), max(yData)])
    plt.xlabel('Melt fraction (f)')
    plt.ylabel('Temperature (T)')
    plt.grid(alpha=0.5, linestyle='--')

    # Colors
    cmap = matplotlib.cm.get_cmap('Wistia')
    colors = np.linspace(0, 1, len(phases))
    colors = [cmap(color) for color in colors]

    for polygon, phase, color in zip(polygons, phases, colors):
        pltPoly = Polygon(
            polygon,
            facecolor=color,
            edgecolor='0.1',
            label=", ".join(phase))
        ax.add_patch(pltPoly)

    lgd = ax.legend(loc="upper right", ncol=2)
    plt.show()


def welcomeScreen():
    screenTxt = (
        'Welcome\n'
        'Choose option:\n'
        '\t1. Plot Coexisting Phases\n'
        '\t0. Exit\n'
        '\nEnter Your Choice: '
    )
    choice = input(screenTxt)

    return str(choice)


if __name__ == '__main__':
    choice = welcomeScreen()

    while choice != '0':
        if choice == '1':
            root = Tk()
            dir = filedialog.askdirectory()
            root.destroy()

            mainpath = dir + '/'
            DF = pd.read_csv(mainpath + "Phase_main_tbl.csv")

            xData, yData, phases, deltaPhase, polygons = extractData(DF)

            phases = mapPhases(phases)

            phasePlot(xData, yData, phases, deltaPhase, polygons)

        choice = welcomeScreen()