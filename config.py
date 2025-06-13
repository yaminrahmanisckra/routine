import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'routine-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///routine.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False



