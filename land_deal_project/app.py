from flask import Flask, render_template, request, redirect, session
import os
import json
from datetime import datetime
import uuid


app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = "landlink_secret"

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# create folders if not exist
os.makedirs(os.path.join(BASE_DIR, "buyer_data"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "seller_data"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "buyer_preference"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "seller_preference"), exist_ok=True)

# IMPORTANT: static upload folder
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# -------------------------
# Login Page
# -------------------------
@app.route("/login")
def login_page():
    return render_template("login.html")


# -------------------------
# Login Submit
# -------------------
@app.route("/login_user", methods=["POST"])
def login_user():
    phone = request.form.get("phone")
    password = request.form.get("password")
    purpose = request.form.get("purpose")

    folder = "buyer_data" if purpose == "buy" else "seller_data"
    filepath = os.path.join(BASE_DIR, folder, f"{phone}.json")

    if not os.path.exists(filepath):
        return render_template("login.html", error="❌ No account found with this number.")

    with open(filepath, "r") as f:
        user = json.load(f)

    if user["password"] == password:
        session["user"] = phone
        session["purpose"] = purpose
        return redirect("/buyer" if purpose == "buy" else "/seller")
    else:
        return render_template("login.html", error="❌ Incorrect password.")
    



@app.route("/signup", methods=["POST"])
def signup():
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    password = request.form.get("password")
    confirm = request.form.get("confirm")
    purpose = request.form.get("purpose")

    if password != confirm:
        return "Passwords do not match"

    folder = "buyer_data" if purpose == "buy" else "seller_data"
    filepath = os.path.join(BASE_DIR, folder, f"{phone}.json")

    if os.path.exists(filepath):
        return "User already exists with this number"

    user_data = {
        "name": name,
        "email": email,
        "phone": phone,
        "password": password
    }

    with open(filepath, "w") as f:
        json.dump(user_data, f, indent=4)

    # Auto login after register
    session["user"] = phone
    session["purpose"] = purpose

    if purpose == "buy":
        return redirect("/buyer")
    else:
        return redirect("/seller")


# -------------------------
# Logout
# -------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# -------------------------
# Home Page
# -------------------------
@app.route("/")
def home():
    try:
        with open(os.path.join(BASE_DIR, "lands.json"), "r") as f:
            lands = json.load(f)
    except:
        lands = []

    return render_template("home_page.html", lands=lands)


# -------------------------
# Buyer Page
# -------------------------
@app.route("/buyer")
def buyer_page():
    if "user" not in session:
        return redirect("/login")
    return render_template("buyer_register.html")


# -------------------------
# Seller Page
# -------------------------
@app.route("/seller")
def seller_page():
    if "user" not in session:
        return redirect("/login")
    return render_template("seller_register.html")


# -------------------------
# Buyer Preference
# -------------------------
@app.route("/register_buyer", methods=["POST"])
def register_buyer():

    if "user" not in session:
        return redirect("/login")

    phone = session["user"]

    data = {
        "phone": phone,
        "location": request.form.get("location"),
        "budget": request.form.get("budget"),
        "land_type": request.form.get("land_type"),
        "min_area": request.form.get("min_area"),
        "max_area": request.form.get("max_area"),
        "road_access": request.form.get("road_access"),
        "purpose": request.form.get("purpose")
    }

    filepath = os.path.join(BASE_DIR, "buyer_preference", f"{phone}.json")

    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

    return redirect("/")


