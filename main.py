from flask import Flask, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap
from forms import ContactForm, SignupForm, LoginForm
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from collections import Counter, OrderedDict
import stripe
from datetime import datetime
import os

app = Flask(__name__)

#CSRF
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

#Bootstrap
Bootstrap(app)

#Login Manager
login_manager = LoginManager()
login_manager.init_app(app)

#Database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#stripe
stripe.api_key = os.environ.get('stripe.api_key')
#myhost
YOUR_DOMAIN = os.environ.get('YOUR_DOMAIN')

class User(db.Model,UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer,primary_key=True)
    email = db.Column(db.String(100),unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    orders = relationship('Order',back_populates="user")
    cart = relationship('Cart',back_populates='user')


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100),unique=True,nullable=False)
    price = db.Column(db.Float,nullable=False)
    img_url = db.Column(db.String(300))
    stripe_id = db.Column(db.String(100),unique=True,nullable=False)
    cart = relationship('Cart', back_populates='product')
    order = relationship('Order',back_populates="product")

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user = relationship('User',back_populates="orders")
    time = db.Column(db.String(100),nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))
    product = relationship('Product',back_populates="order")
    quantity = db.Column(db.Integer, nullable=False)

class Cart(db.Model):
    __tablename__ = 'carts'
    id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user = relationship('User',back_populates="cart")
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))
    product = relationship('Product',back_populates="cart")

db.create_all()

#user_id (if the success page or cancel page log out it will login again)
current_user_id = None

@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)

@app.route('/')
def home():
    # db.session.add(Product(name='ps4',price=499,img_url='https://m.media-amazon.com/images/I/61OL2zIliML._AC_UY327_FMwebp_QL65_.jpg',stripe_id='price_1JMVnsCSW8vxpkyLICIPGyqC'))
    # db.session.add(Product(name='xbox one',price=384,img_url='https://m.media-amazon.com/images/I/612wQCy8x+L._AC_UY327_FMwebp_QL65_.jpg',stripe_id='price_1JMVmyCSW8vxpkyLKTGBhXcq'))
    # db.session.add(Product(name='ps5',price=1099,img_url='https://m.media-amazon.com/images/I/31q4oLyLneL._AC_UY327_FMwebp_QL65_.jpg',stripe_id='price_1JMVllCSW8vxpkyLowWDobdv'))
    # db.session.add(Product(name='switch',price=119,img_url='https://m.media-amazon.com/images/I/61CqIvtcrML._AC_UY327_FMwebp_QL65_.jpg',stripe_id='price_1JMVjTCSW8vxpkyLbiZ8jgcN'))
    # db.session.commit()
    return render_template('index.html')

@app.route('/product')
def product():
    products = db.session.query(Product).all()
    return render_template('product.html',products=products)

