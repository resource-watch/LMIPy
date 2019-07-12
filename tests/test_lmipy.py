import pytest
import random
import os
from LMIPy import Dataset, Collection, Layer, Metadata, Vocabulary, Widget, Image, ImageCollection, Geometry, utils

try:
    API_TOKEN = os.environ.get("API_TOKEN", None)
except:
    raise ValueError(f"Failed to access keys for test.")


### Collection Tests

def test_search_collection():
    """Search all gfw collection for an object"""
    col = Collection(search='forest', app=['gfw'])
    assert len(col) > 1

def test_search_collection_object_type():
    """Search all gfw collection for an object"""
    col = Collection(search='forest', object_type=['layer', 'dataset', 'widget'], app=['gfw'])
    assert len(col) > 1

def test_search_collection_filters():
    """Search all gfw collection for an object"""
    col = Collection(search='forest', object_type=['layer'], filters={'provider': 'gee'}, app=['gfw'])
    assert len(col) > 1

### Dataset Tests

def test_create_dataset():
    ds = Dataset(id_hash='bb1dced4-3ae8-4908-9f36-6514ae69713f')
    assert ds.id == 'bb1dced4-3ae8-4908-9f36-6514ae69713f'
    assert type(ds.attributes) == dict
    assert len(ds.attributes) > 0

def test_queries_on_datasets():
    ds = Dataset(id_hash='bd5d7924-611e-4302-9185-8054acb0b44b')
    df = ds.query('SELECT fid, ST_ASGEOJSON(the_geom_webmercator) FROM data LIMIT 5')
    assert len(df) > 1

def test_access_vocab():
    ds = Dataset(id_hash='bb1dced4-3ae8-4908-9f36-6514ae69713f')
    assert type(ds.vocabulary) == list
    assert len(ds.vocabulary) > 0

def test_access_meta():
    ds = Dataset(id_hash='bb1dced4-3ae8-4908-9f36-6514ae69713f')
    assert type(ds.metadata) == list
    assert len(ds.metadata) > 0

def test_access_meta_attributes():
    ds = Dataset('044f4af8-be72-4999-b7dd-13434fc4a394')
    meta = ds.metadata[0].attributes
    assert type(meta) is dict

def test_access_widget():
    ds = Dataset(id_hash='dcd1e9c7-1370-404e-8816-eaa51d4b1a39')
    assert type(ds.widget) == list
    assert len(ds.widget) > 0

### Clone Dataset
### Update Dataset
def test_update_dataset():
    hash = random.getrandbits(8)
    ds = Dataset(id_hash='bc06c603-9b16-4e51-99e6-228fa576e06b')
    updated = ds.update(token=API_TOKEN, update_params={'name': f'Template Dataset #{hash}'})
    assert updated.attributes['name'] == f'Template Dataset #{hash}'
    updated = ds.update(token=API_TOKEN, update_params={'name': f'Template Dataset'})
    assert updated.attributes['name'] == 'Template Dataset'


### Delete Dataset

#----- Layer Tests -----#

def test_layer_creation():
    ly = Layer(id_hash='dc6f6dd2-0718-4e41-81d2-109866bb9edd')
    assert ly is not None

### Clone and Delete Layer
def test_clone_and_delete_layer():
    hash = random.getrandbits(8)
    l = Layer(id_hash='0328715e-6c6e-4e11-8177-5f0681794f8d')
    cloned = l.clone(token=API_TOKEN, layer_params={'name': f'Template Layer Clone #{hash}'})
    assert cloned.attributes['name'] == f'Template Layer Clone #{hash}'
    assert cloned.id is not '0328715e-6c6e-4e11-8177-5f0681794f8d'
    assert cloned.delete(token=API_TOKEN, force=True) == None

### Create and Delete Layer
def test_create_and_delete_layer():
    hash = random.getrandbits(8)
    ds_id = 'bb1dced4-3ae8-4908-9f36-6514ae69713f'
    l_payload = {
        "name": f'Created Layer #{hash}',
        "description": "",
        "application": [
            "gfw"
        ],
        "iso": [],
        "provider": "gee",
        "default": False,
        "env": "production",
        "layerConfig": {},
        "legendConfig": {},
        "interactionConfig": {},
        "applicationConfig": {}
    }
    new = l.new_layer(token=API_TOKEN, attributes=l_payload)
    assert new.attributes['name'] == f'Created Layer #{hash}'
    assert new.delete(token=API_TOKEN, force=True) == None

### Update Layer
def test_update_layer():
    hash = random.getrandbits(8)
    l = Layer(id_hash='0328715e-6c6e-4e11-8177-5f0681794f8d')
    updated = l.update(token=API_TOKEN, update_params={'name': f'Template Layer #{hash}'})
    assert updated.attributes['name'] == f'Template Layer #{hash}'
    updated = l.update(token=API_TOKEN, update_params={'name': f'Template Layer'})
    assert updated.attributes['name'] == 'Template Layer'

### Widget Tests

def test_create_widget():
    w = Widget(id_hash='8571b2c4-9478-4b63-8444-d308b191df92')
    assert w.id == '8571b2c4-9478-4b63-8444-d308b191df92'
    assert type(w.attributes) == dict
    assert len(w.attributes) > 0

### Add Widget
### Update Layer
### Delete Layer


#----- Vocab Tests -----#

### Delete Vocab
def test_delete_vocab():
    ds = Dataset(id_hash='bc06c603-9b16-4e51-99e6-228fa576e06b')
    v = ds.vocabulary[0]
    assert type(v.id) == str
    deleted_vocab = v.delete(token=API_TOKEN)
    assert deleted_vocab == None

