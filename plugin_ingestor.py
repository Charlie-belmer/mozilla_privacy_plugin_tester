# Ingests the plugin.json file into the database
import json
from db import store_plugin

def ingest_plugins(file='crawler/plugins.json'):
    with open(file, 'r') as plugins: 
        plugins = json.load(plugins) 
        
        for plugin in plugins: 
            plugin["users"] = plugin["users"][:plugin["users"].find("user") - 1].replace(",","")
            store_plugin(plugin)