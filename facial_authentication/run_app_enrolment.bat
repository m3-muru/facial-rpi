@ECHO OFF
ECHO -----Checking for python...-----
set pythonPATH=.\venv38\Scripts
set pythonDefaultLocation=.\venv38\Scripts\python.exe
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
ECHO -----Activating Environment...-----
cmd /c  "cd .\venv38\Scripts\ & activate && ECHO Ok: environment activated && cd ..\..\ && %pythonPATH%\python app_enrolment.py && ECHO Ok: application ended"

:ENDPROGRAM

@pause