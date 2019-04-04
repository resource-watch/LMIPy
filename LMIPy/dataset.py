import requests
import json
import random
from pprint import pprint
from .layer  import Layer
from .utils import html_box
from .lmipy import Vocabulary, Metadata


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
        try:
            hash = random.getrandbits(16)
            url = (f'{self.server}/v1/dataset/{self.id}?includes=layer,vocabulary,metadata&hash={hash}')
            r = requests.get(url)
        except:
            raise ValueError(f'Unable to get Dataset {self.id} from {r.url}')

        if r.status_code == 200:
            return r.json().get('data').get('attributes')
        else:
            raise ValueError(f'Dataset with id={self.id} does not exist.')


    def __carto_query__(self, sql, decode_geom=False, APIKEY=None):
        """
        Returns a GeoPandas GeoDataFrame for CARTO datasets.
        """

        if 'the_geom' not in sql and decode_geom == True:
            sql = sql.replace('SELECT', 'SELECT the_geom,')

        if 'count' in sql:
            decode_geom = False

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

    def query(self, sql="SELECT * FROM data LIMIT 5", decode_geom=False, APIKEY=None):
        """
        Returns a carto table as a GeoPandas GeoDataframe from a Vizzuality API using the query endpoint.
        """
        provider = self.attributes.get('provider', None)
        if provider != 'cartodb':
            raise ValueError(f'Unable to perform query on datasets with provider {provider}. Must be `cartodb`.')

        return self.__carto_query__(sql=sql, decode_geom=decode_geom)

    def head(self, n=5, decode_geom=True, APIKEY=None):
        """
        Returns a table as a GeoPandas GeoDataframe from a Vizzuality API using the query endpoint.
        """
        sql = f'SELECT * FROM data LIMIT {n}'
        return self.__carto_query__(sql=sql, decode_geom=decode_geom)

    def update_keys(self):
        """
        Returns specific attribute values.
        """
        # Cannot update the following
        update_blacklist = ['metadata','layer', 'vocabulary', 'updatedAt', 'userId', 'slug', "clonedHost", "errorMessage", "taskId", "dataLastUpdated"]
        updatable_fields = {f'{k}':v for k,v in self.attributes.items() if k not in update_blacklist}

        print(f'Updatable keys: \n{list(updatable_fields.keys())}')
        return updatable_fields

    def update(self, update_json=None, API_TOKEN=None, show_difference=False):
        """
        Update layer specific attribute values.
        Returns updated Dataset.
        """
        if not API_TOKEN:
            raise ValueError(f'[API_TOKEN=None] Resource Watch API TOKEN required for updates.')

        if not update_json:
            print('Requires update JSON.')
            return self.update_keys()

        attributes = self.update_keys()

        payload = { f'{key}': update_json[key] for key in update_json if key in attributes }

        ### Update here
        try:
            url = f"http://api.resourcewatch.org/dataset/{self.id}"
            headers = {'Authorization': f'Bearer {API_TOKEN}', 'Content-Type': 'application/json'}
            r = requests.patch(url, data=json.dumps(payload), headers=headers)
        except:
            raise ValueError(f'Dataset update failed.')

        if r.status_code == 200:
            response = r.json()['data']
        else:
            print(r.status_code)
            return None

        if show_difference:
            old_attributes = { f'{k}': attributes[k] for k,v in payload.items() }
            print(f"Attributes to change:")
            pprint(old_attributes)

        print('Updated!')
        pprint({ f'{k}': v for k, v in response['attributes'].items() if k in payload })
        self.attributes = self.get_dataset()
        return self

    def confirm_delete(self):
        print(f"Delete Dataset {self.attributes['name']} with id={self.id}?")
        print("Note: Dataset deletion cascades to all associated Layers, Metadata and Vocabularies.\n> y/n")
        conf = input()
        
        if conf.lower() == 'y':
            return True
        elif conf.lower() == 'n':
            return False
        else:
            print('Requires y/n input!')
            return False

    def delete(self, API_TOKEN=None, force=False):
        """
        Deletes a target layer
        """
        if not API_TOKEN:
            raise ValueError(f'[API_TOKEN=None] Resource Watch API TOKEN required to delete.')

        ### Check if dataset has layers first. Cannot delete
        layer_count = len(self.layers)
        if layer_count > 0:
            print(f'WARNING - Dataset has {layer_count} associated Layer(s).')
            print('[D]elete ALL associated Layers, or\n[A]bort delete process?')
            conf = input()
        
            if conf.lower() == 'd':
                for l in self.layers:
                    l.delete(API_TOKEN, force=True)
            elif conf.lower() == 'a':
                return False
            else:
                print('Requires D/A input!')
                return False

        if not force:
            conf = self.confirm_delete()
        elif force:
            conf = True

        if conf:
            try:        
                url = f'http://api.resourcewatch.org/dataset/{self.id}'
                headers = {'Authorization': f'Bearer {API_TOKEN}', 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}
                r = requests.delete(url, headers=headers)
            except:
                raise ValueError(f'Layer deletion failed.')

            if r.status_code == 200:
                print(r.url)
                pprint('Deletion successful!')
                self = None
        
        else:
            print('Deletion aborted.')
        
        return self
