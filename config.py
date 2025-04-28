# config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'supersecretkey'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:Anirudh%401102@localhost/buyme'
    SQLALCHEMY_TRACK_MODIFICATIONS = False