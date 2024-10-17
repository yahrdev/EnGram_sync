from api.schemas import GettedTests
import json
from typing import Tuple, Any, Generator, Optional
from datetime import datetime, timezone
from api.models import Levels
import pytest
from api.schemas import DataTestsToDB
from pydantic import ValidationError
from api.cache_utils import CacheListener
from config import settings
import time
from conftest import check_datetime_in_db

get_data = [("NE", 200),            #the level which has questions in db
            ('', 400),              #the empty level
            ('A200', 400),          #non existent level
            ("E", 404)]             #the level which does not have questions in db

def post_data() -> list:
    """the func for calculation testing data for test_update_endpoint"""
    try:
        Testing_Data = []
        for t in get_data:                              #first we check the same data as for test_get_endpoint
            One_Unit = DataTestsToDB(Level=t[0], ID = None, datetime_shown=None)
            if t[0] == "E":                             #we return 200 if a question was not found in db
                Testing_Data.append((One_Unit.model_dump(), 200))
            else:
                Testing_Data.append((One_Unit.model_dump(), t[1]))
        One_Unit = DataTestsToDB(Level= "NE", ID = 5000, datetime_shown=None)   #non existent id
        Testing_Data.append((One_Unit.model_dump(), 200))
        One_Unit = DataTestsToDB(Level= "NE", ID = 'test', datetime_shown=None)  #wrong id type
        Testing_Data.append((One_Unit.model_dump(), 400))
        One_Unit = DataTestsToDB(Level= "NE", ID = None, datetime_shown='test')  #wrong type of datetime_shown
        Testing_Data.append((One_Unit.model_dump(), 400))
        Testing_Data.append(('', 400))      #wrong json
        return Testing_Data
    except Exception as e:
        pytest.fail(f"An error occurred while preparing post_data for testing: {e}")


@pytest.mark.usefixtures("init_test_cache")
class TestEndpoints():

    @pytest.mark.parametrize("testing_level, expected_status", get_data)
    def test_get_endpoint(self, client, level, questions_count_dict, testing_level, expected_status):
        """testing gettests endpoint"""

        testing_level = calculate_level_from_data(level, questions_count_dict, testing_level)
        if testing_level == False:
            pytest.skip(f"test_get_endpoint: Test skipped due to not found" 
                        f"the appropriate testing level without questions in db")
        
        response_code, response_dict = get_question(client, testing_level)
        assert response_code == expected_status, (
                f"test_get_endpoint: Expected status code {expected_status}, but got {response_code}" 
                f"when level {testing_level}")
        if expected_status == 200:
            try:
                GettedTests(**response_dict)  #check correctness of the returned data 
                assert True
            except ValidationError:
                pytest.fail(f"test_get_endpoint: Data was not validated at level {testing_level}")



    @pytest.mark.parametrize("dict_to_test, expected_status", post_data())
    def test_update_endpoint(self, client, level, questions_count_dict, dict_to_test, expected_status):
        """testing updatestatus endpoint"""
        if isinstance(dict_to_test, dict):
            testing_model = DataTestsToDB(**dict_to_test) #we use schemas in order to avoid text typing

            testing_level = calculate_level_from_data(level, questions_count_dict, testing_model.Level)
            if testing_level == False:
                pytest.skip(
                    f"test_update_endpoint: Test skipped due to not found" 
                    f"the appropriate testing level without questions in db")

            response_code, response_dict = get_question(client, level)
            response_model = GettedTests(**response_dict)
            if testing_model.datetime_shown is None:        #None was added for now datetime selection
                new_datatime = datetime.now(timezone.utc)
            else:
                new_datatime = testing_model.datetime_shown
            if testing_model.ID == None:
                testing_id = response_model.ID    #None was added for getted id from get enpoint 
            else:
                testing_id = testing_model.ID

            response_code = post_question(client, testing_level, testing_id,
                                        new_datatime.isoformat() if isinstance(new_datatime, datetime) else new_datatime)
            #in case of wrong datetime_shown type we can not use isoformat()

        else:
            response = client.post("/testsapi/updatestatus", json=dict_to_test)
            response_code = response.status_code
        
        assert response_code == expected_status, (
                    f"test_update_endpoint: Expected status code {expected_status}, but got {response_code}" 
                    f" when data {dict_to_test}")



    def test_consistency(self, client, level, questions_number_to_test):
        """We test if the endpoints return non-repeated questions for some time.
        For this we choose a level with the biggest questions number. 
        They should not be repeated until they are finished"""

        i = 1
        Returned_IDs = []
        while i <= questions_number_to_test:
            response_code, response_dict = get_question(client, level)
            assert response_code == 200, (
                f"test_consistency: Expected status code 200, but got {response_code} when data getting data")
            response_model = GettedTests(**response_dict)
            if response_model.ID in Returned_IDs:
                pytest.fail(f"test_consistency: Repeated test {response_model.ID}")  
            else:
                Returned_IDs.append(response_model.ID)        
            response_code = post_question(client, 
                                          level, 
                                          response_model.ID, datetime.now(timezone.utc).isoformat())
            assert response_code == 200
            i+=1

