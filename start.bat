@echo off
echo Starting Tailwind CSS Compiler...
.\tailwind.exe -i ./static/src/input.css -o ./static/css/output.css --watch
pause