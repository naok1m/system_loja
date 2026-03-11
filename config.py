import os

basedir = os.path.abspath(os.path.dirname(__file__))


def normalize_database_url(url):
    url = url.strip()
    if url.startswith('postgres://'):
        url = 'postgresql+psycopg://' + url[len('postgres://'):]
    elif url.startswith('postgresql://') and '+' not in url.split('://')[0]:
        url = 'postgresql+psycopg://' + url[len('postgresql://'):]
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
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,   # testa a conexão antes de usar; evita erros após hibernação
        'pool_recycle': 280,     # recicla conexões a cada ~5min (evita timeout do Postgres)
        'pool_size': 3,
        'max_overflow': 2,
    }
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
