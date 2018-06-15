@echo off

setlocal
SET parent=%~dp0
FOR %%a IN ("%parent:~0,-1%") DO SET grandparent=%%~dpa

set pyScript="plot.py"

python %pyScript%

pause