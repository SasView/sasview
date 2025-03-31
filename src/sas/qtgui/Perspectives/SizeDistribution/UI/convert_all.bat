@echo off

for %%f in (*.ui) do (
  call pyuic4.bat %%f > %%~nf.py
)


