The **API** generates tests for English grammar learning and can be used as a backend for English learning-related projects.

The app was built using **Flask** and has two endpoints: `gettests` and `updatestatus`.

- The first endpoint generates one test each time it's called.
- The second endpoint updates the date and time when the test was displayed on the frontend.

When the `gettests` endpoint is called, the app retrieves a fixed number of tests from the database and stores them in the cache. Users receive one test from the cache per call, so the app avoids making database requests for every endpoint call. The `updatestatus` endpoint ensures test variation by sorting the tests by the `datetime_shown` field, ensuring users always receive the oldest available test.

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
