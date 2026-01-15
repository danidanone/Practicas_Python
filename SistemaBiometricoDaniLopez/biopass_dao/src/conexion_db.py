import psycopg2
from src.config import Config

class DBConnection:
    _connection = None

    @classmethod
    def get_connection(cls):
        if cls._connection is None or cls._connection.closed:
            config = Config()
            cls._connection = psycopg2.connect(**config.get_db_params())
        return cls._connection