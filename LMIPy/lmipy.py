import requests
import random
import geopandas as gpd
from shapely.geometry import shape
import cartoframes as cf
from IPython.display import display, HTML

APIKEY = ''

def html_box(item):
    """Returns an HTML block with template strings filled-in based on item attributes."""
    is_layer = type(item) == Layer
    is_dataset = type(item) == Dataset or type(item) == Table
    if is_layer:
        kind_of_item = 'Layer'
        url_link = f'{item.server}/v1/layer/{item.id}?includes=vocabulary,metadata'
    elif is_dataset:
        kind_of_item = 'Dataset'
        url_link = f'{item.server}/v1/dataset/{item.id}?includes=vocabulary,metadata,layer'
    else:
        kind_of_item = 'Unknown'
    table_statement = f"Data source {item.attributes.get('provider')}"
    if item.attributes.get('connectorUrl') and item.attributes.get('provider') == "cartodb":
        table_statement = (f"Carto table: <a href={item.attributes.get('connectorUrl')}"
                           " target='_blank'>"
                           f"{item.attributes.get('tableName')}"
                           "</a>"
                          )
    if item.attributes.get('connectorUrl') and item.attributes.get('provider') == "csv":
        table_statement = (f"CSV Table: <a href={item.attributes.get('connectorUrl')}"
                           " target='_blank'>"
                           f"{item.attributes.get('tableName')}"
                           "</a>"
                          )
    if item.attributes.get('provider') == 'gee':
        table_statement = (f"GEE asset: <a href='https://code.earthengine.google.com/asset='"
                           f"{item.attributes.get('tableName')} target='_blank'>"
                           f"{item.attributes.get('tableName')}"
                           "</a>"
                          )

    html = ("<div class='item_container' style='height: auto; overflow: hidden; border: 1px solid #80ceb9;"
            "border-radius: 2px; background: #f2fffb; line-height: 1.21429em; padding: 10px;''>"
            "<div class='item_left' style='width: 210px; float: left;''>"
            "<a href='https://resourcewatch.org/' target='_blank'>"
            "<img class='itemThumbnail' src='https://resourcewatch.org/static/images/logo-embed.png'>"
            "</a></div><div class='item_right' style='float: none; width: auto; overflow: hidden;''>"
            f"<a href={url_link} target='_blank'>"
            f"<b>{item.attributes.get('name')}</b>"
            "</a>"
            f"<br> {table_statement} 🗺{kind_of_item} in {', '.join(item.attributes.get('application')).upper()}."
            f"<br>Last Modified: {item.attributes.get('updatedAt')}"
            f"<br>Connector: {None}"
            f" | Published: {item.attributes.get('published')}"
            " </div> </div>")
    return html


class Collection:
    """
    Returns a list of objects from a server

    This function searches all avaiable layers or dataset entries within user specified limits and returns a list.
    of objects.

    Parameters
    ----------
    app: list
        A list of string IDs of applications to search, e.g. [‘gfw’, ‘rw’]
    limit: int
        Maximum number of items to return
    order: str
        Field to order items by, e.g. ’date’
    sort: str
        Rule to sort items by, either ascending (’asc’) or descending ('desc')
    search: str
        String to search records by, e.g. ’Forest loss’
    object_type: list
        A list of strings of object types to search, e.g. [‘dataset’, ‘layer’]
    """
    def __init__(self, search, app=['gfw','rw'], env='production', limit=1000, order='name', sort='desc',
                 object_type=['dataset', 'layer'], server='https://api.resourcewatch.org'):
        self.server = server
        self.search = search.strip().split(' ')
        self.app = ",".join(app)
        self.env = env
        self.limit = limit
        self.order = order
        self.sort = sort
        self.object_type = object_type
        self.collection = self.get_collection()
        self.iter_position = 0

    def __repr__(self):
        return [str(c) for c in self.collection]

    def __iter__(self):
        return self

    def __next__(self): # Python 3: def __next__(self)
        if self.iter_position >= len(self.collection):
            self.iter_position = 0
            raise StopIteration
        else:
            self.iter_position += 1
            return self.collection[self.iter_position - 1]

    def __getitem__(self, key):
        return self.collection[key]

    def get_collection(self):
        """
        Getter for the a collection object.
        """
        if 'layer' in self.object_type:
            response_list = self.get_layers()
        else:
            response_list = self.get_datasets()
        ordered_list = self.order_results(response_list)
        return ordered_list

    def get_datasets(self):
        """Return all datasets and connected items within a limit and specified environment"""
        hash = random.getrandbits(16)
        url = (f'{self.server}/v1/dataset?app={self.app}&env={self.env}&'
               f'includes=layer,vocabulary,metadata&page[size]=1000&hash={hash}')
        r = requests.get(url)
        response_list = r.json().get('data', None)
        if len(response_list) < 1:
            raise ValueError('No items found')
        identified_layers = self.filter_results(response_list)
        return identified_layers

    def get_layers(self):
        """Return all layers from specified apps and environment within a limit number"""
        hash = random.getrandbits(16)
        url = (f"{self.server}/v1/layer?app={self.app}&env={self.env}"
               f"&includes=vocabulary,metadata&page[size]=1000&hash={hash}")
        r = requests.get(url)
        response_list = r.json().get('data', None)
        if len(response_list) < 1:
            raise ValueError('No items found')
        identified_layers = self.filter_results(response_list)
        return identified_layers

    def filter_results(self, response_list):
        """Search by a list of strings to return a filtered list of Dataset or Layer objects"""
        filtered_response = []
        collection = []
        for item in response_list:
            in_description = False
            in_name = False
            name = item.get('attributes').get('name').lower()
            description = item.get('attributes').get('description')
            if description:
                in_description = any([s in description for s in self.search])
            if name:
                in_name = any([s in name for s in self.search])
            if in_name or in_description:
                if len(filtered_response) < self.limit:
                    filtered_response.append(item)
                if item.get('type') == 'dataset' and item.get('attributes').get('provider') in ['csv', 'json']:
                    collection.append(Table(id_hash = item.get('id'), attributes=item.get('attributes')))
                elif item.get('type') == 'dataset' and item.get('attributes').get('provider') != 'csv':
                    collection.append(Dataset(id_hash = item.get('id'), attributes=item.get('attributes')))
                if item.get('type') == 'layer':
                    collection.append(Layer(id_hash = item.get('id'), attributes=item.get('attributes')))
        return collection

    def order_results(self, collection_list):
        """Operate on a list of objects given the order key, limit, and rule a user has passed"""
        tmp_sorted = []
        try:
            d = {}
            for n, z in enumerate([c.attributes.get(self.order.lower()) for c in collection_list]):
                d[z] = collection_list[n]
            keys = sorted(d, reverse=self.sort.lower() == 'asc')
            for key in keys:
                tmp_sorted.append(d[key])
        except:
            raise ValueError(f'[Order-error] Param does not exist in collection: {self.order}, rule: {self.sort}')
        if self.limit < len(tmp_sorted):
            tmp_sorted = tmp_sorted[0:self.limit]
        return tmp_sorted


