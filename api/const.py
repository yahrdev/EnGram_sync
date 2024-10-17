
class TxtData():
    RoutesName = "testsapi"
    RoutesDescription = "Tests operations"
    GetTestRoute = '/gettests'
    UpdateTestRoute = '/updatestatus'
    GeneralRoutePath = '/testroutes'
    DocRoutePath = '/docs'
    Level_name = "Level"
    WrongLevelError = "Level should be one of the following: {}"
    LevelDescription = "English Level"
    NoTestsError = "There are no tests in the database"
    NoNewTestError = "A new test was not found in the database"
    SuccessfulUpdate = "Successful"
    NonSuccessfulUpdate = "The test with ID = {0} with the level {1} was not updated"
    CanNotConvertError = "Can not convert models: {}"
    GetTestsDescription = "This route retrieves 1 test from the database or cache"
    UpdateStatusDescription = "This route updates the datetime_shown value for the tests that were shown. If the ID is an integer but does not exist, a 200 status will still be returned."
    DateTimeDescription = 'The datetime when the test was shown'
    IDDescription = 'The ID of a test'
    EmptyOptionsError = 'Options can not be empty'
    NoneValueError = 'The value {} can not be None'
    ServerStopped = 'Server stopped by user'
    DictConvertError = "Error in to_dict function: Can not convert query to the dict"
    ErrorArose = "Error arose in the function {0}, module {1}. The error: {2}"
    LoggerError = "Failed to log error: {0}. Logger error: {1}"



class InternalErrorInfo():
    ErrorText = "Internal Server Error"
    ErrorCode = 500

class BadRequestErrorInfo():
    ErrorText = "Bad Request"
    ErrorCode = 400

class NotFoundErrorInfo():
    ErrorText = "Not Found"
    LoggerDBError = "Unexpected Result from the database query: {0}. Level {1}"
    LoggerError = "The test was not found in either the cache or the database. Level {0}"
    NoTestsText = "There are no tests in the database"
    ErrorCode = 404




