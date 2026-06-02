from flask import Flask, render_template, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv
import os, uuid, time, logging, random, string, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from src.landlink import logger



load_dotenv()


# ── Database connection — reads from .env locally, from ECS env vars on AWS ──
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "landlink_db")
DB_USER = os.environ.get("DB_USER", "landlink_user")
DB_PASS = os.environ.get("DB_PASSWORD", "Aman5423")
APP_PORT = os.environ.get("APP_PORT", "8080")

# ─────────────────────────────────────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────────────────────────────────────
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.environ.get("SECRET_KEY", "landlink_secret_change_me")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///landlink.db")

# app.config['SQLALCHEMY_DATABASE_URI']        = DATABASE_URL

if os.environ.get("FLASK_ENV") == "development":
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///landlink.db"
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    )
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}


# ─────────────────────────────────────────────────────────────────────────
# EMAIL CONFIG  (set these in your .env or Render environment variables)
# ─────────────────────────────────────────────────────────────────────────
SMTP_HOST     = os.environ.get("SMTP_HOST",     "smtp.gmail.com")
SMTP_PORT     = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER     = os.environ.get("SMTP_USER")  
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")   
EMAIL_FROM    = os.environ.get("EMAIL_FROM")


# ─────────────────────────────────────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────────────────────────────────────

class User(db.Model):
    __tablename__ = 'users'
    id         = db.Column(db.Integer,     primary_key=True)
    phone      = db.Column(db.String(15),  unique=True, nullable=False, index=True)
    name       = db.Column(db.String(100))
    email      = db.Column(db.String(120))
    password   = db.Column(db.String(200), nullable=False)
    purpose    = db.Column(db.String(10))
    created_at = db.Column(db.DateTime,    default=datetime.utcnow)

    lands      = db.relationship('Land',      backref='seller', lazy=True)
    bookings   = db.relationship('Booking',   backref='buyer',  lazy=True, foreign_keys='Booking.buyer_id')
    wishlist   = db.relationship('Wishlist',  backref='user',   lazy=True)
    preference = db.relationship('BuyerPref', backref='user',   uselist=False)


class Land(db.Model):
    __tablename__ = 'lands'
    id          = db.Column(db.Integer,    primary_key=True)
    seller_id   = db.Column(db.Integer,    db.ForeignKey('users.id'), nullable=False, index=True)
    title       = db.Column(db.String(200))
    location    = db.Column(db.String(200), index=True)
    address     = db.Column(db.Text)
    price       = db.Column(db.String(50))
    area        = db.Column(db.Float)
    land_type   = db.Column(db.String(50))
    legal_issue = db.Column(db.String(5),  default='No')
    image       = db.Column(db.String(300))
    lat         = db.Column(db.Float)
    lng         = db.Column(db.Float)
    is_active   = db.Column(db.Boolean,    default=True)
    created_at  = db.Column(db.DateTime,   default=datetime.utcnow)

    bookings    = db.relationship('Booking',  backref='land', lazy=True)
    wishlisted  = db.relationship('Wishlist', backref='land', lazy=True)


class Booking(db.Model):
    __tablename__ = 'bookings'
    id             = db.Column(db.Integer,    primary_key=True)
    ref_number     = db.Column(db.String(30), unique=True, nullable=False)
    buyer_id       = db.Column(db.Integer,    db.ForeignKey('users.id'), nullable=False)
    land_id        = db.Column(db.Integer,    db.ForeignKey('lands.id'), nullable=False)
    payment_method = db.Column(db.String(30))
    amount_paid    = db.Column(db.String(50))
    status         = db.Column(db.String(30), default='token_paid')
    created_at     = db.Column(db.DateTime,   default=datetime.utcnow)


