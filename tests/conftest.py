"""the file for tests configuration. To run tests: pytest -v  tests/"""

import pytest
from api.models import db, Questions
from api.app_preparation import create_app, setup_cache, create_api, init_app_db
from config import settings
from api.cache_utils import CacheListener
from typing import Generator

app = create_app(settings.DB_URL)
db = init_app_db(app)
create_api(app)

@pytest.fixture()
def created_app():
    """we do not create a new db everytime but we clean datetime_shown"""

    if settings.MODE != "TEST":
        pytest.fail("An error occurred while preparing the db: the database is not for testing")

    with app.app_context():
        _update_tests()
        yield app


@pytest.fixture()
def init_test_cache() -> Generator[CacheListener, None, None]:
    """the fixture for cache init"""

    with app.app_context():
        try:
            cache_listener = setup_cache(app)
            yield cache_listener
        except Exception as e:
            pytest.fail(f"An error occurred while preparing the cache: {e}")
        finally:
            try:
                cache_listener.on_stop_app()
                cache_listener.stop_cache_listener()
            except Exception as e:
                pytest.fail(f"An error occurred while stopping the cache listener: {e}")
            



@pytest.fixture()
def client(created_app):
    created_app.testing = True
    return created_app.test_client()


@pytest.fixture(scope="module")
def select_level() -> tuple[str, int, dict]:
    """this fixture checks the testing db and gathers information about existing questions for every level"""
    try:
        Questions_Count = _get_tests_from_db()
        Selected_Level = max(Questions_Count, key=Questions_Count.get)
        if Questions_Count[Selected_Level] > 50:  #<=50 questions is enough for testing
            return Selected_Level, 50, Questions_Count
        else:
            return Selected_Level, Questions_Count[Selected_Level], Questions_Count
    except Exception as e:
            pytest.fail(f"An error occurred while selecting the level: {e}")
    


@pytest.fixture(scope="module")
def level(select_level) -> str:
    """selected testing level for all tests"""
    return select_level[0]


@pytest.fixture(scope="module")
def questions_number_to_test(select_level) -> int:
    """the max number of questions to use in test_consistency"""
    return select_level[1]

@pytest.fixture(scope="module")
def questions_count_dict(select_level) -> dict:
    """the dict {Level: number of tests in db}"""
    return select_level[2]

    

def _get_tests_from_db() -> dict:
    """we check existing questions in the testing db"""
    with app.app_context():
        try:
            
            Stmt = db.select(Questions)
            Result = db.session.execute(Stmt)
            Questions_Count = {}
            
            for (q,) in Result.fetchall():
                q: Questions
                if q.level.value in Questions_Count:
                    Questions_Count[q.level.value] += 1
                else:
                    Questions_Count[q.level.value] = 1
            return Questions_Count
        except Exception as e:
            pytest.fail(f"An error occurred while getting data from the db: {e}")




def check_datetime_in_db(app, for_level) -> int:
    """get number of updated questions in db"""
    with app.app_context():
        try:
            Stmt = db.select(Questions).where(Questions.level == for_level)
            Result = db.session.execute(Stmt)
            i = 0
            for (q,) in Result.fetchall():
                q: Questions
                if q.datetime_shown:
                    i += 1
            return i

        except Exception as e:
            pytest.fail(f"An error occurred while getting data from the db for checking: {e}")

        



def _update_tests():
    """for preparing the testing db"""
    try:
        statement = db.update(Questions).values(datetime_shown = None)
        db.session.execute(statement)
        db.session.commit() 
    except Exception as e:
        pytest.fail(f"An error occurred while preparing the db: {e}")
