import logging
from const import TxtData, NotFoundErrorInfo, InternalErrorInfo, BadRequestErrorInfo, NotFoundErrorInfo
from werkzeug.exceptions import HTTPException
import functools
from schemas import Message
from models import Levels
from flask import jsonify

def global_error_handler_sync(func):

    """general handler for Internal Server Error logging of sync functions"""

    @functools.wraps(func) 
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log_raise_error(e, func)
    return wrapper



def log_raise_error(exception, func):

    """The function for errors detailed handling"""

    if not hasattr(exception, '_logged'): #check whether was logged already
        module_name = func.__module__
        function_name = func.__name__ 
        error_text = TxtData.ErrorArose.format(function_name, module_name, str(exception))
        try:
            logging.error(error_text)

        except Exception as e:  #if smth happend with the logger
            print(TxtData.LoggerError.format(error_text, str(e)))

        setattr(exception, '_logged', True)  
            #add a new attribute in order to mark the error as logged already. 
            #Otherwise we will see the same error for each function in the stack
        raise



class NoTestsError(HTTPException):

    """404 error for the case when there are no tests in db"""

    code = NotFoundErrorInfo.ErrorCode
    description = NotFoundErrorInfo.NoTestsText


class WrongLevelError(HTTPException):

    """400 error for the case when wrong level"""

    code = BadRequestErrorInfo.ErrorCode
    description = TxtData.WrongLevelError.format(list(Levels._value2member_map_))



def handle_request_validation_error(error):
    """400. We detail the error that arises when a user sends incorrect data in JSON"""
    try:
        message = Message(message=[{"field": err["loc"][0], "details": err["msg"]} for err in error.validation_error.errors()])
        return jsonify(message.model_dump()), BadRequestErrorInfo.ErrorCode
    except Exception as e:
        message = Message(message=str(error))
        return jsonify(message.model_dump()), BadRequestErrorInfo.ErrorCode


def handle_bad_request_error(error):
    """400. We detail the error that arises when a user sends incorrect data (not json for example)"""
    message = Message(message=str(error))
    return jsonify(message.model_dump()), BadRequestErrorInfo.ErrorCode


def handle_not_found_error(error):
    """404. We detail any 404 error"""
    message = Message(message=str(error))
    return jsonify(message.model_dump()), NotFoundErrorInfo.ErrorCode


def handle_no_tests_error(error):
    """404. We detail the error that arises when there are not tests in db"""
    message = Message(message=NotFoundErrorInfo.NoTestsText)
    return jsonify(message.model_dump()), NotFoundErrorInfo.ErrorCode


def handle_internal_error(error):
    """500. We change the format of 500 error"""
    message = Message(message=InternalErrorInfo.ErrorText)
    return jsonify(message.model_dump()), InternalErrorInfo.ErrorCode


def handle_wrong_level_error(error):
    """400. We detail the error that arises when a user sends wrong level"""
    message = Message(message=TxtData.WrongLevelError.format(list(Levels._value2member_map_)))
    return jsonify(message.model_dump()), BadRequestErrorInfo.ErrorCode


def register_error_handlers(app):
    app.register_error_handler(404, handle_not_found_error)
    app.register_error_handler(400, handle_bad_request_error)
    app.register_error_handler(500, handle_internal_error)
    app.register_error_handler(NoTestsError, handle_no_tests_error)
    app.register_error_handler(WrongLevelError, handle_wrong_level_error)
    app.register_error_handler(400, handle_request_validation_error)