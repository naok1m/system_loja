import logging
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # em produção (Render), env vars são configuradas no dashboard

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger(__name__)

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Faça login para acessar esta página.'


def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'),
    )
    app.config.from_object('config.Config')

    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    logger.info('DATABASE_URL scheme: %s', db_uri.split('://')[0])
    logger.info('DATABASE_URL host: %s', db_uri.split('@')[-1].split('/')[0] if '@' in db_uri else 'N/A')

    db.init_app(app)
    login_manager.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.routes import auth_bp, main_bp, produtos_bp, vendas_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(produtos_bp)
    app.register_blueprint(vendas_bp)

    @app.errorhandler(500)
    def internal_error(e):
        logger.exception('Erro 500: %s', e)
        return '<h1>Erro interno do servidor</h1><p>Veja os logs para detalhes.</p>', 500

    with app.app_context():
        try:
            db.create_all()
            logger.info('Tabelas criadas/verificadas com sucesso.')
        except Exception:
            logger.exception('Erro ao criar tabelas no banco de dados.')
            raise

    return app
