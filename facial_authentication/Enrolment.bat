@ECHO OFF
set pythonPATH=.\venv38\Scripts

:BEGINPROGRAM
ECHO -----Activating Environment...-----
cmd /c  "cd %pythonPATH% & activate && ECHO Ok: environment activated && cd ..\..\ && %pythonPATH%\python app_enrolment.py && ECHO Ok: application ended"

:ENDPROGRAM
@pause