@echo off

rem Used with MS VS2015

set "FILE=%~1"
if "%FILE%" == "" goto :USAGE
if not "%FILE:dll=%" == "%FILE%" goto :DLL
if not "%FILE:def=%" == "%FILE%" goto :DEF
goto :USAGE

:USAGE
echo Usage: %~nx0 {file.dll^|file.def}
goto :EOF

:DLL
set "DEF_FILE=%FILE:dll=def%"
dumpbin /exports "%FILE%" > "%DEF_FILE%"
if %ERRORLEVEL% neq 0 goto :EOF

echo The %DEF_FILE% file has been created. Now edit it in the manner:
echo:
echo EXPORTS
echo funcName1
echo funcName2
echo ...
echo:
echo And then launch:
echo %~nx0 %DEF_FILE%
goto :EOF

:DEF
set "LIB_FILE=%FILE:def=lib%"
lib /def:"%FILE%" /out:"%LIB_FILE%" /machine:x64
if %ERRORLEVEL% neq 0 goto :EOF
goto :EOF
