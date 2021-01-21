from pyrosm import OSM
from concurrent.futures import ProcessPoolExecutor, as_completed
import time
import geopandas as gpd
import os
from pygeos import GEOSException
from shapely.geometry import Polygon

import signal
import psutil


def kill_child_processes(parent_pid, sig=signal.SIGTERM):
    try:
        parent = psutil.Process(parent_pid)
    except psutil.NoSuchProcess:
        return
    children = parent.children(recursive=True)
    for process in children:
        process.send_signal(sig)


class ProcessOSM:
    """
        Processing Class
    """

    def __init__(self, inputs, output, prefix, ext, themes, features):
        self.inputs = inputs
        self.output = output
        self.themes = themes
        self.features = features
        self.workers = 1
        self.clip_data = None
        self.clip_gdf = None
        self.osm = None
        self.keep = False  # False removes invalid geometries
        self.show_warning = False
        self.prefix = prefix
        self.ext = ext
        self.bbox = None
        self.layer = None

    def process(self):
        """
        Handle general multiprocessing workflow.  
        """

        # if self.show_warning:
        #    warnings.filterwarnings("ignore")
        # warnings.filterwarnings("ignore")

        begin_time = time.time()
        if self.clip_data is not None:
            if self.layer is None:
                self.clip_gdf = gpd.read_file(self.clip_data)
            else:
                try:
                    self.clip_gdf = gpd.read_file(self.clip_data, driver="FileGDB", layer=self.layer)
                except ValueError as e:
                    print(e)
                    exit()

            geo = self.clip_gdf.geometry.unary_union
            self.osm = OSM(self.inputs, geo)
        elif self.bbox is not None:
            self.osm = OSM(self.inputs, self.bbox)

            # Create Clip GDF from bbox coordinate
            p = Polygon([(self.bbox[0], self.bbox[1]), (self.bbox[0], self.bbox[3]),
                         (self.bbox[2], self.bbox[3]), (self.bbox[2], self.bbox[1])])
            self.clip_gdf = gpd.GeoDataFrame({'geometry': [p]}, geometry='geometry')
            self.clip_gdf.set_crs(epsg=4326, inplace=True)
        else:
            self.osm = OSM(self.inputs)

        # self.process_key(self.themes[8])

        # for theme in self.themes:
        #    self.process_key(theme)

        futures = []
        with ProcessPoolExecutor(max_workers=self.workers) as executor:
            for theme in self.themes:
                futures.append(executor.submit(self.process_key, theme))
            # for f in futures:
            #    print(f, 'running?', f.running())
            for x in as_completed(futures):

                #for f in futures:
                #    print(f, 'running?', f.running())
                if x.exception() is not None:
                    print(f'Future Exception {x.exception()}')
                    # Kill remaining child processes
                    kill_child_processes(os.getpid())
                    # Plagued by general memory errors from pyrosm
                    # Consumes all memory ram/swap then hangs machine
                    # you can't cancel an active job
                    # shutdown only cancels queued tasks not active tasks
                    # only thing left to do is kill processes if there is an error

                    #print('cancel')
                    #for f in futures:
                    #    f.cancel()
                    # executor.shutdown(wait=False)
                    # for f in futures:
                    #     f.cancel()
                    #     print(f, 'running?', f.running())
                    #     if f.running():
                    #         f.cancel()
                    #         print('Cancelled? ', f.cancelled())
                    # exit()

                #try:
                #    print(x.result())
                #except Exception as exc:
                #    print(f'generated an exception: {exc}')
                #    exit()

        total_time = time.time() - begin_time
        print('Done after {} seconds.'.format(round(total_time, 0)))

    def process_key(self, theme):
        """
        Workflow for processing OSM data
        """
        begin_time = time.time()
        geod = {'point': ['Point', 'MultiPoint'], 'line': ['LineString', 'MultiLineString'],
                'polygon': ['Polygon', 'MultiPolygon']}
        print(f'Processing PBF for {theme}')
        try:
            gdf = self.osm.get_data_by_custom_criteria(osm_keys_to_keep=theme, custom_filter={theme: True})
        except Exception as e:
            print('Bad Mojo')
            print(f'Exception Exit {e} theme :{theme}')
            raise #RuntimeError(f'Exception Exit {e}')
            #exit()

        print('Done PBF for {} after {} seconds.'.format(theme, round(time.time() - begin_time, 0)))
        if gdf is not None:
            theme_time = time.time()
            gdf['geom_type'] = gdf.geometry.geom_type

            for geo in self.features:
                print(f'Processing {theme}:{geo}')
                theme_time = time.time()
                gdf_select = gdf[gdf["geom_type"].isin(geod[geo])]
                if not gdf_select.empty:
                    if self.clip_gdf is not None:
                        try:
                            # Remove bad geometries in OSM file before clipping
                            if not self.keep:
                                start = gdf_select.shape[0]
                                gdf_select = gdf_select[gdf_select.geometry.is_valid]
                                if start != gdf_select.shape[0]:
                                    end = start - gdf_select.shape[0]
                                    print(f'\tRemoving {end} geometries from {theme}:{geo}')
                            gdp_clip = gpd.clip(gdf_select, self.clip_gdf)
                            print('{}:{} shape {}'.format(theme, geo, gdp_clip.shape))
                            print('Done Geodataframe processing: {}:{} after {} seconds .'.format(theme, geo,
                                                                                round(time.time() - theme_time, 0)))

                            self.write_data(gdp_clip, theme, geo)
                        except GEOSException:

                            print(f'Unable to clip {theme}:{geo} exporting unclipped')
                            self.write_data(gdf_select, theme, geo)
                            continue
                    else:
                        print('{}:{} shape {}'.format(theme, geo, gdf_select.shape))
                        print('Done Geodataframe processing: {}:{} after {} seconds .'.format(theme, geo,
                                                                                    round(time.time() - theme_time, 0)))

                        self.write_data(gdf_select, theme, geo)
                else:
                    print(f'\tEmpty dataframe {theme}:{geo}')
        else:
            print(f'\tEmpty theme {theme}')

        total_time = time.time() - begin_time
        print('Done {} after {} seconds.'.format(theme, round(total_time, 0)))
        return theme

    # noinspection SpellCheckingInspection
    def write_data(self, gdf_write, theme, geo):
        begin_time = time.time()
        if self.ext == 'shp':
            outputfile_shp = os.path.join(self.output, f'{self.prefix}_{theme}_{geo}.shp')
            gdf_write.to_file(outputfile_shp)
        elif self.ext == 'geojson':
            outputfile_gjson = os.path.join(self.output, f'{self.prefix}_{theme}_{geo}.geojson')
            gdf_write.to_file(outputfile_gjson, driver='GeoJSON')
        else:
            outputfile_gpkg = os.path.join(self.output, f'{self.prefix}_{theme}_{geo}.gpkg')
            gdf_write.to_file(outputfile_gpkg, layer='{}_{}'.format(theme, geo), driver="GPKG")

        print('Done {}:{} in {} seconds to file.'.format(theme, geo, round(time.time() - begin_time, 0)))
