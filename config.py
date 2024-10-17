#the file for importing of the config settings which will be used for the database connection


from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DB_USER: str
    DB_PASS: str
    DB_HOST: str
    DB_NAME: str
    DB_PORT: int
    MODE: str
    CACHE_REDIS_HOST: str
    CACHE_REDIS_PORT: int
    CACHE_REDIS_DB: int
    CACHE_TYPE: str
    CACHE_DEFAULT_TIMEOUT: int  #ttl for cache
    CACHE_KEY_PREFIX: str
    CACHE_CHECK_TIMEOUT: int  #how frequently check the ttl of the cache
    NUMBER_OF_TESTS: int
    SERVER_HOST: str
    SERVER_PORT: int

    @property
    def DB_URL(self):
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    

    model_config = SettingsConfigDict(env_file=".env", extra='allow')

settings = Settings()