# -------------------------
# Seller Registration
# -------------------------
@app.route("/register_seller", methods=["POST"])
def register_seller():

    if "user" not in session:
        return redirect("/login")

    phone = session["user"]

    # --------- Image Upload ----------
    image = request.files.get("image")
    image_relative_path = ""

    if image and image.filename != "":
        image_name = f"{phone}_{image.filename}"
        image_path = os.path.join(UPLOAD_FOLDER, image_name)
        image.save(image_path)
        image_relative_path = f"uploads/{image_name}"

    # --------- Get Map Coordinates ----------
    lat = request.form.get("lat")
    lng = request.form.get("lng")

    # --------- Seller Data ----------
    data = {
        "phone": phone,
        "title": request.form.get("title"),
        "location": request.form.get("location"),
        "address": request.form.get("address"),
        "price": request.form.get("price"),
        "area": request.form.get("area"),
        "land_type": request.form.get("land_type"),
        "legal_issue": request.form.get("legal_issue"),
        "image": image_relative_path,
        "lat": lat,
        "lng": lng
    }

    # --------- Save seller preference ----------
    pref_path = os.path.join(BASE_DIR, "seller_preference", f"{phone}.json")
    with open(pref_path, "w") as f:
        json.dump(data, f, indent=4)

    # --------- Save seller login data ----------
    seller_path = os.path.join(BASE_DIR, "seller_data", f"{phone}.json")

    if not os.path.exists(seller_path):
        seller_login_data = {
            "phone": phone,
            "password": "1234"
        }

        with open(seller_path, "w") as f:
            json.dump(seller_login_data, f, indent=4)

    # --------- Update lands.json ----------
    lands_file = os.path.join(BASE_DIR, "lands.json")

    if os.path.exists(lands_file):
        with open(lands_file, "r") as f:
            lands = json.load(f)
    else:
        lands = []

    land_card = {
        "id": len(lands),
        "title": data["title"],
        "location": data["location"],
        "address": data["address"],
        "price": data["price"],
        "area": data["area"],
        "land_type": data["land_type"],
        "legal_issue": data["legal_issue"],
        "image": data["image"],
        "lat": float(lat) if lat else None,
        "lng": float(lng) if lng else None
    }

    lands.append(land_card)

    with open(lands_file, "w") as f:
        json.dump(lands, f, indent=4)

    return redirect("/")


# -------------------------
# Land Details
# -------------------------
# ── Add / replace these routes in your app.py ──────────────────


# ── 1. Land Detail page ─────────────────────────────────────────
@app.route("/land/<int:land_id>")
def land_detail(land_id):
    lands_file = os.path.join(BASE_DIR, "lands.json")
    try:
        with open(lands_file) as f:
            lands = json.load(f)
    except:
        return "Lands data not found", 500

    if land_id >= len(lands):
        return render_template("404.html"), 404

    land = lands[land_id]

    # Inject the id into the land dict so templates can use {{ land.id }}
    land["id"] = land_id

    # Pass predicted_price=None initially (only set after form submit)
    return render_template("land_details.html", land=land, predicted_price=None)


# ── 2. AI Price Predictor (simple rule-based until ML model ready) ──
@app.route("/predict_price", methods=["POST"])
def predict_price():
    
    try:
        area       = float(request.form.get("area", 0))
        distance   = float(request.form.get("distance", 10))
        road       = int(request.form.get("road", 1))
        land_type  = request.form.get("land_type_pred", "Agriculture")
        land_id    = int(request.form.get("land_id", 0))

        # ── Base rate per sq.ft by type ──
        base_rates = {
            "Agriculture": 50,
            "Residential": 180,
            "Commercial":  320,
        }
        base = base_rates.get(land_type, 80)

        # ── Adjustments ──
        # Distance penalty: -2% per km from city, max -50%
        dist_factor = max(0.5, 1 - (distance * 0.02))

        # Road access bonus
        road_bonus = 1.12 if road == 1 else 1.0

        # Final calculation
        estimated = area * base * dist_factor * road_bonus

        # Format Indian style
        if estimated >= 1_00_00_000:
            display = f"{estimated/1_00_00_000:.2f} Crore"
        elif estimated >= 1_00_000:
            display = f"{estimated/1_00_000:.1f} Lakh"
        else:
            display = f"{int(estimated):,}"

        predicted_price = display

    except Exception as e:
        predicted_price = "Unable to predict — check inputs"

    # Reload the land and re-render with prediction
    lands_file = os.path.join(BASE_DIR, "lands.json")
    try:
        with open(lands_file) as f:
            lands = json.load(f)
        land = lands[land_id]
        land["id"] = land_id
    except:
        land = {"title": "Land", "location": "", "price": "0",
                "image": "", "lat": None, "lng": None, "id": land_id}

    return render_template(
        "land_details.html",
        land=land,
        predicted_price=predicted_price
    )
# -------------------------
# Map selector
# -------------------------
@app.route("/select_land")
def select_land():
    return render_template("select_land.html")

