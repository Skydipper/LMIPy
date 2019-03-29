import requests
import random
from IPython.display import display, HTML


class LMI:
    """
    Main class to connect to multiple objects in the Vizzuality API.
    """
    def __init__(self, token=None, server='https://api.resourcewatch.org'):
        self.token = token
        self.server = server

    def __repr__(self):
        return f"LMI class object"        

    def set_token(self, token):
        """Set the API token"""
        try:
            token = str(token)
            self.token = token
        except:
            raise ValueError('API token invalid')

    def set_server(self, server):
        """Set the target server"""
        try:
            server = str(server)
            self.server = server
        except:
            raise ValueError('Server not valid')

    def collection(self, search, app=['gfw','rw'], env='production', limit=1000, order='date', sort='asc', object_type=['dataset', 'layer']):
        """
            Retunrn a list of objects from a server
            
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
        search = search.strip().split(' ')
        if app:
            app_string = ",".join(app)
        else:
            raise ValueError('Please specify an app to search.')   
        if 'layer' in object_type:
            response_list = self.get_layers(search=search, env=env, app_string=app_string, limit=limit)
        else:
            response_list = self.get_datasets(search=search, env=env, app_string=app_string, limit=limit)  
        response_list = order_results(response_list)
        return response_list
    
    def get_datasets(self, search, env, app_string, limit):
        """Return all datasets and connected items within a limit and specified environment"""
        hash = random.getrandbits(16)
        url = (f'{self.server}/v1/dataset?app={app_string}&env={env}&'
               f'includes=layer,vocabulary,metadata&page[size]=1000&hash={hash}')
        r = requests.get(url)
        #print(r.url)
        response_list = r.json().get('data', None)
        if len(response_list) < 1:
            raise ValueError('No items found')
        identified_layers = self.filter_results(response_list, search, limit)
        return identified_layers
    
    def get_layers(self, search, env, app_string, limit):
        """Return all layers from specified apps and environment within a limit number"""
        hash = random.getrandbits(16)
        url = (f"{self.server}/v1/layer?app={app_string}&env={env}"
               f"&includes=vocabulary,metadata&page[size]=1000&hash={hash}")
        r = requests.get(url)
        #print(r.url)
        response_list = r.json().get('data', None)
        if len(response_list) < 1:
            raise ValueError('No items found')
        identified_layers = self.filter_results(response_list, search, limit)
        return identified_layers
    
    
    def filter_results(self, response_list, search, limit):
        """Search by a list of strings to return a filtered list of Dataset or Layer objects"""
        filtered_response = []
        collection = []
        #print(f'searching for {search}')
        for item in response_list:
            in_description = False
            in_name = False
            id_hash = item.get('id')
            name = item.get('attributes').get('name').lower()
            description = item.get('attributes').get('description')
            if description:
                in_description = any([s in description for s in search])
            if name:
                in_name = any([s in name for s in search])
            if in_name or in_description:
                if len(filtered_response) < limit:
                    filtered_response.append(item)
                if item.get('type') == 'dataset':
                    collection.append(Dataset(id_hash = item.get('id'), attributes=item.get('attributes')))
                if item.get('type') == 'layer':
                    collection.append(Layer())
        return collection
    
    
    def order_results(self, response_list, limit,):
        """Operate on a list of objects given the rules a user has passed"""
        pass
        return response_list
    
    
class Dataset:
    """ 
    This is the main Dataset class. 
      
    Attributes: 
        id_hash (int): An ID hash. 
        attributes (dic): A dictionary holding the attributes of a dataset. 
    """
    def __init__(self,id_hash=None, attributes=None, server='https://api.resourcewatch.org'):
        self.id = id_hash
        self.server = server
        if not attributes:
            self.attributes = self.get_dataset()
        else:
            self.attributes = attributes
        self.url = f"{server}/v1/dataset/{id_hash}?hash={random.getrandbits(16)}"
    
    def __repr__(self):
        return self.__str__()
    
    def __str__(self):
        return f"Dataset {self.id}"
    
    def _repr_html_(self):
        """For notebook"""
        if self.attributes.get('connectorUrl'):
            table_statement = (f"Origin source: <a href={self.attributes.get('connectorUrl')}"
                               " target='_blank'>"
                               f"{self.attributes.get('tableName')}"
                               "</a>"
                              )
        else:
            table_statement = "Data source X"
        
        html = ("<div class='item_container' style='height: auto; overflow: hidden; border: 1px solid #80ceb9;"
                "border-radius: 2px; background: #f2fffb; line-height: 1.21429em; padding: 10px;''>"
                "<div class='item_left' style='width: 210px; float: left;''>"
                "<a href='https://resourcewatch.org/' target='_blank'>"
                "<img class='itemThumbnail' src='https://resourcewatch.org/static/images/logo-embed.png'>"
                "</a></div><div class='item_right' style='float: none; width: auto; overflow: hidden;''>"
                f"<a href={self.url} target='_blank'>"
                f"<b>{self.attributes.get('name')}</b>"
                "</a>"
                f"<br> {table_statement} 🗺Dataset in {', '.join(self.attributes.get('application')).upper()}."
                f"<br>Last Modified: {self.attributes.get('updatedAt')}"
                f"<br>Connector: {self.attributes.get('connectorType').title()}"
                f" | Published: {self.attributes.get('published')}"
                " </div> </div>")
        
        return html
        
    
    def get_dataset(self):
        """
        Retrieve a dataset from a server by ID.
        """
        hash = random.getrandbits(16)
        url = (f'{self.server}/v1/dataset/{self.id}?hash={hash}')
        r = requests.get(url)
        if r.status_code == 200:
            return r.json().get('data').get('attributes')
        else:
            raise ValueError(f'Unable to get dataset {self.id} from {r.url}')


class Layer:
    def __init__(self):
        self.id = None
        self.dataset = None
        
    def __repr__(self):
        return f"Layer {self.id}"
        