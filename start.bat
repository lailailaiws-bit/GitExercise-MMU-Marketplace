@echo off
echo Starting Tailwind Compiler for Flask...
.\tailwind.exe -i .\static\src\input.css -o .\static\css\output.css --watch
pause