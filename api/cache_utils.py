"""The functions for cache managing"""

from flask_caching import Cache
from config import settings
import redis
from typing import List, Union
from schemas import CachedTests
import threading
import time
from models import db, Questions
from flask import Flask, current_app
from sqlalchemy.orm import sessionmaker
from werkzeug.exceptions import InternalServerError
from handlers import global_error_handler_sync



"""In the following functions, CachedList has the following structure:
CachedList = [{
    "ID": int,
    "Question": str,
    "Options": [
        {
            "option_id": int,
            "option_text": str
        },
        ...
    ],
    "correct_option_id": int,
    "explanation": str,
    "datetime_shown": datetime,
    "shown": bool
}, {
    "ID": int, ...
},
...]
"""

@global_error_handler_sync
def initcache(app: Flask) -> Cache:

    """init cache for all the app"""

    cache = Cache(config = {
                            'CACHE_TYPE': settings.CACHE_TYPE,
                            'CACHE_REDIS_HOST': settings.CACHE_REDIS_HOST,
                            'CACHE_REDIS_PORT': settings.CACHE_REDIS_PORT,
                            'CACHE_REDIS_DB': settings.CACHE_REDIS_DB,
                            'CACHE_DEFAULT_TIMEOUT': settings.CACHE_DEFAULT_TIMEOUT,
                            'CACHE_KEY_PREFIX': settings.CACHE_KEY_PREFIX,
                        })
    cache.init_app(app)
    return cache

@global_error_handler_sync
def get_cache_session():
    """The cache will work with our db in separate sessions, so we should create a sessionmaker"""
    Session = sessionmaker(bind=current_app.extensions['sqlalchemy'].db.engine)
    return Session()


class EngCache():

    """The class for cache processing"""

    def __init__(self, cache):
        self.cache = cache
        #self.Session = Session
        
    @global_error_handler_sync
    def addtocache(self, Tests_list: List[dict], level):

        """adding data from database to cache"""

        ToCache = []
        for k in Tests_list:
            newcachedtest = CachedTests(**k)  #we use pydantic in order to avoide text in code
            ToCache.append(newcachedtest.model_dump())
        self.cache.set(level, ToCache)


    @global_error_handler_sync
    def get_cached_test(self, level) -> Union[dict, None]:

        """retrieving data from cache"""

        CachedList = self.cache.get(level)
        if CachedList:
            Cached_Models = [CachedTests(**onetest) for onetest in CachedList]
            Filtered_Models = [m for m in Cached_Models if not m.shown] #just that tests which were not shown
            if Filtered_Models:
                return Filtered_Models[0].model_dump()
            else:                 #the case when all tests in cache were already shown
                
                send_cach_to_db(CachedList) 
                self.cache.clear()
                return None
        else:
            return None

        

    @global_error_handler_sync
    def update_cached_tests(self, level, test_id, datetime_shown) -> bool:

        """updating Shown checkmark and datetime_shown in the cache"""

        CachedList = self.cache.get(level.value)
        if CachedList:
            i = 0
            for i, onetest in enumerate(CachedList):
                testclass = CachedTests(**onetest)
                if testclass.ID == test_id:
                    testclass.datetime_shown = datetime_shown
                    testclass.shown = True
                    CachedList[i] = testclass.model_dump()
                    self.cache.set(level.value, CachedList)
                    return True
                i += 1
        return False
        
    
class CacheListener():

    """"The cache listener in order to make necessary operations with cache before it cleared"""

    def __init__(self, cache, app: Flask, Session):
        self.redis_client = redis.Redis(host=settings.CACHE_REDIS_HOST, 
                           port=settings.CACHE_REDIS_PORT, 
                           db=settings.CACHE_REDIS_DB)
        self.cache = cache
        self.app = app
        self.ActiveListener = True
        self.Session = Session
        
        
    @global_error_handler_sync
    def on_stop_app(self):

        """It works when the app was stopped manually (like Ctrl+C in terminal)
        We should write the new datetime_shown to the database and after that clear cache"""
        
        with self.app.app_context():
            keys = self.redis_client.keys('*')    
            decoded_keys = [key.decode('utf-8') for key in keys]  
                                #originally keys are bytes like [b'key1', b'key2', b'key3']
            for k in decoded_keys:
                CachedList = self.cache.get(k)
                if CachedList:
                    send_cach_to_db(CachedList, self.Session)
                self.cache.delete(k)


    @global_error_handler_sync
    def cache_event_listener(self):

        """This function works in separate thread and makes sure that 
        the new datetime_shown was sent to the database before the cache clearing"""
        i = 0
        while self.ActiveListener:
            if i >= settings.CACHE_DEFAULT_TIMEOUT/settings.CACHE_CHECK_TIMEOUT:
                i = 0
                keys = self.redis_client.keys('*')
                decoded_keys = [key.decode('utf-8') for key in keys]
                for k in decoded_keys:
                    ttl = self.redis_client.ttl(k)  #ttl seconds left before the key will be deleted
                    if ttl <= settings.CACHE_CHECK_TIMEOUT:  
                        CachedList = self.cache.get(k)
                        if CachedList:
                            #with self.app.app_context():
                            
                            send_cach_to_db(CachedList, self.Session)
                            self.cache.delete(k)
            i += 1                 
            time.sleep(1)

    @global_error_handler_sync
    def start_cache_listener(self):
        """separate thread for cache processing"""

        listener_thread = threading.Thread(target=self.cache_event_listener)
        listener_thread.start()
        self.ActiveListener = True

    def stop_cache_listener(self):
        self.ActiveListener = False


@global_error_handler_sync
def send_cach_to_db(Tests_List, Session = None):

    """the function for sending the new datetime_shown to the database"""
    if Session:
        session = Session()
    else:
        session = db.session
    try:    
        
        for k in Tests_List:       
            onetest = CachedTests(**k)
            statement = db.update(Questions).where(Questions.id == onetest.ID).values(datetime_shown = onetest.datetime_shown)
            session.execute(statement)
            session.commit()
    except Exception as e:
        InternalServerError(e)
    finally:
        session.close()


