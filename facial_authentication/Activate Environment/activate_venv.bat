@ECHO OFF

set "rootFolder=%cd%"

cmd /k  "cd .\venv38\Scripts\ & activate && cd %rootFolder% && ECHO venv activated"