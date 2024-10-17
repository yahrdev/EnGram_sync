"""This file prepares the application for execution"""

from flask import Flask, redirect
from config import settings
from flask_migrate import Migrate
from models import db
from routes import ns as routes_namespace
from flask_restx import Api
from cache_utils import EngCache, CacheListener, initcache
from const import TxtData
from sqlalchemy.orm import sessionmaker
from handlers import global_error_handler_sync, register_error_handlers

@global_error_handler_sync
def create_app(URL = settings.DB_URL):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = URL
    app.config['RESTX_ERROR_404_HELP'] = False  
                #in order to hide automatically generated text which is added to 404 error

    app.config["RESTX_MASK_SWAGGER"] = False    
    
    @app.route('/')   #for redirecting from http://127.0.0.1:8000/
    def index():
        return redirect('/docs')
    
    register_error_handlers(app)

    return app

@global_error_handler_sync
def init_app_db(app: Flask):
    db.init_app(app)
    migrate = Migrate()
    migrate.init_app(app, db) 
    return db

@global_error_handler_sync
def create_api(app: Flask):
    api = Api(app, doc=TxtData.DocRoutePath)  #we use flask_restx in order to work with Swagger
    api.add_namespace(routes_namespace, path='')  #add routes to the api
    return api

@global_error_handler_sync
def setup_cache(app: Flask):
    """The cache will work with our db in separate sessions, so we should create a sessionmaker"""
    with app.app_context():
        cache = initcache(app)
        engcache = EngCache(cache)  #init the class for cache processing
        Session = sessionmaker(bind=db.engine) #separate session for CacheListener
        cache_listener = CacheListener(cache, app, Session)   #init separate thread to listen cache
        cache_listener.start_cache_listener() #start the thread
        app.config['EngCache'] = engcache #config in order to pass EngCache class from cache_utils.py to routes.py
    return cache_listener
