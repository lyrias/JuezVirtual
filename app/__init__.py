import os
from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
from dotenv import load_dotenv
from datetime import datetime
from app.extensions import db, migrate, login_manager


from app.models import Usuario  
from flask_wtf.csrf import CSRFProtect
from flask_wtf.csrf import generate_csrf

load_dotenv()

csrf = CSRFProtect()  

migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app():
    app = Flask(__name__)

    usuario = os.getenv('DB_USER')
    contrasena = os.getenv('DB_PASSWORD')
    host = os.getenv('DB_HOST')
    nombre_bd = os.getenv('DB_NAME')
    puerto = os.getenv('DB_PORT', 3306)

    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f'mysql+pymysql://{usuario}:{contrasena}@{host}:{puerto}/{nombre_bd}'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'clave_secreta_default')

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # Importa y registra tus blueprints aquí
    from app.routes.auth import auth
    from app.routes.main import main
    from app.routes.problemas import problemas_bp
    from app.concursos.routes import concursos_bp, utc_a_bolivia

    app.jinja_env.globals.update(utc_a_bolivia=utc_a_bolivia)
    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(problemas_bp)
    app.register_blueprint(concursos_bp)

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        from app.worker import iniciar_worker
        iniciar_worker()

    @app.context_processor
    def inject_now():
        return {'current_year': datetime.utcnow().year}
    
    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf)
    
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('403.html'), 403

    return app