class Dataset:
    """
    This is the main Dataset class.

    Parameters
    ----------
    id_hash: int
        An ID hash of the dataset in the API.
    attributes: dic
        A dictionary holding the attributes of a dataset.
    sever: str
        A URL string of the vizzuality server.
    """
    def __init__(self, id_hash=None, attributes=None, server='https://api.resourcewatch.org'):
        self.id = id_hash
        self.layers = []
        self.server = server
        if not attributes:
            self.attributes = self.get_dataset()
        else:
            self.attributes = attributes
        if len(self.attributes.get('layer')) > 0:
            self.layers = [Layer(attributes=l) for l in self.attributes.get('layer')]
            _ = self.attributes.pop('layer')
        if len(self.attributes.get('metadata')) > 0:
            self.metadata = Metadata(self.attributes.get('metadata')[0])
            _ = self.attributes.pop('metadata')
        else:
            self.metadata = False
        if len(self.attributes.get('vocabulary')) > 0:
            self.vocabulary = Vocabulary(self.attributes.get('vocabulary')[0])
            _ = self.attributes.pop('vocabulary')
        else:
            self.vocabulary = False
        self.url = f"{server}/v1/dataset/{id_hash}?hash={random.getrandbits(16)}"

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"Dataset {self.id}"

    def _repr_html_(self):
        return html_box(item=self)

    def get_dataset(self):
        """
        Retrieve a dataset from a server by ID.
        """
        hash = random.getrandbits(16)
        url = (f'{self.server}/v1/dataset/{self.id}?includes=layer,vocabulary,metadata&hash={hash}')
        r = requests.get(url)
        if r.status_code == 200:
            return r.json().get('data').get('attributes')
        else:
            raise ValueError(f'Unable to get dataset {self.id} from {r.url}')

    def __carto_query__(self, sql, decode_geom=False):
        """
        Returns a GeoPandas GeoDataFrame for CARTO datasets.
        """

        if 'the_geom' not in sql and decode_geom == True:
            sql = sql.replace('SELECT', 'SELECT the_geom,')

        if 'count' in sql:
            decode_geom = False:

        table_name = self.attributes.get('tableName', 'data')
        sql = sql.replace('FROM data', f'FROM {table_name}').replace('"', "'") 

        connector = self.attributes.get('connectorUrl', '')

        if connector:
            account = connector.split('.carto.com/')[0]
            urlCartoContext = "{0}.carto.com".format(account)
                
            cc = cf.CartoContext(base_url=urlCartoContext, api_key=APIKEY)

        table = self.attributes.get('tableName', None)
        if table:
            return cc.query(sql, decode_geom=decode_geom)

    def query(self, sql="SELECT * FROM data LIMIT 5", decode_geom=False):
        """
        Returns a carto table as a GeoPandas GeoDataframe from a Vizzuality API using the query endpoint.
        """
        provider = self.attributes.get('provider', None)
        if provider != 'cartodb':
            raise ValueError(f'Unable to perform query on datasets with provider {provider}. Must be `cartodb`.')

        return self.__carto_query__(sql=sql, decode_geom=decode_geom)
        
    def head(self, n=5, decode_geom=True):
        """
        Returns a table as a GeoPandas GeoDataframe from a Vizzuality API using the query endpoint.
        """
        sql = f'SELECT * FROM data LIMIT {n}'
        return self.__carto_query__(sql=sql, decode_geom=decode_geom)