class Wishlist(db.Model):
    __tablename__ = 'wishlist'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    land_id    = db.Column(db.Integer, db.ForeignKey('lands.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class BuyerPref(db.Model):
    __tablename__ = 'buyer_preferences'
    id          = db.Column(db.Integer,    primary_key=True)
    user_id     = db.Column(db.Integer,    db.ForeignKey('users.id'), nullable=False, unique=True)
    location    = db.Column(db.String(200))
    budget      = db.Column(db.String(50))
    land_type   = db.Column(db.String(50))
    min_area    = db.Column(db.Float)
    max_area    = db.Column(db.Float)
    road_access = db.Column(db.String(5))
    purpose     = db.Column(db.String(50))


class PredictorWaitlist(db.Model):
    __tablename__ = 'predictor_waitlist'
    id         = db.Column(db.Integer,     primary_key=True)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime,    default=datetime.utcnow)


# ─────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────

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


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_password(length=8):
    """Generate a random 8-character alphanumeric password."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


def send_welcome_email(to_email, name, phone, password, purpose):
    """
    Send a welcome email with the auto-generated password.
    Returns True on success, False on failure.
    Requires SMTP_USER and SMTP_PASSWORD in environment.
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured — skipping email.")
        return False

    purpose_label = "Buy Land 🏡" if purpose == "buy" else "Sell Land 🌾"

    html_body = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:32px 0;">
    <tr>
      <td align="center">
        <table width="560" cellpadding="0" cellspacing="0"
               style="background:#ffffff;border-radius:20px;overflow:hidden;
                      box-shadow:0 4px 24px rgba(0,0,0,0.08);max-width:560px;width:100%;">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#0d3320,#1a6b3c);
                       padding:32px 40px;text-align:center;">
              <div style="display:inline-flex;align-items:center;gap:10px;">
                <div style="width:44px;height:44px;background:rgba(255,255,255,0.15);
                            border-radius:12px;display:inline-block;
                            line-height:44px;text-align:center;font-size:22px;">🌿</div>
                <span style="font-family:Georgia,serif;font-size:1.8rem;
                             font-weight:700;color:#ffffff;letter-spacing:-0.01em;">
                  Land<span style="color:#34d068;">Link</span>
                </span>
              </div>
              <p style="color:rgba(255,255,255,0.7);margin:10px 0 0;font-size:0.9rem;">
                India's Smartest Land Marketplace
              </p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:36px 40px;">
              <h2 style="margin:0 0 8px;font-family:Georgia,serif;
                         font-size:1.5rem;color:#111a14;">
                Welcome aboard, {name}! 🎉
              </h2>
              <p style="color:#6b7280;font-size:0.95rem;margin:0 0 24px;line-height:1.6;">
                Your LandLink account has been created successfully.
                You're registered as: <strong>{purpose_label}</strong>
              </p>

              <!-- Credentials Card -->
              <div style="background:#f0faf4;border:1.5px solid #c6e8d4;
                          border-radius:14px;padding:20px 24px;margin-bottom:24px;">
                <p style="margin:0 0 4px;font-size:0.78rem;font-weight:700;
                           color:#1a6b3c;text-transform:uppercase;letter-spacing:0.08em;">
                  Your Login Credentials
                </p>
                <table cellpadding="0" cellspacing="0" width="100%" style="margin-top:12px;">
                  <tr>
                    <td style="padding:6px 0;font-size:0.88rem;color:#6b7280;width:100px;">
                      📱 Mobile
                    </td>
                    <td style="padding:6px 0;font-size:0.95rem;
                               font-weight:600;color:#111a14;">
                      {phone}
                    </td>
                  </tr>
                  <tr>
                    <td style="padding:6px 0;font-size:0.88rem;color:#6b7280;">
                      🔑 Password
                    </td>
                    <td style="padding:6px 0;">
                      <span style="font-family:monospace;font-size:1.1rem;
                                   font-weight:700;color:#1a6b3c;
                                   background:#e8f7ee;padding:4px 12px;
                                   border-radius:7px;letter-spacing:0.1em;">
                        {password}
                      </span>
                    </td>
                  </tr>
                  <tr>
                    <td style="padding:6px 0;font-size:0.88rem;color:#6b7280;">
                      🎯 Purpose
                    </td>
                    <td style="padding:6px 0;font-size:0.88rem;
                               font-weight:600;color:#111a14;">
                      {purpose_label}
                    </td>
                  </tr>
                </table>
              </div>

              <!-- CTA Button -->
              <div style="text-align:center;margin-bottom:24px;">
                <a href="https://landlink.onrender.com/login"
                   style="display:inline-block;background:#1a6b3c;color:#ffffff;
                          text-decoration:none;padding:14px 36px;border-radius:12px;
                          font-size:1rem;font-weight:700;">
                  Login to LandLink →
                </a>
              </div>

              <!-- Security Note -->
              <div style="background:#fff8ed;border:1px solid #fcd97c;
                          border-radius:10px;padding:14px 18px;margin-bottom:20px;">
                <p style="margin:0;font-size:0.83rem;color:#92400e;line-height:1.6;">
                  ⚠️ <strong>Important:</strong> Please change your password
                  after logging in. Go to <em>Profile → Edit Profile</em>.
                </p>
              </div>

              <p style="color:#9ca3af;font-size:0.82rem;line-height:1.6;margin:0;">
                If you did not create this account, please ignore this email
                or contact our support team immediately.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#f9f9f7;border-top:1px solid #eee;
                       padding:18px 40px;text-align:center;">
              <p style="margin:0;font-size:0.78rem;color:#aaa;">
                © 2026 LandLink · Made with 🌿 for India
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

    plain_body = f"""
Welcome to LandLink, {name}!

Your account has been created.

Login Credentials:
  Mobile:   {phone}
  Password: {password}
  Purpose:  {purpose_label}

Login at: https://landlink.onrender.com/login

Please change your password after logging in.

© 2026 LandLink
"""

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🌿 Welcome to LandLink, {name}! Your login credentials"
        msg["From"]    = f"LandLink <{EMAIL_FROM}>"
        msg["To"]      = to_email

        msg.attach(MIMEText(plain_body, "plain"))
        msg.attach(MIMEText(html_body,  "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, [to_email], msg.as_string())

        logger.info(f"Welcome email sent to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


def init_db_with_retry(retries=5, delay=4):
    for attempt in range(1, retries + 1):
        try:
            db.create_all()
            logger.info("✅ Database tables ready.")
            return
        except Exception as e:
            logger.warning(f"DB not ready (attempt {attempt}/{retries}): {e}")
            if attempt < retries:
                time.sleep(delay)
    logger.error("❌ Could not connect to the database after retries.")
    raise SystemExit(1)


# ─────────────────────────────────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    try:
        db.session.execute(db.text("SELECT 1"))
        return jsonify({"status": "ok", "db": "connected"}), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────────────────

@app.route("/login")
def login_page():
    show_register = request.args.get("register") == "1"
    return render_template("login.html", show_register=show_register)


@app.route("/login_user", methods=["POST"])
def login_user():
    phone    = request.form.get("phone", "").strip()
    password = request.form.get("password", "")
    purpose  = request.form.get("purpose", "")
    try:
        user = User.query.filter_by(phone=phone, purpose=purpose).first()
    except Exception as e:
        logger.error(f"Login DB error: {e}")
        return render_template("login.html", error="⚠️ Database error. Please try again.")
    if not user:
        return render_template("login.html", error="❌ No account found with this number.")
    if user.password != password:
        return render_template("login.html", error="❌ Incorrect password.")
    session["user"]    = phone
    session["purpose"] = purpose
    return redirect("/buyer" if purpose == "buy" else "/seller")


@app.route("/signup", methods=["POST"])
def signup():
    """
    New registration flow:
    1. Collect: purpose, full name, email, mobile number
    2. Generate a random 8-character password
    3. Create the account
    4. Send the password to the user's email
    5. Redirect to login page with a success message
    """
    name    = request.form.get("name", "").strip()
    email   = request.form.get("email", "").strip().lower()
    phone   = request.form.get("phone", "").strip()
    purpose = request.form.get("purpose", "")

    # ── Validation ──
    if not name:
        return render_template("login.html",
                               error="❌ Please enter your full name.",
                               show_register=True)
    if not email or "@" not in email:
        return render_template("login.html",
                               error="❌ Please enter a valid email address.",
                               show_register=True)
    if not phone or len(phone) < 10:
        return render_template("login.html",
                               error="❌ Please enter a valid 10-digit mobile number.",
                               show_register=True)
    if not purpose:
        return render_template("login.html",
                               error="❌ Please select your purpose (Buy or Sell).",
                               show_register=True)

    try:
        # Check duplicates
        if User.query.filter_by(phone=phone).first():
            return render_template("login.html",
                                   error="❌ An account already exists with this mobile number.",
                                   show_register=True)
        if User.query.filter_by(email=email).first():
            return render_template("login.html",
                                   error="❌ An account already exists with this email.",
                                   show_register=True)

        # Generate password
        password = generate_password(8)

        # Create user
        user = User(
            phone=phone,
            name=name,
            email=email,
            password=password,
            purpose=purpose
        )
        db.session.add(user)
        db.session.commit()
        logger.info(f"New user registered: {phone} ({purpose})")

        # Send email (non-blocking — don't fail registration if email fails)
        email_sent = send_welcome_email(email, name, phone, password, purpose)

        if email_sent:
            success_msg = (
                f"✅ Account created! Check your email ({email}) for your login password. "
                f"Use your mobile number and the password we sent you."
            )
        else:
            # Email failed — show the password directly on screen as fallback
            success_msg = (
                f"✅ Account created! We couldn't send the email right now. "
                f"Your temporary password is: {password} — please save it!"
            )

        return render_template("login.html", success=success_msg)

    except Exception as e:
        db.session.rollback()
        logger.error(f"Signup error: {e}")
        return render_template("login.html",
                               error="⚠️ Could not create account. Please try again.",
                               show_register=True)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ─────────────────────────────────────────────────────────────────────────
# HOME
# ─────────────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    try:
        lands_orm = Land.query.filter_by(is_active=True).order_by(Land.created_at.desc()).all()
        lands     = [land_to_dict(l) for l in lands_orm]
    except Exception as e:
        logger.error(f"Home page error: {e}")
        lands = []

    seller_land  = None
    token_buyers = []
    if session.get("purpose") == "sell":
        try:
            user = User.query.filter_by(phone=session.get("user")).first()
            if user:
                sl = Land.query.filter_by(seller_id=user.id, is_active=True).first()
                if sl:
                    seller_land = land_to_dict(sl)
                    for b in Booking.query.filter_by(land_id=sl.id).all():
                        buyer = db.session.get(User, b.buyer_id)
                        token_buyers.append({
                            "phone":      buyer.phone if buyer else "—",
                            "name":       buyer.name  if buyer else "Unknown",
                            "ref_number": b.ref_number,
                            "timestamp":  b.created_at.strftime("%Y-%m-%d %H:%M") if b.created_at else "",
                            "amount":     b.amount_paid,
                            "status":     b.status,
                        })
        except Exception as e:
            logger.error(f"Seller home error: {e}")

    return render_template("home_page.html",
                           lands=lands,
                           seller_land=seller_land,
                           token_buyers=token_buyers)


# ─────────────────────────────────────────────────────────────────────────
# BUYER / SELLER PAGES
# ─────────────────────────────────────────────────────────────────────────

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


@app.route("/register_buyer", methods=["POST"])
def register_buyer():
    if "user" not in session:
        return redirect("/login")
    try:
        user = User.query.filter_by(phone=session["user"]).first()
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
    except Exception as e:
        db.session.rollback()
        logger.error(f"register_buyer error: {e}")
    return redirect("/")


@app.route("/register_seller", methods=["POST"])
def register_seller():
    if "user" not in session:
        return redirect("/login")
    try:
        user  = User.query.filter_by(phone=session["user"]).first()
        image = request.files.get("image")
        image_path = ""
        if image and image.filename and allowed_file(image.filename):
            filename = f"{session['user']}_{uuid.uuid4().hex[:8]}_{image.filename}"
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
                seller_id=user.id, title=request.form.get("title"),
                location=request.form.get("location"), address=request.form.get("address"),
                price=request.form.get("price"), area=request.form.get("area") or None,
                land_type=request.form.get("land_type"),
                legal_issue=request.form.get("legal_issue", "No"),
                image=image_path,
                lat=float(lat) if lat else None, lng=float(lng) if lng else None,
            )
            db.session.add(land)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"register_seller error: {e}")
    return redirect("/")


# ─────────────────────────────────────────────────────────────────────────
# LAND DETAIL
# ─────────────────────────────────────────────────────────────────────────

@app.route("/land/<int:land_id>")
def land_detail(land_id):
    land = db.session.get(Land, land_id)
    if not land:
        return render_template("login.html", error="Land not found."), 404
    return render_template("land_details.html", land=land_to_dict(land), predicted_price=None)


# ─────────────────────────────────────────────────────────────────────────
# AI PRICE PREDICTOR
# ─────────────────────────────────────────────────────────────────────────

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
            predicted_price = f"₹ {estimated/1_00_00_000:.2f} Crore"
        elif estimated >= 1_00_000:
            predicted_price = f"₹ {estimated/1_00_000:.1f} Lakh"
        else:
            predicted_price = f"₹ {int(estimated):,}"
    except Exception:
        predicted_price = "Unable to predict — check inputs"
        land_id = 0
    land = db.session.get(Land, land_id)
    land_dict = land_to_dict(land) if land else {
        "id": land_id, "title": "Land", "location": "",
        "price": "0", "image": "", "lat": None, "lng": None
    }
    return render_template("land_details.html", land=land_dict, predicted_price=predicted_price)


# ─────────────────────────────────────────────────────────────────────────
# SEARCH
# ─────────────────────────────────────────────────────────────────────────

@app.route("/search")
def search():
    location  = request.args.get("location", "").strip()
    min_price = request.args.get("min_price", "")
    max_price = request.args.get("max_price", "")
    land_type = request.args.get("land_type", "")
    try:
        query = Land.query.filter_by(is_active=True)
        if location:
            query = query.filter(Land.location.ilike(f"%{location}%"))
        if land_type:
            query = query.filter_by(land_type=land_type)
        results = query.all()
    except Exception as e:
        logger.error(f"Search error: {e}")
        results = []

    def parse_price(p):
        try: return float(str(p).replace(",", "").replace(" ", ""))
        except: return 0

    if min_price:
        results = [l for l in results if parse_price(l.price) >= float(min_price)]
    if max_price:
        results = [l for l in results if parse_price(l.price) <= float(max_price)]
    return render_template("search_results.html", lands=[land_to_dict(l) for l in results])


# ─────────────────────────────────────────────────────────────────────────
# MAP SEARCH
# ─────────────────────────────────────────────────────────────────────────

@app.route("/map-search")
def map_search():
    try:
        lands = Land.query.filter_by(is_active=True).all()
    except Exception:
        lands = []
    return render_template("map_search.html", lands=[land_to_dict(l) for l in lands])


# ─────────────────────────────────────────────────────────────────────────
# OTHER PAGES
# ─────────────────────────────────────────────────────────────────────────

@app.route("/select_land")
def select_land():
    return render_template("select_land.html")


@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect("/login")
    user = User.query.filter_by(phone=session["user"]).first()
    if not user:
        session.clear()
        return redirect("/login")
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
    try:
        user       = User.query.filter_by(phone=session["user"]).first()
        user.name  = request.form.get("name")
        user.email = request.form.get("email")
        new_pw     = request.form.get("password")
        if new_pw:
            user.password = new_pw
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"save_profile error: {e}")
    return redirect("/profile")


# ─────────────────────────────────────────────────────────────────────────
# SAVED / WISHLIST
# ─────────────────────────────────────────────────────────────────────────

@app.route("/saved")
def saved_page():
    if "user" not in session:
        return redirect("/login")
    try:
        user = User.query.filter_by(phone=session["user"]).first()
        wishlist_items = Wishlist.query.filter_by(user_id=user.id).all()
        saved_lands = []
        for item in wishlist_items:
            land = db.session.get(Land, item.land_id)
            if land and land.is_active:
                saved_lands.append(land_to_dict(land))
    except Exception as e:
        logger.error(f"Saved page error: {e}")
        saved_lands = []
    return render_template("saved.html", saved_lands=saved_lands)


@app.route("/save_wishlist", methods=["POST"])
def save_wishlist():
    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401
    try:
        user = User.query.filter_by(phone=session["user"]).first()
        data = request.get_json()
        ids  = data.get("ids", [])
        Wishlist.query.filter_by(user_id=user.id).delete()
        for land_id in ids:
            land = db.session.get(Land, int(land_id))
            if land:
                db.session.add(Wishlist(user_id=user.id, land_id=land.id))
        db.session.commit()
        return jsonify({"success": True, "saved": len(ids)}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"save_wishlist error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/saved_count")
def saved_count():
    if "user" not in session:
        return jsonify({"count": 0})
    try:
        user  = User.query.filter_by(phone=session["user"]).first()
        count = Wishlist.query.filter_by(user_id=user.id).count() if user else 0
        return jsonify({"count": count})
    except Exception:
        return jsonify({"count": 0})


# ─────────────────────────────────────────────────────────────────────────
# PAYMENT / BOOKINGS
# ─────────────────────────────────────────────────────────────────────────

@app.route("/process_payment", methods=["POST"])
def process_payment():
    if "user" not in session:
        return jsonify({"success": False, "error": "Please login to continue"}), 401
    try:
        user           = User.query.filter_by(phone=session["user"]).first()
        data           = request.get_json()
        land_ids       = data.get("land_ids", [])
        payment_method = data.get("payment_method", "upi")
        amount         = data.get("amount", "₹0")
        ref_number     = "LL-" + uuid.uuid4().hex[:8].upper()
        for lid in land_ids:
            land = db.session.get(Land, int(lid))
            if land:
                db.session.add(Booking(
                    ref_number=f"{ref_number}-{lid}", buyer_id=user.id,
                    land_id=land.id, payment_method=payment_method,
                    amount_paid=amount, status="token_paid"
                ))
        db.session.commit()
        return jsonify({"success": True, "ref_number": ref_number,
                        "message": "Token payment recorded successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"process_payment error: {e}")
        return jsonify({"success": False, "error": "Payment processing failed"}), 500


@app.route("/my_bookings")
def my_bookings():
    if "user" not in session:
        return redirect("/login")
    phone   = session["user"]
    purpose = session.get("purpose", "buy")
    bookings = []
    try:
        user = User.query.filter_by(phone=phone).first()
        if purpose == "buy":
            for b in Booking.query.filter_by(buyer_id=user.id).order_by(Booking.created_at.desc()).all():
                land = db.session.get(Land, b.land_id)
                bookings.append({
                    "ref_number": b.ref_number,
                    "timestamp":  b.created_at.strftime("%Y-%m-%d %H:%M") if b.created_at else "",
                    "payment_method": b.payment_method, "amount_paid": b.amount_paid,
                    "status": b.status, "lands": [land_to_dict(land)] if land else []
                })
        else:
            sl = Land.query.filter_by(seller_id=user.id).first()
            if sl:
                for b in Booking.query.filter_by(land_id=sl.id).order_by(Booking.created_at.desc()).all():
                    buyer = db.session.get(User, b.buyer_id)
                    bookings.append({
                        "ref_number": b.ref_number,
                        "timestamp":  b.created_at.strftime("%Y-%m-%d %H:%M") if b.created_at else "",
                        "payment_method": b.payment_method, "amount_paid": b.amount_paid,
                        "status": b.status, "buyer_phone": buyer.phone if buyer else "—",
                        "buyer_name": buyer.name if buyer else "Unknown",
                        "lands": [land_to_dict(sl)]
                    })
    except Exception as e:
        logger.error(f"my_bookings error: {e}")
    return render_template("my_bookings.html", bookings=bookings)


@app.route("/update_booking_status", methods=["POST"])
def update_booking_status():
    if "user" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    try:
        data       = request.get_json()
        ref_number = data.get("ref_number")
        new_status = data.get("status")
        VALID = ["token_paid", "docs_verified", "site_visit", "registered", "cancelled"]
        if new_status not in VALID:
            return jsonify({"success": False, "error": "Invalid status"}), 400
        booking = Booking.query.filter_by(ref_number=ref_number).first()
        if not booking:
            return jsonify({"success": False, "error": "Booking not found"}), 404
        booking.status = new_status
        db.session.commit()
        return jsonify({"success": True, "ref_number": ref_number, "new_status": new_status})
    except Exception as e:
        db.session.rollback()
        logger.error(f"update_booking_status error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────
# AI PREDICTOR WAITLIST
# ─────────────────────────────────────────────────────────────────────────

@app.route("/notify_predictor", methods=["POST"])
def notify_predictor():
    try:
        data  = request.get_json()
        email = data.get("email", "").strip()
        if not email or "@" not in email:
            return jsonify({"success": False, "error": "Invalid email"}), 400
        if not PredictorWaitlist.query.filter_by(email=email).first():
            db.session.add(PredictorWaitlist(email=email))
            db.session.commit()
        return jsonify({"success": True, "message": "Added to waitlist"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"notify_predictor error: {e}")
        return jsonify({"success": False, "error": "Could not add to waitlist"}), 500


# ─────────────────────────────────────────────────────────────────────────
# INIT TABLES + RUN
# ─────────────────────────────────────────────────────────────────────────

with app.app_context():
    init_db_with_retry()

if __name__ == "__main__":
    PORT  = int(os.environ.get("PORT", 8080))
    DEBUG = os.environ.get("FLASK_ENV") == "development"
    logger.info(f"Starting LandLink on port {PORT} (debug={DEBUG})")
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)