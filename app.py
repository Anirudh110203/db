# app.py
from flask import Flask, render_template, redirect, url_for, flash, request, session
from models import db, User, Item, Auction, Bid, Alert, Category, CustomerActionLog
from config import Config
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)



@app.route('/')
def index():
    auctions = Auction.query.join(Item).all()
    return render_template('list_auctions.html', auctions=auctions)

# -------- Authentication --------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        user_type = request.form['user_type']

        user = User(username=username, email=email, password_hash=password, user_type=user_type)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['user_type'] = user.user_type
            flash('Logged in successfully.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'info')
    return redirect(url_for('index'))

# -------- Posting Auctions --------

@app.route('/post_item', methods=['GET', 'POST'])
def post_item():
    if 'user_id' not in session:
        flash('Login required.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        
        selected_category = request.form['category_id']

        # Handle if "other" is selected
        if selected_category == 'other':
            new_category_name = request.form['other_category']

            # Check if category already exists
            existing_category = Category.query.filter_by(name=new_category_name).first()
            if existing_category:
                category = existing_category
            else:
                category = Category(name=new_category_name)
                db.session.add(category)
                db.session.commit()
        else:
            # Existing standard category
            category = Category.query.filter_by(name=selected_category).first()
            if not category:
                flash('Category not found. Please contact admin.', 'danger')
                return redirect(url_for('post_item'))

        category_id = category.id

        start_price = float(request.form['start_price'])
        min_increment = float(request.form['min_increment'])
        min_price = float(request.form['min_price'])
        start_time = datetime.strptime(request.form['start_time'], "%Y-%m-%dT%H:%M")
        end_time = datetime.strptime(request.form['end_time'], "%Y-%m-%dT%H:%M")

        # Optional vehicle fields
        vehicle_make = request.form.get('vehicle_make')
        vehicle_model = request.form.get('vehicle_model')
        year = request.form.get('year')
        mileage = request.form.get('mileage')

        item = Item(
            title=title,
            description=description,
            category_id=category_id,
            seller_id=session['user_id'],
            vehicle_make=vehicle_make,
            vehicle_model=vehicle_model,
            year=int(year) if year else None,
            mileage=int(mileage) if mileage else None,
        )
        db.session.add(item)
        db.session.commit()

        auction = Auction(
            item_id=item.id,
            start_price=start_price,
            min_increment=min_increment,
            min_price=min_price,
            start_time=start_time,
            end_time=end_time,
            status='open'
        )
        db.session.add(auction)
        db.session.commit()

        flash('Item and Auction created!', 'success')
        return redirect(url_for('index'))

    # Only for GET request, load basic categories
    categories = Category.query.all()
    return render_template('post_item.html', categories=categories)
# -------- Auction Details and Bidding --------

@app.route('/auction/<int:auction_id>', methods=['GET', 'POST'])
def auction_detail(auction_id):
    auction = Auction.query.get_or_404(auction_id)
    item = auction.item
    bids = Bid.query.filter_by(auction_id=auction_id).order_by(Bid.bid_amount.desc()).all()

    if request.method == 'POST':
        if 'user_id' not in session:
            flash('Login required.', 'warning')
            return redirect(url_for('login'))

        bid_amount = float(request.form['bid_amount'])
        auto_max = request.form.get('auto_max')

        bid = Bid(
            auction_id=auction.id,
            user_id=session['user_id'],
            bid_amount=bid_amount,
            max_auto_bid=float(auto_max) if auto_max else None,
        )
        db.session.add(bid)
        db.session.commit()
        flash('Bid placed successfully.', 'success')
        return redirect(url_for('auction_detail', auction_id=auction_id))

    return render_template('auction_detail.html', auction=auction, item=item, bids=bids)




@app.route('/delete_auction/<int:auction_id>', methods=['POST'])
def delete_auction(auction_id):
    auction = Auction.query.get_or_404(auction_id)
    item = auction.item

    # Check if the logged in user is the seller
    if 'user_id' not in session or item.seller_id != session['user_id']:
        flash('You are not authorized to delete this auction.', 'danger')
        return redirect(url_for('index'))

    # Delete auction first
    db.session.delete(auction)
    db.session.commit()

    # Then delete item (optional if you want)
    db.session.delete(item)
    db.session.commit()

    flash('Auction deleted successfully.', 'success')
    return redirect(url_for('index'))

# -------- Alerts --------

@app.route('/set_alert', methods=['GET', 'POST'])
def set_alert():
    if 'user_id' not in session:
        flash('Login required.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        keyword = request.form['keyword']

        alert = Alert(user_id=session['user_id'], keyword=keyword)
        db.session.add(alert)
        db.session.commit()
        flash('Alert set successfully.', 'success')
        return redirect(url_for('index'))

    return render_template('set_alert.html')

# -------- Customer Staff Actions --------

@app.route('/reset_password/<int:user_id>', methods=['POST'])
def reset_password(user_id):
    if session.get('user_type') != 'rep':
        flash('Access Denied.', 'danger')
        return redirect(url_for('index'))

    user = User.query.get(user_id)
    if user:
        user.password_hash = generate_password_hash('default123')
        db.session.commit()

        action = CustomerActionLog(
            rep_id=session['user_id'],
            action_type='reset_password',
            action_time=datetime.utcnow(),
            target_user_id=user.id,
            details='Password reset to default123'
        )
        db.session.add(action)
        db.session.commit()

        flash('Password reset successfully.', 'success')
    else:
        flash('User not found.', 'danger')

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)