import glob
import os
import geopandas as gpd
import fiona


def combine_gpkg(inputs, outputs, prefix):

    all_gpkg = glob.glob(os.path.join(inputs, '*gpkg'))
    target_gpkg = []
    if len(all_gpkg) > 0:
        for each in all_gpkg:
            if prefix in each:
                target_gpkg.append(each)
        for each in target_gpkg:
            if len(fiona.listlayers(each)) == 1:
                layername = fiona.listlayers(each)[0]
                print(layername)
                gdf = gpd.read_file(each, layer=layername)
                gdf.to_file(outputs, layer=layername, driver="GPKG")

    else:
        print('No input files found')

    # combine_gpkg('/vagrant/output','/vagrant/test.gpkg','andorra_e_l-ns3')
