Installation
CD into the deliver folder
	There should be a environmental.yml and the osmgo folder 
Create conda environment
	conda env create
	conda activate osm2go
Test PYROSM installation
	python -c 'import pyrosm'
	If there are no errors, then the package was install successfully
Install OSMGO
	pip install . -v
	Be sure to include the .
	Successfully installed osmgo-0.2
	*Osmconvert is automatically compiled during the install on Linux systems
	By using the -v you should see:
	    running install
        Linux
        cc osmgo/osmconvert/osmconvert.c -lz -O3 -o /home/vagrant/miniconda3/envs/osm2go/bin/osmconvert
Notes
    PYROSM uses a significant amount om memory to open and filter the PBF files. Precautions have been added in the form
    of exceptions to the code to reduce the chances of a runaway process.

    Shapefile have a file size limitation

    Geopackages writ faster that shapefiles

Test OSMGO command line help

(osm2go) C:\OSM\vagrant\test>osmgo
Usage: osmgo [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  combine  Combine gpkg
  export   Export PBF to shp,geojson,gpkg
  extract  Extract PBF file based on shapefile
  
Example commands
	osmgo export ../andorra-latest.osm.pbf  ../output andorra-l-nst -t highway
	osmgo export ../andorra-latest.osm.pbf  ../output andorra-l-nstf -t highway -f line
	osmgo export ../andorra-latest.osm.pbf  ../output andorra-l-nsws  -w 2 -c ../andorra_hole.shp
	osmgo extract ../andorra-latest.osm.pbf ../andorra-extract_lc.pbf -c ../andorra_hole.shp