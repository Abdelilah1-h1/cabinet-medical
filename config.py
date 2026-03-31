import os

class Config:
    # Configuration de base
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'votre-cle-secrete-a-changer-en-production'
    
    # Configuration de la base de données
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///cabinet.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuration Flask-Login
    SESSION_COOKIE_SECURE = False  # Mettre True en production avec HTTPS
    REMEMBER_COOKIE_DURATION = 3600  # 1 heure
