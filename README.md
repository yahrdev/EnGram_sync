The **API** generates tests for English grammar learning and can be used as a backend for English learning-related projects.

The app was built using **Flask** and has two endpoints: `gettests` and `updatestatus`.

- The first endpoint generates one test each time it's called.
- The second endpoint updates the date and time when the test was displayed on the frontend.

When the `gettests` endpoint is called, the app retrieves a fixed number of tests from the database and stores them in the cache. Users receive one test from the cache per call, so the app avoids making database requests for every endpoint call. The `updatestatus` endpoint ensures test variation by sorting the tests by the datetime_shown field, so users always receive the oldest available test.

## Technologies Used

- **Flask**: For building the web API.
- **SQLAlchemy**: For ORM functionality with MySQL.
- **Flask-Migrate**: To handle database migrations.
- **PyMySQL**: MySQL client for Python.
- **Redis**: Used for managing the cache layer.
- **Pydantic**: For data validation.
- **Flask-RESTX**: For creating RESTful services and documenting them.
- **Pytest**: For writing and running unit tests.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/EnGram_sync.git
```

### 2. Navigate into the project directory

```bash
cd EnGram_sync
```

### 3. Install the dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up the environment

Create .env and .test.env files based on the provided examples. 

### 5. Set up the database

Create the database in MySQL and initialize and apply migrations:

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```
You can use that [Initial Migration Script](https://github.com/yahrdev/EnGram_sync/blob/main/api/migrations/versions/3e4caf632902_initial_migration.py) which is provided in this repository.
Also populate the database with data. 

### 6. Set up Redis

Download Redis and place the folder on disk C (for example). Open a command prompt and navigate to the Redis folder:

```bash
cd C:\Redis
```

Set up configuration files. You can either modify the redis.windows.conf or create two copies: redis-prod.conf and redis-test.conf, and specify different ports in each file.
Start Redis servers:

```bash
redis-server.exe redis-test.conf
```

```bash
redis-server.exe redis-prod.conf
```

### 7. Run the application

```bash
python api/app.py
```

### 8. Testing

```bash
pytest -v tests/test_api.py  
```

And check Swagger: http://127.0.0.1:8000/docs