@app.route('/contact',methods=['GET','POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        return redirect(url_for('home'))
    return render_template('contact.html',form=form)

@app.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        exist_user = db.session.query(User).filter_by(email=email).first()
        if exist_user == None:
            flash('That email does not exist, please try again')
        else:
            if check_password_hash(exist_user.password,password):
                login_user(exist_user)
                return redirect(url_for('home'))
            else:
                flash('Password incorrect, please try again')
    return render_template('login.html',form=form)

@app.route('/signup',methods=['GET','POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        name = form.name.data
        exist_user = db.session.query(User).filter_by(email=email).first()
        if exist_user == None:
            password = generate_password_hash(password,method='pbkdf2:sha256',salt_length=8)
            new_user = User(email=email,password=password,name=name)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('home'))
        else:
            flash("You've already signed up with that email, log in instead.")
            return redirect(url_for('login'))
    return render_template('signup.html',form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/add_to_cart')
def add_to_cart():
    if not current_user.is_authenticated:
        flash('Please login first')
        return redirect(url_for('login'))

    product_id = request.args.get('id')
    cart = Cart(user_id=current_user.id,product_id=product_id)
    db.session.add(cart)
    db.session.commit()
    return redirect(url_for('product'))

@app.route('/append_item')
def append_item():
    product_id = request.args.get('id')
    db.session.add(Cart(user_id=current_user.id,product_id=product_id))
    db.session.commit()
    return redirect(url_for('mycart'))

@app.route('/reduce_item')
def reduce_item():
    product_id = request.args.get('id')
    cart = db.session.query(Cart).filter_by(user_id=current_user.id,product_id=product_id).first()
    db.session.delete(cart)
    db.session.commit()
    return redirect(url_for('mycart'))

@app.route('/delete_item')
def delete_item():
    product_id = request.args.get('id')
    cart = db.session.query(Cart).filter_by(user_id=current_user.id,product_id=product_id).all()
    for i in cart:
        db.session.delete(i)
    db.session.commit()
    return redirect(url_for('mycart'))

@app.route('/mycart')
def mycart():
    if not current_user.is_authenticated:
        flash('Please login first')
        return redirect(url_for('login'))

    cart = db.session.query(Cart).filter_by(user_id=current_user.id).all()
    products = []
    for i in cart:
        products.append(i.product_id)

    items = []
    total = 0
    for i in dict(Counter(products)).items():
        item = db.session.query(Product).filter_by(id=i[0]).first()
        quantity = i[1]
        items.append((item,quantity))
        total = total + item.price * quantity
    return render_template('mycart.html',items=items,total=total)

@app.route('/checkout', methods=['POST'])
def checkout():
    if not current_user.is_authenticated:
        flash('Please login first')
        return redirect(url_for('login'))

    cart = db.session.query(Cart).filter_by(user_id=current_user.id).all()
    products = []
    for i in cart:
        products.append(i.product_id)

    line_items = []
    for i in dict(Counter(products)).items():
        price = db.session.query(Product).filter_by(id=i[0]).first().stripe_id
        quantity = i[1]
        line_items.append({'price':price,'quantity':quantity})

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=[
                'card',
            ],
            line_items=line_items,
            mode = 'payment',
            success_url = YOUR_DOMAIN + '/success',
            cancel_url = YOUR_DOMAIN + '/cancel',
        )
    except Exception as e:
        return str(e)

    #if the success page or cancel page log out it will login again
    global current_user_id
    current_user_id = current_user.id

    return redirect(checkout_session.url, code=303)

@app.route('/success')
def success():
    #if the success page log out it will login again
    if not current_user.is_authenticated:
        present_user = db.session.query(User).filter_by(id=current_user_id).first()
        login_user(present_user)

    cart = db.session.query(Cart).filter_by(user_id=current_user.id).all()
    products = []
    for i in cart:
        products.append(i.product_id)
        db.session.delete(i)

    for i in dict(Counter(products)).items():
        user_id = current_user.id
        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        product_id = i[0]
        quantity = i[1]
        db.session.add(Order(user_id=user_id,time=time,product_id=product_id,quantity=quantity))

    db.session.commit()
    return render_template('success.html')

@app.route('/cancel')
def cancel():
    #if the cancel page log out it will login again
    if not current_user.is_authenticated:
        present_user = db.session.query(User).filter_by(id=current_user_id).first()
        login_user(present_user)
    return render_template('cancel.html')


@app.route('/orders')
@login_required
def orders():
    if not current_user.is_authenticated:
        flash('Please login first')
        return redirect(url_for('login'))

    orders = db.session.query(Order).filter_by(user_id=current_user.id).all()
    times = []
    for order in orders:
        time = order.time
        times.append(time)
    times = list(OrderedDict.fromkeys(times))
    return render_template('orders.html',times=times)

@app.route('/detail')
def detail():
    time = request.args.get('time')
    order = db.session.query(Order).filter_by(user_id=current_user.id,time=time).all()
    items = []
    total = 0
    for i in order:
        item = db.session.query(Product).filter_by(id=i.product_id).first()
        quantity = i.quantity
        items.append((item,quantity))
        total = total + item.price * quantity
    return render_template('detail.html',items=items,total=total)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)