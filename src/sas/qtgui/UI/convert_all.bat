@echo off

for %%f in (*.ui) do (
  pyuic4.bat -w %%f > %%~nf.py
)


