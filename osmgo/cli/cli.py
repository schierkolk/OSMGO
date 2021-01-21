import os
import sys
import click
from osmgo.extract import write_poly, write_pbf
from osmgo.osmprocess import ProcessOSM, kill_child_processes
from osmgo.util import combine_gpkg
#from concurrent.futures import ProcessPoolExecutor, as_completed


@click.group()
def cli():
    pass


'''
osmgo andorra-latest.osm.pbf C:/OSM/output -c C:/OSM/andorra.shp -w 4 
'''


# noinspection SpellCheckingInspection
@cli.command('export', short_help='Export PBF to shp,geojson,gpkg')
@click.argument('inputs', type=click.Path(exists=True))
@click.argument('output', type=click.Path(exists=True))
@click.argument('prefix', type=str)
@click.option('-c', '--clip_data', type=click.Path(exists=True), help='Path to clip *.shp')
@click.option('-b', '--bbox', type=str, help='minx,miny,maxx,maxy in decimal degrees')
@click.option('-l', '--layer', type=str, help='layer name used in gdb')
@click.option('-t', '--theme', type=str, help='Individual themes in a comma separated list.')
@click.option('-f', '--feature', type=str, help='Feature type point,line,polygon')
@click.option('-w', '--workers', type=int, default=1, show_default=True, help='Number of workers')
@click.option('-e', '--ext', type=str, default='shp', show_default=True, help='shp,geojson,gpkg')
@click.option('--keep', is_flag=True, show_default=True, help='Keep bad geometries')
def export(inputs, output, prefix, clip_data, theme, feature, workers, ext, keep, bbox, layer):
    # noinspection SpellCheckingInspection
    """

        INPUTS is the name of the PBF file

        OUTPUT is the name of the output folder

        PREFIX is the name added to the front of the export

        Theme options include:

        aerialway,aeroway,amenity,barrier,boundary,building,craft,emergency,geological,
        highway,historic,landuse,leisure,man_made,military,natural,office
        ,place,power,public_transport,railway,route,shop,sport,tourism ,waterway

        The --keep if set retains invalid polygons geometries from the OSM and does not clip the data

        Example:

        osmgo export andorra-latest.osm.pbf output andorra-l-nstfs -t highway -f line -c andorra_hole.shp

        osmgo export andorra-latest.osm.pbf  output andorra_e_l-ns3  -t highway -f line -b 1.4275,42.4705,1.7201,42.6325

        osmgo export andorra-latest.osm.pbf  output andorra_e_l-ns3  -t highway -f line  -c ../andorra.gdb -l andorra_hole
        """

    print(f'Input PBF: {inputs}')
    print(f'Output folder: {output}')
    print(f'Output prefix: {prefix}')
    if clip_data is not None:
        print(f'Clip data: {clip_data}')
    if layer is not None:
        print(f'Layer data: {layer}')

    print(f'Workers: {workers}')
    print(f'Keep bad geometries: {keep}')

    if ext not in ['shp', 'geojson', 'gpkg']:
        print('Please select valid extension')
        exit()
    else:
        print(f'Output extension: {ext}')

    _themes = ['aerialway', 'aeroway', 'amenity', 'boundary', 'building', 'craft', 'emergency', 'geological',
               'highway', 'historic', 'landuse', 'leisure', 'natural', 'office', 'place', 'power', 'public_transport',
               'railway', 'route', 'shop', 'tourism', 'waterway']

    if theme is None:
        themes = _themes
    else:
        themes = []
        for each in theme.split(','):
            each = each.strip()
            if each in _themes:
                themes.append(each)
            else:
                print(f'Theme {each} is misspelled or missing')
                exit()
    print('Processing the following themes {}'.format(','.join(themes)))

    _features = ['point', 'line', 'polygon']

    if feature is None:
        features = _features
    else:
        features = []
        for each in feature.split(','):
            each = each.strip()
            if each in _features:
                features.append(each)
            else:
                print(f'Feature {each} is misspelled or missing')
                exit()
    print('Processing the following features {}'.format(','.join(features)))

    if bbox is None:
        box = None
    else:
        box = []
        for each in bbox.split(','):
            each = each.strip()
            try:
                box.append(float(each))
            except ValueError:
                print(f'{each} not a integer or float value')
                exit()
        if box[0] >= box[2] or box[1] >= box[3]:
            print('Coordinates out of sequence')
            exit()
        print(f'Bounding box {box}')
    if clip_data is not None and bbox is not None:
        print('Clip data and BBOX selected')
        exit()

    if clip_data is not None:
        if os.path.splitext(clip_data)[-1] not in ['.shp', '.gdb']:
            print('Clip data not a .shp or .gdb')
            exit()

        if os.path.splitext(clip_data)[-1] == '.gdb' and layer is None:
            print('GDB missing layer flag')
            exit()

    # process(input, output, themes, features,workers,clip_data)
    posm = ProcessOSM(inputs, output, prefix, ext, themes, features)

    if workers > 1:
        posm.workers = workers

    if clip_data is not None:
        posm.clip_data = clip_data
        if layer is not None:
            posm.layer = layer

    if keep:
        posm.keep = True

    if bbox is not None:
        posm.bbox = box

    posm.process()

    #
    # futures = []
    # with ProcessPoolExecutor(max_workers=posm.workers) as executor:
    #     for theme in posm.themes:
    #         futures.append(executor.submit(posm.process_key, theme))
    #
    #     for x in as_completed(futures):
    #         if x.exception() is not None:
    #             print(f'Future Exception {x.exception()}')
    #             # Kill remaining child processes
    #             kill_child_processes(os.getpid())
    #

