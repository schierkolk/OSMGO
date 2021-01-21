import os
import geopandas as gpd
import subprocess


def write_pbf(inputs, output, osmconvert, poly=None, bbox=None):
    """
        Run osmcovert to clip and/or write pbf file
    """
    cmd = None
    try:

        if poly is not None:
            cmd = '{}  {} -B={} -o={} -t={}/osm_temp'.format(osmconvert, inputs, poly, output, os.path.dirname(output))
            subprocess.run(cmd, shell=True)

        elif bbox is not None:
            cmd = '{} {} -b={},{},{},{} -o={} -t={}/osm_temp'.format(osmconvert, inputs, bbox[0], bbox[1], bbox[2],
                                                                     bbox[3], output, os.path.dirname(output))
            subprocess.run(cmd, shell=True)

        else:
            cmd = '{}  {} -o={} -t={}/osm_temp'.format(osmconvert, inputs, output, os.path.dirname(output))
            subprocess.run(cmd, shell=True)

    except subprocess.CalledProcessError as e:
        print(e.output)
        print('Unable to finish export')
        print(cmd)


def write_poly(clip_data, output, layer=None):
    """
        Read shapefile and write *.poly file for use with osmconvert
    """
    if os.path.splitext(clip_data)[-1] == '.shp':
        print('Processing shapefile')
        wb_poly = gpd.read_file(clip_data)
        attr = os.path.basename(clip_data).split('.')[0]
    else:
        print('Processing FileGDB')
        wb_poly = gpd.read_file(clip_data, driver="FileGDB", layer=layer)
        attr = layer

    poly = os.path.join(os.path.dirname(output), f'{attr}.poly')
    with open(poly, 'w') as fp:
        fp.write(attr + "\n")
        total_ring_count = 0
        for _, f in wb_poly.iterrows():
            geom = f.geometry
            coordinates = extract_coords(geom)
            for coordinate in coordinates:

                fp.write('{0}\n'.format(total_ring_count))
                for coords in coordinate[0]['exterior_coords']:
                    x = '{:.7E}'.format(coords[0])
                    y = '{:.7E}'.format(coords[1])
                    fp.write('\t{0}\t{1}\n'.format(x, y))
                fp.write("END\n")
                total_ring_count += 1
                for rings in coordinate[0]['interior_coords']:
                    fp.write('!{0}\n'.format(total_ring_count))
                    for coords in rings:
                        x = '{:.7E}'.format(coords[0])
                        y = '{:.7E}'.format(coords[1])
                        fp.write('\t{0}\t{1}\n'.format(x, y))
                    total_ring_count += 1
                    fp.write("END\n")

        fp.write("END\n")
    return poly


def extract_coords(geom):
    coords = []
    if geom.type == 'Polygon':
        coords.append(extract_poly_coords(geom))
    elif geom.type == 'MultiPolygon':
        coords.extend(extract_multi_poly_coords(geom))
    else:
        raise ValueError('Unhandled geometry type: ' + repr(geom.type))
    return coords


def extract_poly_coords(geom):
    exterior_coords = None
    interior_coords = None
    if geom.type == 'Polygon':
        exterior_coords = geom.exterior.coords[:]
        interior_coords = []
        for interior in geom.interiors:
            interior_coords.append(interior.coords[:])

    return [{'exterior_coords': exterior_coords,
             'interior_coords': interior_coords}]


# noinspection SpellCheckingInspection
def extract_multi_poly_coords(geom):
    coords = []
    if geom.type == 'MultiPolygon':
        for part in geom:
            coords.append(extract_poly_coords(part))  # Recursive call
    return coords
