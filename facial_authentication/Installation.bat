@ECHO OFF
set pythonPATH=.\venv38\Scripts
set pythonDefaultLocation=.\Python38\python.exe
set pythonDefaultLocation2= %pythonPATH%\python.exe
ECHO Checking if Python3.8 is installed at default location "%pythonDefaultLocation%"

if exist %pythonDefaultLocation% (
    echo Ok: Python is installed
    ECHO. 
    goto BEGINPROGRAM
) else (
    echo Error: Python3.8 not detected at default location "%pythonDefaultLocation%"
    ECHO. 
    goto ENDPROGRAM
)

:BEGINPROGRAM
if exist venv38\ (
    ECHO -----Deleting existing venv38 folder-----
    @RD /S /Q ".\venv38"
    ECHO Ok: venv38 folder deleted
    ECHO. 
)

ECHO -----Installing virtual environment using Python 3.8-----
virtualenv -p "%pythonDefaultLocation%" ".\venv38" 
ECHO Ok: new virtual environment folder "venv38" created
ECHO. && ECHO.


if exist %pythonDefaultLocation2% (
    ECHO Ok: Python3.8 is installed in "vene38" folder
    ECHO -----Installing additional required packages...-----
    cmd /k  "cd %pythonPATH% & activate && ECHO Ok: environment activated && cd ..\..\library_whl && for %%x in (*.whl) do python -m pip install %%x"
    ECHO Ok: offline packages installed
    ECHO -----ENVIS Authentication is ready to run-----
) else (
    echo Error: Python3.8 not detected at default location "%pythonDefaultLocation2%"
    ECHO. 
    goto ENDPROGRAM
)
:ENDPROGRAM

@pause