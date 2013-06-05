from json import JSONEncoder
        
##ERRORCODES
ERR_NUM_OK = 0
ERR_MSG_OK = ""

#radio
ERR_NUM_LIST_RADIO_STATIONS_FAILED = 1

ERR_NUM_RADIO_STATION_ID_DOES_NOT_EXIST = 2
ERR_MSG_RADIO_STATION_ID_DOES_NOT_EXIST = "Radio station with given id not found!"

ERR_NUM_PLAY_RADIO_STATION_FAILED = 3

ERR_NUM_STOP_RADIO_STATION_FAILED = 5

ERR_NUM_SET_VOLUME_FAILED = 6

ERR_NUM_SEARCH_FAILED = 7

class Response:
    def __init__(self, error_code=ERR_NUM_OK, error_message=ERR_MSG_OK, data=None):
        self.error_code = error_code
        self.error_message = error_message
        self.data = data
        

#Helper class to serialize objects to JSON
class ResponseJSONEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__          
