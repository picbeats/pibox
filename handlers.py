import tornado.web
import tornado.ioloop
import tornado.template
import datetime
import logging
from common import *
from state import *
from mplayer import *

class Index(tornado.web.RequestHandler):
    def get(self):
        path = os.path.dirname(os.path.realpath(__file__))
        loader = tornado.template.Loader(path + "/templates")
        self.write(loader.load("index.html").generate())       
        
class GetMultiState(tornado.web.RequestHandler):
    def initialize(self, states):
        self.states = states
        self.results = {}
        self.callbacks = {}
        self.ready = False
        self.lock = threading.RLock()
        self.waiter = []

    @tornado.web.asynchronous
    def post(self):
        for key in self.states.keys():
            self.lock.acquire()
            callback = lambda data, key_closure=key: self.on_state_update(key_closure, data)
            revision = long(self.get_argument(key))
            try:           
                self.results[key] = { 'revision' : revision }
                self.callbacks[key] = callback
            finally:
                self.lock.release()
            self.states[key].wait_for_update(revision, callback)
        
        self.lock.acquire()
        try:
            if len(self.callbacks) < len(self.results):
                self.cancel_callbacks()
                self.return_results()
            else:
                tornado.ioloop.IOLoop.instance().add_timeout(datetime.timedelta(0, 120), self.on_timeout)
                self.ready = True
        finally:
            self.lock.release()
                      
    def on_state_update(self, key, data):
        # Closed client connection
        if self.request.connection.stream.closed():
            return
            
        self.lock.acquire()
        try:
            self.results[key] = data
            del self.callbacks[key]
            if not self.ready:
                return
            # print 'on_state_update ' + str(data)
            self.cancel_callbacks()
            self.return_results();
        finally:
            self.lock.release()

    def on_timeout(self):
        self.lock.acquire()
        try:
            if self.cancel_callbacks():
                self.return_results()
        finally:
            self.lock.release()            

    def on_connection_close(self):
        self.lock.acquire()
        try:
            self.return_results()
        finally:
            self.lock.release()
            
    def cancel_callbacks(self):
        canceled = 0
        for key in self.callbacks.keys():
            if self.states[key].cancel_wait(self.callbacks[key]):
                canceled += 1
            
        self.callbacks.clear()
        return canceled > 0
            
    def return_results(self):        
        if self.request.connection.stream.closed():
            return
                        
        response = Response()
        response.data = self.results
        self.finish(ResponseJSONEncoder().encode(response))
                           
class PlayRadio(tornado.web.RequestHandler):
    def post(self):
        id = self.get_argument("id");
        response = Response()
        print 'Play radio ' + str(id)
        try:
            radio = state.favorites.get_favorite(id)
                
            if radio == None:
                response.err_num = ERR_NUM_RADIO_STATION_ID_DOES_NOT_EXIST
                response.err_msg = ERR_MSG_RADIO_STATION_ID_DOES_NOT_EXIST
            else:           
                print 'Play ' + radio.display_name
                Mplayer.start(radio)
                
        except Exception, err:
            err_msg = str(err)
            errNum = ERR_NUM_PLAY_RADIO_STATION_FAILED
            
        self.write(ResponseJSONEncoder().encode(response))

class StopRadio(tornado.web.RequestHandler):
    def post(self):
        response = Response()
        print 'Stop radio '
        try:
            Mplayer.stop()
        except Exception, err:
            err_msg = str(err)
            errNum = ERR_NUM_PLAY_RADIO_STATION_FAILED
            
        self.write(ResponseJSONEncoder().encode(response))

class SetVolume(tornado.web.RequestHandler):
    def post(self):
        revision = self.get_argument("revision");
        volume = self.get_argument("volume");
        response = Response()
        print 'Set volume ' + str(volume)
        try:
            state.mixer_state.set_volume(revision, volume)
        except Exception, err:
            print err
            err_msg = str(err)
            errNum = ERR_NUM_SET_VOLUME_FAILED
            
        self.write(ResponseJSONEncoder().encode(response))
              
if __name__ == "__main__":
    pass