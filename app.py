import os
from flask import Flask, render_template, redirect, url_for

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DB_NAME='kasir_db',
        DB_USER='postgres',
        DB_PASS='5432',
        DB_HOST='localhost',
        DB_PORT='5432',
        UPLOAD_FOLDER='static/uploads',
        MAX_CONTENT_LENGTH=16 * 1024 * 1024, # 16MB limit
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize DB
    import db
    db.init_app(app)

    # Register Blueprints
    import auth
    app.register_blueprint(auth.bp)

    from routes import api, admin, pos
    app.register_blueprint(api.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(pos.bp)

    # Temporary Index
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
