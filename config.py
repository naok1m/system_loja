import os

basedir = os.path.abspath(os.path.dirname(__file__))


def normalize_database_url(database_url):
    if database_url.startswith('postgres://'):
        return database_url.replace('postgres://', 'postgresql://', 1)
    return database_url


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(32).hex())
    SQLALCHEMY_DATABASE_URI = normalize_database_url(
        os.environ.get(
            'DATABASE_URL',
            'postgresql+psycopg://postgres:postgres@localhost:5432/loja_system',
        )
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
