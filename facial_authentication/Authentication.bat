@ECHO OFF
rem set pythonPATH=C:\Users\psms\Desktop\facial_authentication\venv38\Scripts
set pythonPATH=.\venv38\Scripts

:BEGINPROGRAM
ECHO -----Activating Environment...-----
rem cmd /c  "cd ..\%pythonPATH% & activate && ECHO Ok: environment activated && cd ..\..\ && %pythonPATH%\python modern_app_authentication.py && ECHO Ok: application ended"
cmd /c  "cd .\venv38\Scripts & activate && ECHO Ok: environment activated && cd ..\..\ && %pythonPATH%\python modern_app_authentication.py && ECHO Ok: application ended"

:ENDPROGRAM
@pause


@ECHO OFF
set pythonPATH=C:\Users\psms\Desktop\facial_authentication\venv38\Scripts

:BEGINPROGRAM
ECHO -----Activating Environment...-----
cmd /c  "cd /d C:\Users\psms\Desktop\facial_authentication\venv38\Scripts & activate && ECHO Ok: environment activated && cd /d C:\Users\psms\Desktop\facial_authentication && python modern_app_authentication.py && ECHO Ok: application ended"

:ENDPROGRAM
@pause