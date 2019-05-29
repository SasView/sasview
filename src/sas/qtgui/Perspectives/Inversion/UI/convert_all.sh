# UI -> PY
for filename in *.ui; do
  pyuic4 $filename > "`basename "$filename" .ui`.py"
done


