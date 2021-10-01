@if (@a==@b) @end /*

:: fchooser2.bat
:: batch portion

@echo off
setlocal

for /f "delims=" %%I in ('cscript /nologo /e:jscript "%~f0"') do (
    echo You chose %%I
)

goto :EOF

:: JScript portion */

var shl = new ActiveXObject("Shell.Application");
var folder = shl.BrowseForFolder(0, "Select your IDA Installation", 0, 0x00);
WSH.Echo(folder ? folder.self.path : '');