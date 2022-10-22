@echo off

rem Used with MS VS2015

set SELF_HOME=%~dp0
set SELF_NAME=microhttp

set SELF_SRC=src\dllmain.cpp src\api.cpp
set SELF_OBJ=%SELF_SRC:.cpp=.obj%

set LUA_HOME=%SELF_HOME%\contrib\lua\lua-5.4.2-win64-vc15
set LUA_INCLUDE=%LUA_HOME%\include

set QUIK_HOME=%SELF_HOME%\contrib\quik\quik-9.2.3.15
set LUA_LIB=%QUIK_HOME%\lib\lua54.lib

set CURL_HOME=%SELF_HOME%\contrib\curl\curl-7.82.0-win64-mingw
set CURL_INCLUDE=%CURL_HOME%\include
set CURL_LIB=%CURL_HOME%\lib\libcurl.dll.a

set BUILD_DIR=%SELF_HOME%\build
if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"
cd "%BUILD_DIR%"

call vcvars64.bat

cl /c /MT /EHsc /I%LUA_INCLUDE% /I%CURL_INCLUDE% %SELF_SRC:src\=..\src\%
if %ERRORLEVEL% neq 0 goto :EOF

link /DLL %LUA_LIB% %CURL_LIB% %SELF_OBJ:src\=% /OUT:%SELF_NAME%.dll
if %ERRORLEVEL% neq 0 goto :EOF
