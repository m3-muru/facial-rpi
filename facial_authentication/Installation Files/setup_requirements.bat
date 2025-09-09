@ECHO OFF

set pythonDefaultLocation=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python38\python.exe
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
virtualenv -p "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python38\python.exe" ".\venv38" 
ECHO Ok: new virtual environment folder "venv38" created
ECHO. && ECHO. 

ECHO -----Installing additional required packages...-----
cmd /k  "cd .\venv38\Scripts\ & activate && pip install -r ..\..\requirements.txt && cd ..\..\ && ECHO Ok: packages installed"


:ENDPROGRAM

@pause