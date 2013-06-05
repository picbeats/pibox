import urllib
import ast
from state import *

class RadioBrowser():
    @staticmethod
    def to_radio(s):
        return Radio(s['id'], s['name'], s['url'])

    @staticmethod
    def search(searchterm):
        url = 'http://www.radio-browser.info/webservice/json/stations/' + urllib.quote_plus(searchterm)
        
        print 'Quering: ' + url
    
        stations = ast.literal_eval(urllib.urlopen(url).read())

        data = [];
        
        for s in stations:
            data.append(RadioBrowser.to_radio(s))
    
        return data
        
    @staticmethod
    def byid(id):
        print 'RadioBrowser.get: ' + str(id)
        
        url = 'http://www.radio-browser.info/webservice/json/stations/byid/' + urllib.quote_plus(id)
        
        print 'Quering: ' + url
    
        stations = ast.literal_eval(urllib.urlopen(url).read())
        
        for s in stations:
            return RadioBrowser.to_radio(s)
    
        return None