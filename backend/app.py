# App.py, Core of the Application.

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)
    CORS(app)
    
    # Import and register blueprints
    try:
        from auth import auth_bp
        from routes import project_bp, proposal_bp
        
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(project_bp, url_prefix='/api/projects')
        app.register_blueprint(proposal_bp, url_prefix='/api/proposals')
        print("Blueprints registered successfully!")
    except Exception as e:
        print(f"Error registering blueprints: {e}")
    
    # Create tables
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully!")
        except Exception as e:
            print(f"Error creating tables: {e}")
    
    # Health check route
    @app.route('/api/health')
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'SharkTalent API is Functional!'})
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)