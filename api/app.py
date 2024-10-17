"""The main file"""

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
#without this part we lose a possibility to run the app or from the terminal or from the file

from asgiref.wsgi import WsgiToAsgi
from config import settings
from const import TxtData
from app_preparation import create_app, create_api, init_app_db, setup_cache



app = create_app(settings.DB_URL)
init_app_db(app)

if __name__ == '__main__':
    
    cache_listener = setup_cache(app)
    api = create_api(app)

    asgi_app = WsgiToAsgi(app) 
    """we use ASGI (Asynchronous Server Gateway Interface) framework 
    because we work with Uvicorn (Flask is WSGI by default)"""

    import uvicorn
    try:
        uvicorn.run(asgi_app, host= settings.SERVER_HOST, port= settings.SERVER_PORT)  

    except KeyboardInterrupt:  
        """The part for Ctrl+C in terminal. When the app is stopped the data should be written to the db"""
        print(TxtData.ServerStopped)  
        cache_listener.on_stop_app()
        cache_listener.stop_cache_listener()
        sys.exit(0)
