"""restx models"""

from flask_restx import fields
from flask_restx import Namespace, fields
from const import TxtData

ns = Namespace(TxtData.RoutesName, description=TxtData.RoutesDescription)

options_list = ns.model('OptionsList', {"option_id": fields.Integer, "option_text": fields.String}) 

getted_tests_model = ns.model('GettedTests', {
    'ID': fields.Integer,
    'Question': fields.String,
    'Options': fields.List(fields.Nested(options_list)),
    'correct_option_id': fields.Integer,
    'explanation': fields.String,
    'datetime_shown': fields.String
})     #to return one test to a user 


message_model = ns.model('Message', {
    'message': fields.Raw(description="Can be string or list: [{'field'/'errors': str, 'details'/'message': str]")
})    #general model for errors and messages





update_model = ns.model('TestData', {
    'Level': fields.String(description=TxtData.LevelDescription, required=True),
    'ID': fields.Integer(description=TxtData.IDDescription, required=True),
    'datetime_shown': fields.String(description=TxtData.DateTimeDescription, required=False, default=None)
})     #the model for updatetestsroute 