### Add Vocab
def test_add_vocab():
    ds = Dataset(id_hash='bc06c603-9b16-4e51-99e6-228fa576e06b')
    payload = {
        'name': 'categoryTab',
        'tags': ['forestChange', 'treeCoverChange'],
        'application': 'gfw'
    }
    ds.add_vocabulary(vocab_params=payload, token=API_TOKEN)
    updated_ds = Dataset(id_hash='bc06c603-9b16-4e51-99e6-228fa576e06b')
    assert len(updated_ds.vocabulary) > 0

### Update Vocab
def test_update_vocab():
    ds = Dataset(id_hash='bc06c603-9b16-4e51-99e6-228fa576e06b')
    v = ds.vocabulary[0]
    assert type(v.id) == str
    payload = {
        'name': 'categoryTab',
        'tags': ['forestChange', 'treeCoverChange']
    }
    updated_v = v.update(update_params=payload, token=API_TOKEN)
    assert updated_v[0].attributes['name'] == 'categoryTab'
    assert updated_v[0].attributes['tags'] == ['forestChange', 'treeCoverChange']

#----- Meta Tests -----#

### Delete Meta
def test_delete_meta():
    ds = Dataset(id_hash='bc06c603-9b16-4e51-99e6-228fa576e06b')
    m = ds.metadata[0]
    assert type(m.id) == str
    deleted_meta = m.delete(token=API_TOKEN)
    assert deleted_meta == None

### Add Meta
def test_add_meta():
    ds = Dataset(id_hash='bc06c603-9b16-4e51-99e6-228fa576e06b')
    payload = {
    'application': 'gfw',
    'info': {'citation': 'Example citation',
        'color': '#fe6598',
        'description': 'This is an example dataset.',
        'isLossLayer': True,
        'name': 'Template Layer'},
        'language': 'en'
    }
    ds.add_metadata(meta_params=payload, token=API_TOKEN)
    updated_ds = Dataset(id_hash='bc06c603-9b16-4e51-99e6-228fa576e06b')
    assert len(updated_ds.metadata) > 0

### Update Meta
def test_update_meta():
    ds = Dataset(id_hash='bc06c603-9b16-4e51-99e6-228fa576e06b')
    m = ds.metadata[0]
    assert type(m.id) == str
    payload = {
    'application': 'gfw',
    'info': {'citation': 'TEST',
        'color': '#fe6598',
        'description': 'TEST',
        'isLossLayer': False,
        'name': 'Template Layer'},
    'language': 'en'}
    m.update(update_params=payload, token=API_TOKEN)
    ds = Dataset(id_hash='bc06c603-9b16-4e51-99e6-228fa576e06b')
    updated_m = ds.metadata[0]
    assert updated_m.attributes['info']['description'] == 'TEST'
    assert updated_m.attributes['info']['isLossLayer'] == False

#----- Geometry Tests -----#

def test_geometry_create_and_describe():
    atts={'geojson': {'type': 'FeatureCollection',
                        'features': [{'type': 'Feature',
                            'properties': {},
                            'geometry': {'type': 'Polygon',
                            'coordinates': [[[28.00004197633704,49.710191987352424],
                            [28.00004197633704,48.18737001395745],
                            [27.750103011493355,48.18737001395745],
                            [27.50016404664967,48.18737001395745],
                            [27.25022508180598,48.18737001395745],
                            [26.99982835329041,48.18737001395745],
                            [26.99982835329041,49.710191987352424],
                            [27.25022508180598,49.710191987352424],
                            [27.50016404664967,49.710191987352424],
                            [27.750103011493355,49.710191987352424],
                            [28.00004197633704,49.710191987352424]]]}}]}}
    g = Geometry(attributes=atts)
    g.describe()
    assert g.description.get('title') is not None

#----- ImageCollection Tests -----#

def test_image_collection_search():
    ic = ImageCollection(lon=28.271979, lat=-16.457814, start='2018-06-01', end='2018-06-20')
    assert len(ic) > 0

#----- Image Tests -----#

#----- Utils Tests -----#

def test_sld_functions():
    sld_obj = {
        'extended': 'false',
        'items': [
            {'color': '#F8EBFF', 'quantity': -40},
            {'color': '#ECCAFC', 'quantity': -20.667},
            {'color': '#DFA4FF', 'quantity': -14.667},
            {'color': '#C26DFE', 'quantity': -10},
            {'color': '#9D36F7', 'quantity': -3.333},
            {'color': '#6D00E1', 'quantity': -0.667},
            {'color': '#3C00AB', 'quantity': 0}
        ],
        'type': 'ramp'
    }

    test_sld = {
        'extended': 'false',
        'items': [
            {'color': '#F8EBFF', 'quantity': '-40'},
            {'color': '#ECCAFC', 'quantity': '-20.667'},
            {'color': '#DFA4FF', 'quantity': '-14.667'},
            {'color': '#C26DFE', 'quantity': '-10'},
            {'color': '#9D36F7', 'quantity': '-3.333'},
            {'color': '#6D00E1', 'quantity': '-0.667'},
            {'color': '#3C00AB'}
        ],
        'type': 'ramp'
        }

    sld_str = utils.sldDump(sld_obj)
    assert sld_str == '<RasterSymbolizer> <ColorMap type="ramp" extended="false"> <ColorMapEntry color="#F8EBFF" quantity="-40" /> + <ColorMapEntry color="#ECCAFC" quantity="-20.667" /> + <ColorMapEntry color="#DFA4FF" quantity="-14.667" /> + <ColorMapEntry color="#C26DFE" quantity="-10" /> + <ColorMapEntry color="#9D36F7" quantity="-3.333" /> + <ColorMapEntry color="#6D00E1" quantity="-0.667" /> + <ColorMapEntry color="#3C00AB" /> + </ColorMap> </RasterSymbolizer>'
    assert utils.sldParse(sld_str) == test_sld
