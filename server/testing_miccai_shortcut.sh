# register dataset
medperf auth login -e traincol2@example.com
medperf dataset create -p 1 -d ../../datasets_folder_final/col2 -l ../../datasets_folder_final/col1 --name col2 --description col2data --location col2location
medperf dataset submit -d 54ea1643f6006ead7e8517cd65fd5275f99abe7349895be25bd8485761cde088 -y

# associate dataset
medperf training associate_dataset -t 1 -d 2 -y