@pytest.mark.usefixtures("init_test_cache")
class TestCache():

    def test_cache_data(self, client, created_app, level):
        """testing of cache data after get and post endpoints running"""

        response_code, response_dict = get_question(client, level)
        response_model = GettedTests(**response_dict)
        new_datatime = datetime.now(timezone.utc)
        post_question(client, level, response_model.ID, new_datatime.isoformat())

        cache = created_app.config['EngCache'].cache
        Cache_list = cache.get(level)
        assert any(Cache_list), (
                        f"test_cache_data: Cache is empty when level {level}, id {response_model.ID}," 
                        "datetime {new_datatime}")
        Found = False
        for t in Cache_list:  #check whether datetime_shown was changed
            if t['ID'] == response_model.ID:
                
                assert t['datetime_shown'] == new_datatime.isoformat(), (
                    f"test_cache_data: Cache datatime is wrong when level {level}," 
                    f"id {response_model.ID}, Expected datetime {new_datatime.isoformat()}, but got {t['datetime_shown']}")
                Found = True
        assert Found, (
            f"test_cache_data: Data not found in cache when level {level}, id {response_model.ID}," 
            f"datetime {new_datatime.isoformat()}")


    
    def test_cache_listener(self, mocker, client, created_app, level, 
                            questions_number_to_test, 
                            init_test_cache: Generator[CacheListener, None, None]):
        
        """testing cache listener which works simultaneously with the app"""


        mocker.patch('config.settings.CACHE_DEFAULT_TIMEOUT', 6)
        mocker.patch('config.settings.CACHE_CHECK_TIMEOUT', 3)
        cache_listener = init_test_cache
        redis_client_test = cache_listener.redis_client


        i = 1
        while i <= questions_number_to_test/2:  
            """run get and update endpoints questions_number_to_test/2 times"""

            response_code, response_dict = get_question(client, level)
            response_model = GettedTests(**response_dict)
            new_datatime = datetime.now(timezone.utc)
            post_question(client, level, response_model.ID, new_datatime.isoformat())
            i += 1

        keys_before = redis_client_test.keys('*') #check in cache
        assert len(keys_before) > 0, f"test_cache_listener: Data not found in cache when level {level}"
    
        mocker.patch.object(redis_client_test, 'ttl', return_value=settings.CACHE_CHECK_TIMEOUT - 1)
        #replace current ttl in order to do the process quicker

        time.sleep(settings.CACHE_DEFAULT_TIMEOUT/settings.CACHE_CHECK_TIMEOUT + 2)
        #should wait some time while cache listener processes the new ttl


        keys_after = redis_client_test.keys('*')
        assert len(keys_after) == 0, (
            f"test_cache_listener: Data was not removed from the cache when level {level}")
        
        updated_tests = check_datetime_in_db(created_app, level)  #check whether datetime_shown was updated
        assert questions_number_to_test/2 == updated_tests, (
                f"test_cache_listener: Should be updated {questions_number_to_test/2}" 
                f"lines in db, but updated {updated_tests} lines")

    

def get_question(client, level) -> Tuple[int, Any]:
    """running gettests enpoint"""

    response = client.get('/testsapi/gettests?Level=' + str(level))
    decoded_string = response.data.decode('utf-8')
    response_dict = json.loads(decoded_string)
    return response.status_code, response_dict

def post_question(client, level, ID, datetime_shown) -> int:  
    """running updatestatus enpoint"""

    testing_json={
        "Level": level,
        "ID": ID,
        "datetime_shown": datetime_shown
        }
    response = client.post("/testsapi/updatestatus", json=testing_json)
    return response.status_code


def calculate_level_from_data(level, questions_count_dict, testing_level) -> Optional[str]:
    """We replace testing data with data from the fixtures because 
    otherwise we can not call the fixtures before calling the testing functions"""

    if testing_level == "NE":
        testing_level = level   #selected testing level for all tests
    if testing_level == "E":    #try to find a level with no questions
        for l in Levels._value2member_map_:
            if not l in questions_count_dict:
                testing_level = l
                break
    if testing_level in ["NE", "E"]:
        return False
    else:
        return testing_level











                





    
    
    