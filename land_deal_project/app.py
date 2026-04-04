from flask import Flask, render_template, request, redirect, session
import os
import json
from datetime import datetime

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
# -------------------------
# @app.route("/login_user", methods=["POST"])
# def login_user():
#     phone = request.form.get("phone")
#     password = request.form.get("password")
#     purpose = request.form.get("purpose")

#     folder = "buyer_data" if purpose == "buy" else "seller_data"
#     filepath = os.path.join(BASE_DIR, folder, f"{phone}.json")

#     if not os.path.exists(filepath):
#         return "User not found"

#     with open(filepath, "r") as f:
#         user = json.load(f)

#     if user["password"] == password:
#         session["user"] = phone
#         session["purpose"] = purpose

#         if purpose == "buy":
#             return redirect("/buyer")
#         else:
#             return redirect("/seller")
#     else:
#         return "Wrong password"


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
@app.route("/land/<int:land_id>")
def land_detail(land_id):

    with open(os.path.join(BASE_DIR, "lands.json")) as f:
        lands = json.load(f)

    if land_id >= len(lands):
        return "Land not found"

    land = lands[land_id]

    return render_template("land_details.html", land=land)


# -------------------------
# Map selector
# -------------------------
@app.route("/select_land")
def select_land():
    return render_template("select_land.html")
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




@app.route("/search")
def search():

    location = request.args.get("location", "").lower()
    min_price = int(request.args.get("min_price", 0))
    max_price = int(request.args.get("max_price", 999999999))

    with open("lands.json") as f:
        lands = json.load(f)

    results = []

    for land in lands:
        price = int(land["price"])

        if (
            location in land["location"].lower()
            and price >= min_price
            and price <= max_price
        ):
            results.append(land)

    return render_template("search_results.html", lands=results)


@app.route("/map-search")
def map_search():

    with open("lands.json") as f:
        lands = json.load(f)

    return render_template("map_search.html", lands=lands)

if __name__ == "__main__":
    app.run(debug=True)