class Table(Dataset):
    """
    This is the main Table class.

    Parameters
    ----------
    id_hash: int
        An ID hash.
    attributes: dic
        A dictionary holding the attributes of a tabular dataset.
    server: str
        A string of the server URL.
    """
    def __init__(self, id_hash=None, attributes=None, server='https://api.resourcewatch.org'):
        super().__init__(id_hash=id_hash, attributes=attributes, server=server)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"Table {self.id}"

    def __fetch_query__(self, sql, decode_geom=False):
        """
        Forms a base query and returns data
        """

        table_name = self.attributes.get('tableName', 'data')
        sql = sql.replace('FROM data', f'FROM {table_name}') 

        try:
            url = (f'{self.server}/v1/query/{self.id}?sql={sql}')
            r = requests.get(url)
            if r.status_code == 200:
                response_data = r.json().get('data')
                if decode_geom:
                    for d in response_data:
                        if d.get('the_geom', None):
                            d['geometry'] = shape(d['the_geom'])
                return response_data
            else:
                raise ValueError(f'Unable to get table {self.id} from {r.url}')
        except:
            raise ValueError(f'Unable to get table {self.id} from {r.url}')
            


    def head(self, n=5, decode_geom=True):
        """
        Returns a table as a GeoPandas GeoDataframe from a Vizzuality API using the query endpoint.
        """
        sql = f'SELECT * FROM data LIMIT {n}'
        response_data = self.__fetch_query__(sql=sql, decode_geom=decode_geom)

        try:
            gdf = gpd.GeoDataFrame(response_data)
            if 'geometry' in gdf:
                gdf = gdf.set_geometry('geometry')
            return gdf
        except:
            raise ValueError(f'Unable to get table {self.id}')

    def query(self, sql='SELECT * FROM data LIMIT 5', decode_geom=False):
        """Return a query as a dataframe object"""
        response_data = self.__fetch_query__(sql=sql, decode_geom=decode_geom)
        try:
            gdf = gpd.GeoDataFrame(response_data)
            if 'geometry' in gdf:
                gdf = gdf.set_geometry('geometry')
            return gdf
        except:
            raise ValueError(f'Unable to query table {self.id} with {sql}')


class Layer:
    """
    This is the main Layer class.

    Parameters
    ----------
    id_hash: int
        An ID hash.
    attributes: dic
        A dictionary holding the attributes of a dataset.
    server: str
        A string of the server URL.
    """
    def __init__(self, id_hash=None, attributes=None, server='https://api.resourcewatch.org'):
        self.server = server
        if not id_hash:
            if attributes:
                self.id = attributes.get('id', None)
                self.attributes = attributes.get('attributes', None)
            else:
                self.id = None
                self.attributes = None
        else:
            self.id = id_hash
            self.attributes = self.get_layer()

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"Layer {self.id}"

    def _repr_html_(self):
        return html_box(item=self)

    def get_layer(self):
        """
        Returns a layer from a Vizzuality API.
        """
        hash = random.getrandbits(16)
        url = (f'{self.server}/v1/layer/{self.id}?includes=vocabulary,metadata&hash={hash}')
        r = requests.get(url)
        if r.status_code == 200:
            return r.json().get('data').get('attributes')
        else:
            raise ValueError(f'Unable to get dataset {self.id} from {r.url}')


class Metadata:
    """
    This is the main Metadata class.

    Parameters
    ----------
    attributes: dic
        A dictionary holding the attributes of a metadata (which are attached to a Dataset).
    """
    def __init__(self, attributes=None):
        if attributes.get('type') != 'metadata':
            raise ValueError(f"Non metadata attributes passed to Metadata class ({attributes.get('type')})")
        self.id = attributes.get('id')
        self.attributes = attributes.get('attributes')

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"Metadata {self.id}"


class Vocabulary:
    """
    This is the main Vocabulary class.

    Parameters
    ----------
    attributes: dic
        A dictionary holding the attributes of a vocabulary (which are attached to a Dataset).
    """
    def __init__(self, attributes=None,):
        if attributes.get('type') != 'vocabulary':
            raise ValueError(f"Non vocabulary attributes passed to Vocabulary class ({attributes.get('type')})")
        self.attributes = attributes.get('attributes')
        self.id = self.attributes.get('resource').get('id')

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"Vocabulary {self.id}"
