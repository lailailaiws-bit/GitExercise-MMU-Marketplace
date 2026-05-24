@echo off
echo Starting Tailwind Compiler for Flask...
npx @tailwindcss/cli -i .\static\src\input.css -o .\static\css\output.css --watch
pause