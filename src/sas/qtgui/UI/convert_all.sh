# UI -> PY
for filename in *.ui; do
  pyuic.bat $filename > "`basename "$filename" .ui`.py"
done