@app.route("/notify_predictor", methods=["POST"])
def notify_predictor():
    """Saves email to a waitlist for the AI Land Predictor feature."""
    data  = request.get_json()
    email = data.get("email", "").strip()
 
    if not email or "@" not in email:
        return {"success": False, "error": "Invalid email"}, 400
 
    waitlist_file = os.path.join(BASE_DIR, "predictor_waitlist.json")
 
    try:
        with open(waitlist_file) as f:
            waitlist = json.load(f)
    except:
        waitlist = []
 
    if email not in waitlist:
        waitlist.append(email)
        with open(waitlist_file, "w") as f:
            json.dump(waitlist, f, indent=4)
 
    return {"success": True, "message": "Added to waitlist"}, 200
 
# -----------------------
# Profile 
# -----------------------------

@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect("/login")

    phone = session["user"]
    purpose = session["purpose"]

    folder = "buyer_data" if purpose == "buy" else "seller_data"
    filepath = os.path.join(BASE_DIR, folder, f"{phone}.json")

    with open(filepath) as f:
        user = json.load(f)

    return render_template("profile.html", user=user)



@app.route("/edit_profile")
def edit_profile():
    if "user" not in session:
        return redirect("/login")

    phone = session["user"]
    purpose = session["purpose"]

    folder = "buyer_data" if purpose == "buy" else "seller_data"
    filepath = os.path.join(BASE_DIR, folder, f"{phone}.json")

    with open(filepath) as f:
        user = json.load(f)

    return render_template("edit_profile.html", user=user)




@app.route("/save_profile", methods=["POST"])
def save_profile():

    phone = session["user"]
    purpose = session["purpose"]

    folder = "buyer_data" if purpose == "buy" else "seller_data"
    filepath = os.path.join(BASE_DIR, folder, f"{phone}.json")

    data = {
        "name": request.form.get("name"),
        "email": request.form.get("email"),
        "phone": phone,
        "password": request.form.get("password")
    }

    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

    return redirect("/profile")







# ── Add this route to your app.py ──────────────────────────────

@app.route("/save_wishlist", methods=["POST"])
def save_wishlist():
    """Save buyer's wishlist (saved land IDs) to their profile JSON."""
    if "user" not in session:
        return {"error": "Not logged in"}, 401

    phone = session["user"]
    purpose = session.get("purpose", "buy")

    data = request.get_json()
    ids = data.get("ids", [])

    # Load lands.json to get full land details
    lands_file = os.path.join(BASE_DIR, "lands.json")
    with open(lands_file) as f:
        all_lands = json.load(f)

    wishlist = []
    for land_id in ids:
        if 0 <= land_id < len(all_lands):
            wishlist.append(all_lands[land_id])

    # Save wishlist into the buyer's data file
    folder = "buyer_data" if purpose == "buy" else "seller_data"
    filepath = os.path.join(BASE_DIR, folder, f"{phone}.json")

    if os.path.exists(filepath):
        with open(filepath) as f:
            user = json.load(f)
    else:
        user = {"phone": phone}

    user["wishlist"] = wishlist

    with open(filepath, "w") as f:
        json.dump(user, f, indent=4)

    return {"success": True, "saved": len(wishlist)}, 200




@app.route("/search")
def search():
    location  = request.args.get("location", "").lower().strip()
    min_price = request.args.get("min_price", "0").strip() or "0"
    max_price = request.args.get("max_price", "999999999").strip() or "999999999"

    # Strip commas/spaces from price strings before converting
    try:
        min_p = int(str(min_price).replace(",", "").replace(" ", ""))
    except:
        min_p = 0

    try:
        max_p = int(str(max_price).replace(",", "").replace(" ", ""))
    except:
        max_p = 999_999_999

    lands_file = os.path.join(BASE_DIR, "lands.json")
    try:
        with open(lands_file) as f:
            lands = json.load(f)
    except:
        lands = []

    results = []
    for land in lands:
        try:
            # Strip commas from stored price too (e.g. "25,00,000")
            price = int(str(land.get("price", "0")).replace(",", "").replace(" ", ""))
        except:
            price = 0

        loc_match   = not location or location in land.get("location", "").lower()
        price_match = min_p <= price <= max_p

        if loc_match and price_match:
            results.append(land)

    return render_template("search_results.html", lands=results)



