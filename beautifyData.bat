@echo off
setlocal
set parent=%~dp0
FOR %%a IN ("%parent:~0,-1%") DO SET grandparent=%%~dpa

set pyScript="beautifyData.py"

python %pyScript% -i %grandparent%

pause