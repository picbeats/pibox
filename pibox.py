#!/usr/bin/python

import tornado.ioloop
import tornado.web
import logging
import daemon
import os
from tornado.options import define, options
from handlers import *
from mplayer import *

def clean_up(signal, frame):
    print "quiting ..."
    # Stop accepting new requests from users
    Mplayer.stop()
    #os.kill(self.http.pid, signal.SIGINT)
    tornado.ioloop.IOLoop.instance().stop()

if __name__ == "__main__":
    # get root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # create console handler and set level to debug
    #ch = logging.StreamHandler()
    #ch.setLevel(logging.DEBUG)

    # create formatter
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add formatter to ch
    # ch.setFormatter(formatter)

    # add ch to logger
    #logger.addHandler(ch)
    path = os.path.dirname(os.path.realpath(__file__))
    define("port", default=1080, help="Port")
    define("fg", default=0, help="run in foreground")
    tornado.options.parse_config_file(path + "/pibox.conf")
    tornado.options.parse_command_line()

    application = tornado.web.Application([
        (r"/", Index),
        (r"/(favicon\.ico)", tornado.web.StaticFileHandler, {"path": path + "/static"}),    
        (r"/(apple-touch-icon\.png)", tornado.web.StaticFileHandler, {"path": path + "/static"}),    
        (r"/static/(.*)",tornado.web.StaticFileHandler, {"path": path + "/static"},),	
        (r"/js/(.*)",tornado.web.StaticFileHandler, {"path": path + "/js"},),
        (r"/css/(.*)",tornado.web.StaticFileHandler, {"path": path + "/css"},),	
        (r"/update", GetMultiState, dict(states = dict(favorites = state.favorites, player_state = state.player_state, mixer_state = state.mixer_state))),
        (r"/setvolume", SetVolume),
        (r"/playradio", PlayRadio),
        (r"/stopradio", StopRadio),
        (r"/search/(.*)", Search),
        (r"/playsearch", PlaySearch),
        (r"/addfavorite", AddFavorite),
    ])
    
    if options.fg == 1:
        try:
            application.listen(options.port)
        except:
            try: 
                application.listen(options.port, '0.0.0.0')
            except:
                 print "Unexpected error:", sys.exc_info()[0]
            
        tornado.ioloop.IOLoop.instance().start()    
    else:
        log = open(path + '/logs/pibox.log', 'a+')
        
        context = daemon.DaemonContext(stdout=log, stderr=log)
        context.signal_map = {
                signal.SIGTERM: clean_up,
            }
        
        print "Starting server on port {0} in {1}", options.port, path
        
        
        with context:    
            
            try:
                application.listen(options.port)
            except:
                try: 
                    application.listen(options.port, '0.0.0.0')
                except:
                     print "Unexpected error:", sys.exc_info()[0]
                
            tornado.ioloop.IOLoop.instance().start()