@app.route("/map-search")
def map_search():

    with open("lands.json") as f:
        lands = json.load(f)

    return render_template("map_search.html", lands=lands)







# ── 1. Saved / Cart page ────────────────────────────────────────
@app.route("/saved")
def saved_page():
    """Renders the saved lands / cart page."""
    return render_template("saved.html")


# ── 2. Process Payment ──────────────────────────────────────────
@app.route("/process_payment", methods=["POST"])
def process_payment():
    """
    Receives payment request, saves booking record to buyer's profile.
    In production: integrate Razorpay / PayU / CCAvenue here.
    """
    if "user" not in session:
        return {"success": False, "error": "Please login to continue"}, 401

    phone   = session["user"]
    purpose = session.get("purpose", "buy")
    data    = request.get_json()

    land_ids       = data.get("land_ids", [])
    payment_method = data.get("payment_method", "upi")
    amount         = data.get("amount", "₹0")

    # Generate a unique reference number
    ref_number = "LL-" + str(uuid.uuid4()).replace("-","").upper()[:8]

    # Load full land details for booked lands
    lands_file = os.path.join(BASE_DIR, "lands.json")
    try:
        with open(lands_file) as f:
            all_lands = json.load(f)
    except:
        all_lands = []

    booked_lands = []
    for lid in land_ids:
        try:
            idx = int(lid)
            if 0 <= idx < len(all_lands):
                booked_lands.append(all_lands[idx])
        except:
            pass

    # Build booking record
    booking = {
        "ref_number":     ref_number,
        "timestamp":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "buyer_phone":    phone,
        "payment_method": payment_method,
        "amount_paid":    amount,
        "status":         "token_paid",   # token_paid → docs_verified → registered
        "lands":          booked_lands
    }

    # ── Save booking to buyer's profile ──
    folder   = "buyer_data" if purpose == "buy" else "seller_data"
    filepath = os.path.join(BASE_DIR, folder, f"{phone}.json")

    try:
        with open(filepath) as f:
            user = json.load(f)
    except:
        user = {"phone": phone}

    if "bookings" not in user:
        user["bookings"] = []

    user["bookings"].append(booking)

    with open(filepath, "w") as f:
        json.dump(user, f, indent=4)

    # ── Save to a global bookings log ──
    bookings_file = os.path.join(BASE_DIR, "bookings.json")
    try:
        with open(bookings_file) as f:
            all_bookings = json.load(f)
    except:
        all_bookings = []

    all_bookings.append(booking)

    with open(bookings_file, "w") as f:
        json.dump(all_bookings, f, indent=4)

    return {
        "success":    True,
        "ref_number": ref_number,
        "message":    "Token payment recorded successfully"
    }, 200


# ── 3. View Bookings (for profile page) ────────────────────────
@app.route("/my_bookings")
def my_bookings():
    """Returns the logged-in buyer's booking history."""
    if "user" not in session:
        return redirect("/login")

    phone   = session["user"]
    purpose = session.get("purpose", "buy")
    folder  = "buyer_data" if purpose == "buy" else "seller_data"
    filepath = os.path.join(BASE_DIR, folder, f"{phone}.json")

    try:
        with open(filepath) as f:
            user = json.load(f)
        bookings = user.get("bookings", [])
    except:
        bookings = []

    return render_template("my_bookings.html", bookings=bookings)


# ── 4. Update navbar heart badge count (optional AJAX) ─────────
@app.route("/api/saved_count")
def saved_count():
    """
    Optional: call this via fetch() on page load to sync
    the heart badge in the navbar with the server-side wishlist.
    """
    if "user" not in session:
        return {"count": 0}

    phone   = session["user"]
    purpose = session.get("purpose", "buy")
    folder  = "buyer_data" if purpose == "buy" else "seller_data"
    filepath = os.path.join(BASE_DIR, folder, f"{phone}.json")

    try:
        with open(filepath) as f:
            user = json.load(f)
        count = len(user.get("wishlist", []))
    except:
        count = 0

    return {"count": count}

if __name__ == "__main__":
    app.run(debug=True)