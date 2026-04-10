from flask import Flask, render_template, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv
import os, uuid

# ── Load .env file when running locally ──────────────────────────
load_dotenv()

# ─────────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────────
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.environ.get("SECRET_KEY", "landlink_secret")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Database connection — reads from .env locally, from ECS env vars on AWS ──
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "landlink_db")
DB_USER = os.environ.get("DB_USER", "landlink_user")
DB_PASS = os.environ.get("DB_PASSWORD", "Aman5423")
APP_PORT = os.environ.get("APP_PORT", "8080")

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ── Upload folder ──────────────────────────────────────────────
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ─────────────────────────────────────────────
# DATABASE MODELS  (one class = one table)
# ─────────────────────────────────────────────

class User(db.Model):
    __tablename__ = 'users'

    id         = db.Column(db.Integer,     primary_key=True)
    phone      = db.Column(db.String(15),  unique=True, nullable=False)
    name       = db.Column(db.String(100))
    email      = db.Column(db.String(120))
    password   = db.Column(db.String(200), nullable=False)
    purpose    = db.Column(db.String(10))
    created_at = db.Column(db.DateTime,   default=datetime.utcnow)

    lands      = db.relationship('Land',     backref='seller',   lazy=True)
    bookings   = db.relationship('Booking',  backref='buyer',    lazy=True, foreign_keys='Booking.buyer_id')
    wishlist   = db.relationship('Wishlist', backref='user',     lazy=True)
    preference = db.relationship('BuyerPref', backref='user',   uselist=False)


class Land(db.Model):
    __tablename__ = 'lands'

    id          = db.Column(db.Integer,    primary_key=True)
    seller_id   = db.Column(db.Integer,    db.ForeignKey('users.id'), nullable=False)
    title       = db.Column(db.String(200))
    location    = db.Column(db.String(200))
    address     = db.Column(db.Text)
    price       = db.Column(db.String(50))
    area        = db.Column(db.Float)
    land_type   = db.Column(db.String(50))
    legal_issue = db.Column(db.String(5),  default='No')
    image       = db.Column(db.String(300))
    lat         = db.Column(db.Float)
    lng         = db.Column(db.Float)
    is_active   = db.Column(db.Boolean,   default=True)
    created_at  = db.Column(db.DateTime,  default=datetime.utcnow)

    bookings    = db.relationship('Booking',  backref='land', lazy=True)
    wishlisted  = db.relationship('Wishlist', backref='land', lazy=True)


class Booking(db.Model):
    __tablename__ = 'bookings'

    id             = db.Column(db.Integer,   primary_key=True)
    ref_number     = db.Column(db.String(30), unique=True, nullable=False)
    buyer_id       = db.Column(db.Integer,   db.ForeignKey('users.id'), nullable=False)
    land_id        = db.Column(db.Integer,   db.ForeignKey('lands.id'), nullable=False)
    payment_method = db.Column(db.String(30))
    amount_paid    = db.Column(db.String(50))
    status         = db.Column(db.String(30), default='token_paid')
    created_at     = db.Column(db.DateTime,  default=datetime.utcnow)


