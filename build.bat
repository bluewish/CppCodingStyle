@echo off
setlocal

set CMPC_SDK_ROOT=%~dp0..\..\..
set project_name=%1
set projectA=%2
if "%project_name%"=="" set project_name=ALL
if "%projectA%"=="" set projectA=/
if "%projectA%"=="/" set projectA=

pushd %cd%
cd /d "%CMPC_SDK_ROOT%\build_framework\windows\script"
call buildhead %*
popd

rem if exist "%CMPC_SDK_ROOT%\CppStyleCheck" rd /S /Q "%CMPC_SDK_ROOT%\CppStyleCheck"

call python "%CMPC_SDK_ROOT%\build_framework\windows\script\exportconfig.py" %CMPC_SDK_ROOT%\%projectA% CppStyleCheck %project_name%

call %project_name%.bat

copy /Y %~dp0\coding_style_check\rule_default.txt "%CMPC_SDK_ROOT%\CppStyleCheck\rule_default.txt"

endlocal