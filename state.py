import logging
import csv
import copy
import threading
import datetime
import subprocess
import os
import re

class Revision:
    def __init__(self):
        self.revision = Revision.timestamp()       
        
    @staticmethod
    def timestamp():
        return int((datetime.datetime.utcnow() - datetime.datetime(2013,1,1)).total_seconds()*1000)
    
    def as_model(self):
        return dict(revision = self.revision)

class RevisionLock(Revision):
    def __init__(self):
        Revision.__init__(self)
        self.lock = threading.RLock()
        self.waiters = set()

    def wait_for_update(self, revision, callback):
        self.lock.acquire()
        try:
            if long(revision) < self.revision:
                callback(self.as_model())
                return True
            else:
                self.waiters.add(callback)
                return False
        finally:
            self.lock.release()                    
            
    def cancel_wait(self, callback):
        self.lock.acquire()
        try:
            if callback in self.waiters:
                self.waiters.remove(callback)
                return True
            else:
                return False               
        finally:
            self.lock.release()                            

    def update_revision(self, revision = None):
        self.lock.acquire()        
        try:
            if revision == None or revision <= self.revision:
                self.revision = self.revision + 1            
            else:
                self.revision = revision
            #super(Revision, self).update_revision()
            model = self.as_model()
            waiters = self.waiters
            self.waiters = set()
        except:
            print "Unexpected error:", sys.exc_info()[0]
            raise            
        finally:
            self.lock.release()
            
        for callback in waiters:
            try:
                callback(model)
            except:
                logging.error("Error in waiter callback", exc_info=True)       
            
class Radio:
    def __init__(self, id, display_name, stream_url):
        self.id = id
        self.display_name = display_name
        self.stream_url = stream_url

    def as_model(self):
        return self.__dict__
        
class Favorites(RevisionLock):
    def __init__(self):
        RevisionLock.__init__(self)
        self.radios = []
        self.load_radios()
        
    def load_radios(self): 
        path = os.path.dirname(os.path.realpath(__file__))
        with open(path + '/favorites.csv', 'rb') as csvfile:
            radioreader = csv.reader(csvfile, delimiter=';', quotechar='\"')            
            count = 0
            for row in radioreader:
                self.radios.append(Radio(row[0], row[1], row[2]))
                
    def get_favorite(self, id):
        self.lock.acquire()
        try:
            for radio in self.radios:
                if(str(radio.id) == str(id)):
                    return copy.deepcopy(radio)
            return None
        finally:
            self.lock.release()
    
    def as_model(self):
        self.lock.acquire()
        try:
            result = Revision.as_model(self)
            result['radios'] = copy.deepcopy(self.radios)
            return result;
        finally:
            self.lock.release()
            
class Title:
    def __init__(self, title):
        self.timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.title = title
                                
class PlayerState(RevisionLock) :
    def __init__(self):
        RevisionLock.__init__(self)
        self.radio = None
        self.playlist = []
        
    def set_radio(self, radio): 
        self.lock.acquire()
        try:
            self.radio = radio # set radio 
            del self.playlist[:] # delete playlist
            self.update_revision()
        except:
            print "Unexpected error:", sys.exc_info()[0]
            raise            
        finally:
            self.lock.release()
            
    def add_title(self, title):
        self.lock.acquire()
        try:
            if len(self.playlist) == 0 or self.playlist[0].title != title:
                self.playlist.insert(0, Title(title))
            while len(self.playlist) > 5:
                del self.playlist[len(self.playlist) - 1]
                
            self.update_revision()
        finally:
            self.lock.release()   
            
    def as_model(self):
        self.lock.acquire()
        try:
            result = Revision.as_model(self)
            result['radio'] = copy.deepcopy(self.radio)
            result['playlist'] = copy.deepcopy(self.playlist)
            return result;
        finally:
            self.lock.release()
            
            
class MixerState(RevisionLock):
    def __init__(self):
        RevisionLock.__init__(self)
        self.volume = self.get_volume()
        
    def get_volume(self):
        p = subprocess.Popen(['amixer'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        volume = ""
        while(True):
            retcode = p.poll() #returns None while subprocess is running
            line = p.stdout.readline()
            
            if volume == "" and  line.find("Front Left:") != -1:
                print line
                volume = re.search('\[([0-9]+)%\]',line).group(1)
            
            if retcode is not None:
                break
        
        return int(volume)

    def set_volume(self, revision, volume):
        self.lock.acquire()
        try:
            if revision <=  self.revision:
                return;
            
            if self.volume != volume:
                subprocess.call(['amixer', 'set', 'Speaker', '--', str(volume) + '%']) #USER CALL
                subprocess.call(['sudo', 'alsactl', 'store']) #ROOT CALL
                #subprocess.call(['amixer', 'cset', 'numid=3', '--', volume])            
                
                self.volume = self.get_volume();
            
            self.update_revision(long(revision))
        finally:
            self.lock.release()   
            
    def as_model(self):
        self.lock.acquire()
        try:
            result = Revision.as_model(self)
            result['volume'] = copy.deepcopy(self.volume)
            return result;
        finally:
            self.lock.release()            

class StateContainer: 
    def __init__(self):
        self.currentPlayer = None
        self.player_state = PlayerState()
        self.favorites = Favorites()
        self.mixer_state = MixerState();
    
state = StateContainer()
    
    
    
    