class Wishlist(db.Model):
    __tablename__ = 'wishlist'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    land_id    = db.Column(db.Integer, db.ForeignKey('lands.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class BuyerPref(db.Model):
    __tablename__ = 'buyer_preferences'

    id          = db.Column(db.Integer,    primary_key=True)
    user_id     = db.Column(db.Integer,    db.ForeignKey('users.id'), nullable=False)
    location    = db.Column(db.String(200))
    budget      = db.Column(db.String(50))
    land_type   = db.Column(db.String(50))
    min_area    = db.Column(db.Float)
    max_area    = db.Column(db.Float)
    road_access = db.Column(db.String(5))
    purpose     = db.Column(db.String(50))


class PredictorWaitlist(db.Model):
    __tablename__ = 'predictor_waitlist'

    id         = db.Column(db.Integer,    primary_key=True)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime,  default=datetime.utcnow)


# ─────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────
def land_to_dict(land):
    return {
        "id":          land.id,
        "title":       land.title,
        "location":    land.location,
        "address":     land.address,
        "price":       land.price,
        "area":        land.area,
        "land_type":   land.land_type,
        "legal_issue": land.legal_issue,
        "image":       land.image,
        "lat":         land.lat,
        "lng":         land.lng,
    }


# ─────────────────────────────────────────────
# LOGIN / SIGNUP / LOGOUT
# ─────────────────────────────────────────────

@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/login_user", methods=["POST"])
def login_user():
    phone    = request.form.get("phone", "").strip()
    password = request.form.get("password", "")
    purpose  = request.form.get("purpose", "")

    user = User.query.filter_by(phone=phone, purpose=purpose).first()

    if not user:
        return render_template("login.html", error="❌ No account found with this number.")
    if user.password != password:
        return render_template("login.html", error="❌ Incorrect password.")

    session["user"]    = phone
    session["purpose"] = purpose
    return redirect("/buyer" if purpose == "buy" else "/seller")


@app.route("/signup", methods=["POST"])
def signup():
    name     = request.form.get("name")
    email    = request.form.get("email")
    phone    = request.form.get("phone", "").strip()
    password = request.form.get("password", "")
    confirm  = request.form.get("confirm", "")
    purpose  = request.form.get("purpose", "")

    if password != confirm:
        return render_template("login.html", error="❌ Passwords do not match.")

    if User.query.filter_by(phone=phone).first():
        return render_template("login.html", error="❌ User already exists with this number.")

    user = User(phone=phone, name=name, email=email, password=password, purpose=purpose)
    db.session.add(user)
    db.session.commit()

    session["user"]    = phone
    session["purpose"] = purpose
    return redirect("/buyer" if purpose == "buy" else "/seller")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ─────────────────────────────────────────────
# HOME PAGE
# ─────────────────────────────────────────────

@app.route("/")
def home():
    lands_orm = Land.query.filter_by(is_active=True).order_by(Land.created_at.desc()).all()
    lands     = [land_to_dict(l) for l in lands_orm]

    seller_land  = None
    token_buyers = []

    if session.get("purpose") == "sell":
        phone = session.get("user")
        user  = User.query.filter_by(phone=phone).first()

        if user:
            sl = Land.query.filter_by(seller_id=user.id, is_active=True).first()
            if sl:
                seller_land = land_to_dict(sl)
                bkgs = Booking.query.filter_by(land_id=sl.id).all()
                for b in bkgs:
                    buyer = User.query.get(b.buyer_id)
                    token_buyers.append({
                        "phone":      buyer.phone if buyer else "—",
                        "name":       buyer.name  if buyer else "Unknown",
                        "ref_number": b.ref_number,
                        "timestamp":  b.created_at.strftime("%Y-%m-%d %H:%M") if b.created_at else "",
                        "amount":     b.amount_paid,
                        "status":     b.status,
                    })

    return render_template("home_page.html",
                           lands=lands,
                           seller_land=seller_land,
                           token_buyers=token_buyers)


# ─────────────────────────────────────────────
# BUYER / SELLER PAGES
# ─────────────────────────────────────────────

@app.route("/buyer")
def buyer_page():
    if "user" not in session:
        return redirect("/login")
    return render_template("buyer_register.html")


@app.route("/seller")
def seller_page():
    if "user" not in session:
        return redirect("/login")
    return render_template("seller_register.html")


# ─────────────────────────────────────────────
# BUYER PREFERENCE
# ─────────────────────────────────────────────

@app.route("/register_buyer", methods=["POST"])
def register_buyer():
    if "user" not in session:
        return redirect("/login")

    phone = session["user"]
    user  = User.query.filter_by(phone=phone).first()

    pref = BuyerPref.query.filter_by(user_id=user.id).first()
    if not pref:
        pref = BuyerPref(user_id=user.id)
        db.session.add(pref)

    pref.location    = request.form.get("location")
    pref.budget      = request.form.get("budget")
    pref.land_type   = request.form.get("land_type")
    pref.min_area    = request.form.get("min_area") or None
    pref.max_area    = request.form.get("max_area") or None
    pref.road_access = request.form.get("road_access")
    pref.purpose     = request.form.get("purpose")

    db.session.commit()
    return redirect("/")


# ─────────────────────────────────────────────
# SELLER REGISTRATION
# ─────────────────────────────────────────────

@app.route("/register_seller", methods=["POST"])
def register_seller():
    if "user" not in session:
        return redirect("/login")

    phone = session["user"]
    user  = User.query.filter_by(phone=phone).first()

    image      = request.files.get("image")
    image_path = ""
    if image and image.filename:
        filename   = f"{phone}_{image.filename}"
        image.save(os.path.join(UPLOAD_FOLDER, filename))
        image_path = f"uploads/{filename}"

    lat = request.form.get("lat")
    lng = request.form.get("lng")

    existing = Land.query.filter_by(seller_id=user.id).first()

    if existing:
        existing.title       = request.form.get("title")
        existing.location    = request.form.get("location")
        existing.address     = request.form.get("address")
        existing.price       = request.form.get("price")
        existing.area        = request.form.get("area") or None
        existing.land_type   = request.form.get("land_type")
        existing.legal_issue = request.form.get("legal_issue", "No")
        existing.lat         = float(lat) if lat else None
        existing.lng         = float(lng) if lng else None
        if image_path:
            existing.image = image_path
    else:
        land = Land(
            seller_id   = user.id,
            title       = request.form.get("title"),
            location    = request.form.get("location"),
            address     = request.form.get("address"),
            price       = request.form.get("price"),
            area        = request.form.get("area") or None,
            land_type   = request.form.get("land_type"),
            legal_issue = request.form.get("legal_issue", "No"),
            image       = image_path,
            lat         = float(lat) if lat else None,
            lng         = float(lng) if lng else None,
        )
        db.session.add(land)

    db.session.commit()
    return redirect("/")


# ─────────────────────────────────────────────
# LAND DETAIL
# ─────────────────────────────────────────────

@app.route("/land/<int:land_id>")
def land_detail(land_id):
    land = Land.query.get(land_id)
    if not land:
        return render_template("404.html"), 404
    return render_template("land_details.html", land=land_to_dict(land), predicted_price=None)


# ─────────────────────────────────────────────
# AI PRICE PREDICTOR
# ─────────────────────────────────────────────

@app.route("/predict_price", methods=["POST"])
def predict_price():
    try:
        area      = float(request.form.get("area", 0))
        distance  = float(request.form.get("distance", 10))
        road      = int(request.form.get("road", 1))
        land_type = request.form.get("land_type_pred", "Agriculture")
        land_id   = int(request.form.get("land_id", 0))

        base_rates  = {"Agriculture": 50, "Residential": 180, "Commercial": 320}
        base        = base_rates.get(land_type, 80)
        dist_factor = max(0.5, 1 - (distance * 0.02))
        road_bonus  = 1.12 if road == 1 else 1.0
        estimated   = area * base * dist_factor * road_bonus

        if estimated >= 1_00_00_000:
            predicted_price = f"{estimated/1_00_00_000:.2f} Crore"
        elif estimated >= 1_00_000:
            predicted_price = f"{estimated/1_00_000:.1f} Lakh"
        else:
            predicted_price = f"{int(estimated):,}"
    except:
        predicted_price = "Unable to predict — check inputs"
        land_id = 0

    land = Land.query.get(land_id)
    land_dict = land_to_dict(land) if land else {
        "id": land_id, "title": "Land", "location": "",
        "price": "0", "image": "", "lat": None, "lng": None
    }
    return render_template("land_details.html", land=land_dict, predicted_price=predicted_price)


# ─────────────────────────────────────────────
# SEARCH
# ─────────────────────────────────────────────

@app.route("/search")
def search():
    location  = request.args.get("location", "").strip()
    min_price = request.args.get("min_price", "")
    max_price = request.args.get("max_price", "")
    land_type = request.args.get("land_type", "")

    query = Land.query.filter_by(is_active=True)

    if location:
        query = query.filter(Land.location.ilike(f"%{location}%"))
    if land_type:
        query = query.filter_by(land_type=land_type)

    results = query.all()

    def parse_price(p):
        try: return float(str(p).replace(",", "").replace(" ", ""))
        except: return 0

    if min_price:
        results = [l for l in results if parse_price(l.price) >= float(min_price)]
    if max_price:
        results = [l for l in results if parse_price(l.price) <= float(max_price)]

    return render_template("search_results.html", lands=[land_to_dict(l) for l in results])


# ─────────────────────────────────────────────
# MAP SEARCH
# ─────────────────────────────────────────────

@app.route("/map-search")
def map_search():
    lands = Land.query.filter_by(is_active=True).all()
    return render_template("map_search.html", lands=[land_to_dict(l) for l in lands])


# ─────────────────────────────────────────────
# SELECT LAND
# ─────────────────────────────────────────────

@app.route("/select_land")
def select_land():
    return render_template("select_land.html")


# ─────────────────────────────────────────────
# PROFILE
# ─────────────────────────────────────────────

@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect("/login")
    user = User.query.filter_by(phone=session["user"]).first()
    return render_template("profile.html", user={
        "name": user.name, "email": user.email,
        "phone": user.phone, "purpose": user.purpose
    })


@app.route("/edit_profile")
def edit_profile():
    if "user" not in session:
        return redirect("/login")
    user = User.query.filter_by(phone=session["user"]).first()
    return render_template("edit_profile.html", user={
        "name": user.name, "email": user.email,
        "phone": user.phone, "password": user.password
    })


@app.route("/save_profile", methods=["POST"])
def save_profile():
    if "user" not in session:
        return redirect("/login")

    user       = User.query.filter_by(phone=session["user"]).first()
    user.name  = request.form.get("name")
    user.email = request.form.get("email")
    new_pw     = request.form.get("password")
    if new_pw:
        user.password = new_pw
    db.session.commit()
    return redirect("/profile")


# ─────────────────────────────────────────────
# SAVED / WISHLIST
# ─────────────────────────────────────────────

@app.route("/saved")
def saved_page():
    return render_template("saved.html")


@app.route("/save_wishlist", methods=["POST"])
def save_wishlist():
    if "user" not in session:
        return {"error": "Not logged in"}, 401

    user = User.query.filter_by(phone=session["user"]).first()
    data = request.get_json()
    ids  = data.get("ids", [])

    Wishlist.query.filter_by(user_id=user.id).delete()

    for land_id in ids:
        land = Land.query.get(int(land_id))
        if land:
            db.session.add(Wishlist(user_id=user.id, land_id=land.id))

    db.session.commit()
    return {"success": True, "saved": len(ids)}, 200


@app.route("/api/saved_count")
def saved_count():
    if "user" not in session:
        return {"count": 0}
    user  = User.query.filter_by(phone=session["user"]).first()
    count = Wishlist.query.filter_by(user_id=user.id).count() if user else 0
    return {"count": count}


# ─────────────────────────────────────────────
# PAYMENT / BOOKINGS
# ─────────────────────────────────────────────

@app.route("/process_payment", methods=["POST"])
def process_payment():
    if "user" not in session:
        return {"success": False, "error": "Please login to continue"}, 401

    user           = User.query.filter_by(phone=session["user"]).first()
    data           = request.get_json()
    land_ids       = data.get("land_ids", [])
    payment_method = data.get("payment_method", "upi")
    amount         = data.get("amount", "₹0")
    ref_number     = "LL-" + uuid.uuid4().hex[:8].upper()

    for lid in land_ids:
        try:
            land = Land.query.get(int(lid))
            if land:
                booking = Booking(
                    ref_number     = f"{ref_number}-{lid}",
                    buyer_id       = user.id,
                    land_id        = land.id,
                    payment_method = payment_method,
                    amount_paid    = amount,
                    status         = "token_paid"
                )
                db.session.add(booking)
        except Exception as e:
            print(f"Booking error: {e}")

    db.session.commit()
    return {"success": True, "ref_number": ref_number,
            "message": "Token payment recorded successfully"}, 200


@app.route("/my_bookings")
def my_bookings():
    if "user" not in session:
        return redirect("/login")

    phone   = session["user"]
    purpose = session.get("purpose", "buy")
    user    = User.query.filter_by(phone=phone).first()
    bookings = []

    if purpose == "buy":
        raw = Booking.query.filter_by(buyer_id=user.id)\
                           .order_by(Booking.created_at.desc()).all()
        for b in raw:
            land = Land.query.get(b.land_id)
            bookings.append({
                "ref_number":     b.ref_number,
                "timestamp":      b.created_at.strftime("%Y-%m-%d %H:%M") if b.created_at else "",
                "payment_method": b.payment_method,
                "amount_paid":    b.amount_paid,
                "status":         b.status,
                "lands":          [land_to_dict(land)] if land else []
            })
    else:
        sl = Land.query.filter_by(seller_id=user.id).first()
        if sl:
            raw = Booking.query.filter_by(land_id=sl.id)\
                               .order_by(Booking.created_at.desc()).all()
            for b in raw:
                buyer = User.query.get(b.buyer_id)
                bookings.append({
                    "ref_number":     b.ref_number,
                    "timestamp":      b.created_at.strftime("%Y-%m-%d %H:%M") if b.created_at else "",
                    "payment_method": b.payment_method,
                    "amount_paid":    b.amount_paid,
                    "status":         b.status,
                    "buyer_phone":    buyer.phone if buyer else "—",
                    "buyer_name":     buyer.name  if buyer else "Unknown",
                    "lands":          [land_to_dict(sl)]
                })

    return render_template("my_bookings.html", bookings=bookings)


@app.route("/update_booking_status", methods=["POST"])
def update_booking_status():
    if "user" not in session:
        return {"success": False, "error": "Not logged in"}, 401

    data       = request.get_json()
    ref_number = data.get("ref_number")
    new_status = data.get("status")

    VALID = ["token_paid", "docs_verified", "site_visit", "registered", "cancelled"]
    if new_status not in VALID:
        return {"success": False, "error": "Invalid status"}, 400

    booking = Booking.query.filter_by(ref_number=ref_number).first()
    if not booking:
        return {"success": False, "error": "Booking not found"}, 404

    booking.status = new_status
    db.session.commit()
    return {"success": True, "ref_number": ref_number, "new_status": new_status}


# ─────────────────────────────────────────────
# AI PREDICTOR WAITLIST
# ─────────────────────────────────────────────

@app.route("/notify_predictor", methods=["POST"])
def notify_predictor():
    data  = request.get_json()
    email = data.get("email", "").strip()

    if not email or "@" not in email:
        return {"success": False, "error": "Invalid email"}, 400

    if not PredictorWaitlist.query.filter_by(email=email).first():
        db.session.add(PredictorWaitlist(email=email))
        db.session.commit()

    return {"success": True, "message": "Added to waitlist"}, 200


# ─────────────────────────────────────────────
# CREATE TABLES + RUN
# ─────────────────────────────────────────────

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=PORT, debug=os.environ.get("FLASK_ENV") == "development")