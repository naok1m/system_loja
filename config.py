import os

basedir = os.path.abspath(os.path.dirname(__file__))


def normalize_database_url(url):
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql+psycopg://', 1)
    elif url.startswith('postgresql://'):
        url = url.replace('postgresql://', 'postgresql+psycopg://', 1)
    return url


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise RuntimeError('SECRET_KEY não definida. Defina a variável de ambiente SECRET_KEY.')

    SQLALCHEMY_DATABASE_URI = normalize_database_url(
        os.environ.get(
            'DATABASE_URL',
            'postgresql+psycopg://postgres:postgres@localhost:5433/loja_system',
        )
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
