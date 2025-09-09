@ECHO OFF
rem set pythonPATH=C:\Users\psms\Desktop\facial_authentication\venv38\Scripts
set pythonPATH=.\venv38\Scripts

set SCRIPT_NAME = app_authentication.py
set PROCESS_NAME = "Tpython.exe"

tasklist | find "python.exe">nul
if %ERRORLEVEL% equ 0 (
	echo Script is already running.
	exit
)

:BEGINPROGRAM
ECHO -----Activating Environment...-----
rem cmd /c  "cd ..\%pythonPATH% & activate && ECHO Ok: environment activated && cd ..\..\ && %pythonPATH%\python app_authentication.py && ECHO Ok: application ended"
cmd /c  "cd .\venv38\Scripts & activate && ECHO Ok: environment activated && cd ..\..\ && %pythonPATH%\python app_authentication.py && ECHO Ok: application ended"

:ENDPROGRAM
@pause