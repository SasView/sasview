cd UI
./convert_rc.sh main_resources
./convert_all.sh

cd ../images
./convert_rc.sh images
cd ..

cd Perspectives
cd Fitting/UI
./convert_all.sh
cd ../../Invariant/UI
./convert_all.sh

cd ../../../

