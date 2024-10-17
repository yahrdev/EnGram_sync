from flask import redirect, request, current_app
from schemas import TestsToDB, GettedTests, Message, OptionsTest
from models import db, Options, Questions, Levels
from sqlalchemy.orm import aliased
from flask_restx import Resource
from models_restx import ns, getted_tests_model, message_model, update_model
import logging
from typing import List
from werkzeug.exceptions import BadRequest
from pydantic import ValidationError
from const import TxtData, BadRequestErrorInfo, NotFoundErrorInfo, InternalErrorInfo
import config
from handlers import global_error_handler_sync, log_raise_error, WrongLevelError, NoTestsError
from datetime import datetime, timezone

# logger = getLogger(__name__)
# basicConfig(filemode='a+', 
#             format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s'
# )  #change configuration in order to have understandable error in the terminal



@ns.route('/')  #/testroutes/
class Index(Resource):
    def get(self):
        return redirect('/docs')
    
    

@ns.route(TxtData.GetTestRoute)    #/testroutes/gettests
@ns.doc(description=TxtData.GetTestsDescription)
class GetTests(Resource):   
    @ns.marshal_with(getted_tests_model)
    @ns.response(InternalErrorInfo.ErrorCode, InternalErrorInfo.ErrorText, message_model)
    @ns.response(NotFoundErrorInfo.ErrorCode, NotFoundErrorInfo.ErrorText, message_model)
    @ns.response(BadRequestErrorInfo.ErrorCode, BadRequestErrorInfo.ErrorText, message_model)
    @ns.doc(params={TxtData.Level_name: TxtData.LevelDescription})
    def get(self):
        #The route for a test retrieving. Before a test is returned, 
        #the route get it from cache. If there are no tests in the cache, 
        #the new tests group is taken from db and is written to the cache

        data = request.args
        try:
            level = data.get(TxtData.Level_name)
            if not level in Levels._value2member_map_:     #a list of available levels
                raise WrongLevelError()
            
            EngCache = current_app.config['EngCache']  
            OneTest = EngCache.get_cached_test(level)
            if not OneTest:
                TestsList = _get_tests(level)
                EngCache.addtocache(TestsList, level)
                OneTest = EngCache.get_cached_test(level)
                if not OneTest:
                    raise NoTestsError()
            return OneTest
        except Exception as e:
            log_raise_error(e, GetTests)
            raise e
        

@ns.route(TxtData.UpdateTestRoute) #/testroutes/updatestatus
@ns.doc(description=TxtData.UpdateStatusDescription)
class UpdateStatus(Resource):
    @ns.marshal_with(message_model)
    @ns.expect(update_model)
    @ns.response(InternalErrorInfo.ErrorCode, InternalErrorInfo.ErrorText, message_model)
    @ns.response(NotFoundErrorInfo.ErrorCode, NotFoundErrorInfo.ErrorText, message_model)
    @ns.response(BadRequestErrorInfo.ErrorCode, BadRequestErrorInfo.ErrorText, message_model)
    def post(self):
        #The route for updating data in the cache.
        #We update Shown and datetime_shown values. So tests will not be repeated

        try:
            try:
                data = request.json
                if not data:
                    data = {}
                onetest = TestsToDB(**data) #for data validation

            except ValidationError as e:
                errors = [{"field": err["loc"][0], "details": err["msg"]} for err in e.errors()]
                raise BadRequest(errors)
            
            EngCache = current_app.config['EngCache']
            if not onetest.datetime_shown:
                onetest.datetime_shown = datetime.now(timezone.utc).isoformat()
            if not EngCache.update_cached_tests(onetest.Level, onetest.ID, onetest.datetime_shown):
                logging.warning(TxtData.NonSuccessfulUpdate.format(onetest.ID, onetest.Level.value))

            return Message(message=TxtData.SuccessfulUpdate).model_dump(), 200
            #we return Success for both cases: a test is in the cache or not
        except Exception as e:
            log_raise_error(e, UpdateStatus)
            raise e
        

@global_error_handler_sync
def _get_tests(Level) -> List[dict]:

    """The function for tests retrieving from the db"""
    SubqStmt = db.select(Questions).where(Questions.level == Level).order_by(Questions.datetime_shown).limit(config.settings.NUMBER_OF_TESTS) 
    #select * from question order by datetime_shown limit config.settings.NUMBER_OF_TESTS

    Subquery = SubqStmt.subquery()
    QuestionsAlias = aliased(Questions, Subquery) 
    #apply Questions class to Subquery in order to create necessary structure

    ResultStmt = db.select(QuestionsAlias, Options).join_from(QuestionsAlias, Options, QuestionsAlias.id == Options.question_id, isouter=False)
    #select Q.*, options.* from (Subquery) as Q inner join Options on Q.id = options.question_id;
    
    Result = db.session.execute(ResultStmt)

    if not Result:
        TestsList = [] 
        raise NoTestsError()

    QuestionsList = []   #Received questions models list
    OptionsList = []    #Received options models list
    TestsList = []   #json to return
    idis = set()     #Received questions' IDs


    """ Result.fetchall() returns a list of tuples filled out by SQLAlchemy models
    We try to separate Questions from Options below 
    Our goal - to have the following json:
        {
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
            "datetime_shown": datetime
        }   
    """

    for q, o in Result.fetchall():  #separation
        q: Questions
        o: Options
        
        OptionsList.append(o)

        if not q.id in idis:   #select only unique models without duplicates
            QuestionsList.append(q)   
        idis.add(q.id)
    

    for q in QuestionsList:   #joining together to the json
        q: Questions
        OptionsShortList = []  #short options list without question_id
        for o in OptionsList:
            o: Options
            
            if q.id == o.question_id:
                OptionsModel = OptionsTest(option_id=o.option_id, option_text=o.option_text)
                OptionsShortList.append(OptionsModel.model_dump())


        newtest = GettedTests(ID=q.id,
                            Question=q.question,
                            Options=OptionsShortList,
                            correct_option_id=q.correct_id,
                            explanation= q.explanation,
                            datetime_shown=q.datetime_shown                                        
                            ) 

        TestsList.append(newtest.model_dump())
    return TestsList