'''
OSMCONVERT is installed in the python env bin folder on Linux systems
Environment variable can be set or passed in as an argument as well
Windows example
set OSMCONVERT=C:/OSM/source/OSMtoGDB/Install/osmconvert.exe

Example syntax
osmgo extract andorra-latest.osm.pbf andorra-extract_sub1.pbf -c andorra_hole.shp
'''


@cli.command('extract', short_help='Extract PBF file based on shapefile')
@click.argument('inputs', type=click.Path(exists=True))
@click.argument('output', type=click.Path())
@click.option('-c', '--clip_data', type=click.Path(exists=True), help='Path to clip *.shp')
@click.option('-b', '--bbox', type=str, help='minx,miny,maxx,maxy in decimal degrees')
@click.option('-l', '--layer', type=str, help='layer name used in gdb')
@click.option('--osmconvert', envvar='OSMCONVERT', help='Path to osmconvert file')
def extract(inputs, output, osmconvert, bbox, clip_data, layer):
    """
    Extract PBF file

    Example:

    osmgo extract andorra-latest.osm.pbf andorra-extract_sub1.pbf -c andorra_hole.shp

    osmgo extract andorra-latest.osm.pbf andorra-extract_lc.pbf -b 1.4275,42.4705,1.7201,42.6325

    osmgo extract andorra-latest.osm.pbf andorra-extract_lc.pbf -c andorra.gdb -l andorra_hole

    osmgo extract andorra-latest.osm.pbf andorra-extract_lc.pbf -c andorra_hole.shp
    """
    if os.path.exists(os.path.join(sys.prefix, 'bin/osmconvert')):
        osmconvert = os.path.join(sys.prefix, 'bin/osmconvert')
    elif os.path.exists(osmconvert):
        osmconvert = osmconvert
    else:
        print('Unable to find osmconvert program in {} or {}'.format(os.path.join(sys.prefix, 'bin/osmconvert'),
                                                                     osmconvert))
        exit()

    print(f'Path to osmconvert: {osmconvert}')
    if bbox is None:
        box = None
    else:
        box = []
        for each in bbox.split(','):
            each = each.strip()
            try:
                box.append(float(each))
            except ValueError:
                print(f'{each} not a integer or float value')
                exit()
        if box[0] >= box[2] or box[1] >= box[3]:
            print('Coordinates out of sequence')
            exit()
        print(f'Bounding box {box}')
    if clip_data is not None and bbox is not None:
        print('Clip data and BBOX selected')
        exit()

    if clip_data is not None:
        ext = ['.shp', '.gdb']
        if os.path.splitext(clip_data)[-1] not in ext:
            print('Clip data not a .shp or .gdb')
            exit()

        if os.path.splitext(clip_data)[-1] == '.gdb' and layer is None:
            print('GDB missing layer flag')
            exit()

    if clip_data is not None:
        if os.path.splitext(clip_data)[-1] == '.shp':
            poly = write_poly(clip_data, output)
            write_pbf(inputs, output, osmconvert, poly=poly)
        else:
            poly = write_poly(clip_data, output, layer=layer)
            write_pbf(inputs, output, osmconvert, poly=poly)
    elif box is not None:
        print('bbox')
        write_pbf(inputs, output, osmconvert, bbox=box)
    else:
        write_pbf(inputs, output, osmconvert)


@cli.command('combine', short_help='Combine gpkg')
@click.argument('inputs', type=click.Path(exists=True))
@click.argument('output', type=click.Path())
@click.argument('prefix', type=str)
def combine(inputs, output, prefix):
    """
        INPUTS folder of GPKG

        OUTPUT GPKG

        PREFIX of the GPKG in INPUTS folder
    """
    if os.path.exists(output):
        print(f'{output} already exists please delete before continuing')
        exit()
    combine_gpkg(inputs, output, prefix)
