# Models.py that will create an SQLite Database and store the information.

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import bcrypt

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'client', 'freelancer', 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    projects = db.relationship('Project', backref='client', lazy=True, foreign_keys='Project.client_id')
    proposals = db.relationship('Proposal', backref='freelancer', lazy=True, foreign_keys='Proposal.freelancer_id')
    
    def set_password(self, password):
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

class Project(db.Model):
    __tablename__ = 'project'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    budget = db.Column(db.Float, nullable=False)
    skills_required = db.Column(db.String(300))
    status = db.Column(db.String(20), default='open')  # open, in_progress, completed
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    proposals = db.relationship('Proposal', backref='project', lazy=True)

class Proposal(db.Model):
    __tablename__ = 'proposal'
    
    id = db.Column(db.Integer, primary_key=True)
    cover_letter = db.Column(db.Text, nullable=False)
    bid_amount = db.Column(db.Float, nullable=False)
    timeline_days = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    freelancer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)