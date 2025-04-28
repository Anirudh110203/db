# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # buyer, seller, rep, admin

    items = db.relationship('Item', backref='seller', lazy=True)
    bids = db.relationship('Bid', backref='user', lazy=True)
    alerts = db.relationship('Alert', backref='user', lazy=True)
    
    # FIXED: Tell SQLAlchemy which foreign key to use
    actions = db.relationship(
        'CustomerActionLog',
        backref='rep',
        lazy=True,
        foreign_keys='CustomerActionLog.rep_id'
    )
class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)

    children = db.relationship('Category')

class Item(db.Model):
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Extra vehicle-specific fields
    vehicle_make = db.Column(db.String(100))
    vehicle_model = db.Column(db.String(100))
    year = db.Column(db.Integer)
    mileage = db.Column(db.Integer)

    auction = db.relationship('Auction', backref='item', uselist=False)

class Auction(db.Model):
    __tablename__ = 'auctions'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    start_price = db.Column(db.Float, nullable=False)
    min_increment = db.Column(db.Float, nullable=False)
    min_price = db.Column(db.Float, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False)

    bids = db.relationship('Bid', backref='auction', lazy=True)

class Bid(db.Model):
    __tablename__ = 'bids'

    id = db.Column(db.Integer, primary_key=True)
    auction_id = db.Column(db.Integer, db.ForeignKey('auctions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    bid_time = db.Column(db.DateTime, default=datetime.utcnow)
    bid_amount = db.Column(db.Float, nullable=False)
    max_auto_bid = db.Column(db.Float, nullable=True)

class Alert(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    keyword = db.Column(db.String(100), nullable=False)

class CustomerActionLog(db.Model):
    __tablename__ = 'customer_action_logs'

    id = db.Column(db.Integer, primary_key=True)
    rep_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action_type = db.Column(db.String(100), nullable=False)
    action_time = db.Column(db.DateTime, default=datetime.utcnow)
    target_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    details = db.Column(db.Text)