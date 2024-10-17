"""Pydantic models for data validation and improvement of the code structure"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
from typing import Optional, Union, Any
from models import Levels
from typing_extensions import Annotated



class OptionsTest(BaseModel):    #the part for options in a test
    option_id: Annotated[int, Field(ge=0)]
    option_text: Annotated[str, Field(min_length=1)]
        


class GettedTests(BaseModel):   #the model for validation and processing of getted tests from the db 
    ID: Annotated[int, Field(gt=0)]
    Question:  Annotated[str, Field(min_length=3)]
    Options: list[OptionsTest]
    correct_option_id: Annotated[int, Field(ge=0)]
    explanation: Annotated[str, Field(min_length=3)]
    datetime_shown: Annotated[Union[str, datetime, None], Field(default=None)]

    


class CachedTests(BaseModel):  #the model for tests in the cache
    ID: int
    Question: str
    Options: list
    correct_option_id: int
    explanation: str
    datetime_shown: Annotated[Union[str, datetime, None], Field(default=None)]
    shown: Annotated[Optional[bool], Field(default=False)]




class TestsToDB(BaseModel):    #the model for input data validation in updatetests routes 
    Level: Levels
    ID: Annotated[int, Field(gt=0)]
    datetime_shown: Annotated[Optional[str], Field(default=None, examples=[datetime.now(timezone.utc).isoformat()])]

    @field_validator('datetime_shown')
    def check_datetime_format(cls, value):
        if value != None:
            try:
                dt = datetime.fromisoformat(value)
            except ValueError:
                raise ValueError("Invalid datetime format. Use ISO 8601 format.")
            except TypeError:
                raise TypeError("Invalid datetime format. Use ISO 8601 format.")
            
            if dt.tzinfo is None:
                    raise ValueError("Datetime must include a timezone.")
            if dt.tzinfo != timezone.utc:
                raise ValueError("Datetime must be in UTC.")
            return value


class DataTestsToDB(BaseModel):    #the model for testing 
    Level: Any
    ID: Any
    datetime_shown: Any

class Message(BaseModel):    #general model for errors and messages
    message: Union[str, list]
