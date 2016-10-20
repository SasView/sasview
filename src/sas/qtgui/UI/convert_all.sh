# UI -> PY
for filename in *.ui; do
  pyuic4.bat $filename > "`basename "$filename" .ui`.py"
done


