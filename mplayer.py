import subprocess
import thread
import time
import signal 
import os
import re
from state import *


class MplayerProcess():
    def __init__(self, radio, title_callback):
        self.radio = radio
        self.pipe = None
        self.title_callback = title_callback
        self.read_thread = None
        
    def start(self):
        arguments = ['mplayer', '-quiet', '-slave']
        uri = self.radio.stream_url
        uril = uri.lower()
        if (uril.endswith('.m3u') or uril.endswith('.pls')):
            arguments.append( '-playlist')
        arguments.append(uri)
        print 'Starting ' + ' '.join(arguments)
        self.pipe = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE )   
        thread.start_new_thread(self.reader, ())
        
    def stop(self): 
        try:
            if(self.pipe != None):
                self.pipe.stdin.write('Q\n')
                if self.pipe.poll() == None:
                    time.sleep(1)
                    self.pipe.terminate()
                self.pipe = None
        except:
            logging.error("Error in stop", exc_info=True)
            
    def reader(self):
        try:
            while (True):
                line = self.pipe.stdout.readline()
                if line:
                    if line.startswith('ICY Info:'):
                        info = line.split(':', 1)[1].strip()
                        attrs = dict(re.findall("(\w+)='([^']*)'", info))
                        title = attrs.get('StreamTitle', '(none)')
                        print 'Stream title: ' + title                        
                        try:
                            v = title.decode('utf-8')
                        except UnicodeDecodeError:
                            title = title.decode('latin-1').encode('utf-8')                       
                        self.title_callback(title)
                else:
                    break       
        except:
            logging.error("Error in stop", exc_info=True)
   
    
class Mplayer():
    #the current running mplayer process - none if no mplayer process is running
    currentProcess = None
    lock = threading.RLock()
   
    #starts mplayer with a given media URI
    #stops the running mplayer process
    @staticmethod
    def start(radio):
        Mplayer.lock.acquire()
        try:
            Mplayer.stop()
            Mplayer.currentProcess = MplayerProcess(radio, state.player_state.add_title);
            state.player_state.set_radio(radio)
            Mplayer.currentProcess.start()
        finally:
            Mplayer.lock.release()
            
    
    #stops mplayer
    @staticmethod
    def stop():
        Mplayer.lock.acquire()
        try:
            try:
                if(Mplayer.currentProcess != None):
                    Mplayer.currentProcess.stop();
            except:
                logging.error("Error in stop", exc_info=True)
            finally:
                state.player_state.set_radio(None)
                Mplayer.currentProcess = None
        finally:
            Mplayer.lock.release()
            
if __name__ == "__main__":
    radio = Radio("3", "Swiss Jazz", "http://www.radioswissjazz.ch/live/mp3.m3u")
    Mplayer.start(radio)
    c = raw_input("Eingabe.")
    Mplayer.stop()
    

    
