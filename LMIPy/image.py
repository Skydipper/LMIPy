from .utils import html_box, get_geojson_string
import requests
import json
import folium
import geopandas as gpd
from shapely.geometry.polygon import LinearRing
from shapely.geometry import shape

class Image:
    """
    Main Image Class

    Parameters
    ----------
    bbox: dict
        A dictionary describing the bounding box of the image.

    in: float
        A decimal longitude.

    bands: list
        A list of bands to visulise (e.g. ['b4','b3','b2']).

    instrument: str
        A string indicating the satellite platform ('sentinel', 'landsat', 'all').

    start: str
        Start date ('YYYY-MM-DD') to bound the search for the satellite images.

    end: str
        End date ('YYYY-MM-DD') to bound the search for the satellite images.

    """

    def __init__(self, source=None, instrument=None, date_time=None, cloud_score=None,
                 thumb_url = None, bbox=None, tile_url=None,
                 server='https://production-api.globalforestwatch.org', type=None,
                 band_viz={'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 0.4}):
        self.source = source
        if type == None:
            self.type = 'Image'
        else:
            self.type = type
        self.instrument = instrument
        self.cloud_score = cloud_score
        self.date_time = date_time
        self.server = server
        self.band_viz = band_viz
        self.bbox = bbox
        self.ring = self.get_ring()
        self.tile_url = tile_url
        if thumb_url:
            self.thumb_url = thumb_url
        else:
            self.thumb_url = self.get_thumbs()
        self.attributes = self.get_attributes()

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"Image {self.source}"

    def _repr_html_(self):
        return html_box(item=self)

    def get_thumbs(self):
        payload = {'source_data': [{'source': self.source}], 'bands': self.band_viz.get('bands')}
        url = self.server + '/recent-tiles/thumbs'
        r = requests.post(url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        if  r.status_code == 200:
            return r.json().get('data').get('attributes')[0].get('thumbnail_url')
        else:
            print(f'Failed to get tile {r.status_code}, {r.json()}')
            return None

    def get_image_url(self):
        payload = {'source_data': [{'source': self.source}], 'bands': self.band_viz.get('bands')}
        url = self.server + '/recent-tiles/tiles'
        r = requests.post(url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        if  r.status_code == 200:
            return r.json().get('data').get('attributes')[0].get('tile_url')
        else:
            print(f'Failed to get tile {r.status_code}, {r.json()}')
            return None

    def get_ring(self):
        print(f"bbox fed to ring: {self.bbox.get('geometry').get('coordinates')}")
        ring = LinearRing(self.bbox.get('geometry').get('coordinates'))
        return ring

    def get_attributes(self):
        return {'provider': self.source}

    def map(self, color='#64D1B8', weight=6):
        """
        Returns a folim map of selected image with styles applied.

        Parameters
        ----------
        weight: int
            Weight of geom outline. Default = 6.
        color: str
            Hex code for geom outline. Default = #64D1B8.
        """
        centroid = [self.ring.centroid.xy[1][0], self.ring.centroid.xy[0][0]]
        result_map = folium.Map(location=centroid, tiles='OpenStreetMap')
        if not self.tile_url:
            self.tile_url = self.get_image_url()
        result_map.add_tile_layer(tiles=self.tile_url, attr=f"{self.instrument} image")
        geojson_str = get_geojson_string(self.bbox['geometry'])
        folium.GeoJson(
                    data=geojson_str,
                    style_function=lambda x: {
                    'fillOpacity': 0,
                    'weight': weight,
                    'color': color
                    }
                ).add_to(result_map)
        w,s,e,n = list(self.ring.bounds)
        result_map.fit_bounds([[s, w], [n, e]])
        return result_map

    def classify(self, type='random_forest'):
        """
            Returns a classified Image object.

        Parameters
        ----------
        type: string
            A string ('random_forest' or '') determining which type of classification will be done.
        """
        if type == 'random_forest':
            url = self.server + '/recent-tiles-classifier'
            params = {'img_id': self.attributes.get('provider')}

            r = requests.get(url, params=params)
            if r.status_code == 200:
                classified_tiles = r.json().get('data').get('attributes').get('url')
                tmp = {'instrument': self.instrument,
                        'date_time': self.date_time,
                        'cloud_score': self.cloud_score,
                        'source': self.source,
                        'band_viz': None,
                        'server': self.server,
                        'thumb_url': self.thumb_url,
                        'tile_url': classified_tiles,
                        'type': 'Classified Image',
                        'bbox': self.bbox
                        }
                return Image(**tmp)
            else:
                raise ValueError(f'Classification failed ({r.status_code} response): {r.json()}')
            return None
