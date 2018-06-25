# alphameltsData
alphaMELTS is a very powerful piece of software, which is very extensively used in modelling of various scenarios of crystallisation as well as of melting. However, one caveat which I faced while using the output of the software, was how the output data was stored, as well as the format in which the data itself is stored in the files. alphameltsData contains a set of utility scripts which can be used to standardize the output from any given alphaMELTS batch run, and clean the workspace for further modelling. Basic plotting of these data can also be done, for obtaining rapid results.

## Scripts
There are two python scripts present in this bundle.
> beautifyData.py <br>
> plot.py

Each of these can either be run, using the `python <script.py>` or using the `<script>.bat` file that is also present in the bundle.

1. Calling the `.bat` files, default settings will be used to run the script.
2. One has to either set the command line parameters, or can use the menu system to input the required data while using `python` to run the scripts.

## How to use these files?
To use these scripts,
1. Download the zip file containing the scripts from the main page of the repository (or use this link: [Download](https://github.com/pritamd47/alphameltsData/archive/master.zip) )
2. Extract the contents of the zip file in a folder named alphameltsData, In your links/ directory (where you run the alphamelts software).
3. Now after you run the alphamelts software, and have the output files, navigate into the alphameltsData folder, and run the `beautifyData.bat` (or you can use python to run the scripts) script to organise the output files and create the respective CSV files. `Plot.bat` can then be used to create necessary plots
