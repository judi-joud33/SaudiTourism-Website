import os
import re
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, jsonify
)
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func, text
from sqlalchemy.exc import OperationalError

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET_KEY")

basedir = os.path.abspath(os.path.dirname(__file__))
volume_mount_path = os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
db_path = os.path.join(volume_mount_path, "site.db") if volume_mount_path else os.path.join(basedir, "site.db")
normalized_db_path = db_path.replace("\\", "/")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{normalized_db_path}"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


def ensure_profile_admin_column():
    """Backfill old SQLite databases that predate is_admin."""
    columns = db.session.execute(text("PRAGMA table_info(profiles)")).mappings().all()
    column_names = {col["name"] for col in columns}

    if "is_admin" not in column_names:
        db.session.execute(
            text("ALTER TABLE profiles ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0")
        )
        db.session.commit()

    admin_count = db.session.execute(
        text("SELECT COUNT(1) FROM profiles WHERE is_admin = 1")
    ).scalar()
    if not admin_count:
        first_user_id = db.session.execute(
            text("SELECT id FROM profiles ORDER BY id ASC LIMIT 1")
        ).scalar()
        if first_user_id:
            db.session.execute(
                text("UPDATE profiles SET is_admin = 1 WHERE id = :user_id"),
                {"user_id": first_user_id}
            )
            db.session.commit()


def ensure_location_image_column():
    """Backfill old SQLite databases that predate image_url."""
    columns = db.session.execute(text("PRAGMA table_info(locations)")).mappings().all()
    column_names = {col["name"] for col in columns}

    if "image_url" not in column_names:
        db.session.execute(
            text("ALTER TABLE locations ADD COLUMN image_url VARCHAR(500)")
        )
        db.session.commit()


# ─── DATABASE MODELS ─────────────────────────────────────────────

class Profile(db.Model):
    __tablename__ = 'profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    nationality = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    reviews = db.relationship('Review', backref='author', lazy=True, cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='user', lazy=True, cascade='all, delete-orphan')


class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    
    locations = db.relationship('Location', backref='category', lazy=True)


class Location(db.Model):
    __tablename__ = 'locations'
    
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(255))
    region = db.Column(db.String(255))
    image_url = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text)
    featured = db.Column(db.Boolean, default=False, index=True)
    rating_avg = db.Column(db.Float, default=0.0)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    reviews = db.relationship('Review', backref='location', lazy=True, cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='location', lazy=True, cascade='all, delete-orphan')
    
    @property
    def review_count(self):
        return len(self.reviews)

    def update_rating(self):
        """Update the average rating based on reviews"""
        rating_total, review_count = db.session.query(
            func.coalesce(func.sum(Review.rating), 0),
            func.count(Review.id)
        ).filter(Review.location_id == self.id).one()

        if review_count == 0:
            self.rating_avg = 0.0
            return

        avg_rating = (Decimal(rating_total) / Decimal(review_count)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )
        self.rating_avg = float(avg_rating)


class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('profiles.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    visit_date = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


class Favorite(db.Model):
    __tablename__ = 'favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('profiles.id'), nullable=False, index=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'location_id', name='unique_user_location'),)



def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("login", next=request.url))

        try:
            profile = Profile.query.get(int(user["id"]))
        except OperationalError as e:
            if "no such column: profiles.is_admin" in str(e):
                db.session.rollback()
                ensure_profile_admin_column()
                profile = Profile.query.get(int(user["id"]))
            else:
                raise
        if not profile or not profile.is_admin:
            flash("You do not have permission to access that page.", "error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated


def get_current_user():
    return session.get("user")


@app.context_processor
def inject_user():
    return {"current_user": get_current_user()}


@app.before_request
def ensure_schema_ready():
    if not app.config.get("SCHEMA_READY", False):
        ensure_profile_admin_column()
        ensure_location_image_column()
        app.config["SCHEMA_READY"] = True


# ─── AUTH ROUTES ─────────────────────────────────────────────

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        full_name = request.form.get("full_name", "").strip()
        nationality = request.form.get("nationality", "").strip()

        if not email or not password or not full_name:
            flash("All fields are required.", "error")
            return render_template("register.html")

        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            flash("Please enter a valid email address.", "error")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("register.html")

        try:
            try:
                existing = Profile.query.filter_by(email=email).first()
            except OperationalError as e:
                if "no such column: profiles.is_admin" in str(e):
                    db.session.rollback()
                    ensure_profile_admin_column()
                    existing = Profile.query.filter_by(email=email).first()
                else:
                    raise
            if existing:
                flash("This email is already registered. Please sign in.", "error")
                return render_template("register.html")

            hashed = generate_password_hash(password)
            is_first_user = Profile.query.count() == 0
            profile = Profile(
                email=email,
                password_hash=hashed,
                full_name=full_name,
                nationality=nationality,
                is_admin=is_first_user
            )
            db.session.add(profile)
            db.session.commit()

            session["user"] = {
                "id": str(profile.id),
                "email": email,
                "full_name": full_name,
                "is_admin": profile.is_admin
            }
            flash("Welcome to Saudi Tourism Guide!", "success")
            return redirect(url_for("index"))
        except Exception as e:
            db.session.rollback()
            flash(f"Registration error: {str(e)}", "error")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password are required.", "error")
            return render_template("login.html")

        try:
            try:
                user_data = Profile.query.filter_by(email=email).first()
            except OperationalError as e:
                if "no such column: profiles.is_admin" in str(e):
                    db.session.rollback()
                    ensure_profile_admin_column()
                    user_data = Profile.query.filter_by(email=email).first()
                else:
                    raise

            if not user_data or not check_password_hash(user_data.password_hash, password):
                flash("Invalid email or password.", "error")
                return render_template("login.html")

            session["user"] = {
                "id": str(user_data.id),
                "email": user_data.email,
                "full_name": user_data.full_name,
                "is_admin": user_data.is_admin
            }
            flash(f"Welcome back, {user_data.full_name}!", "success")
            next_url = request.args.get("next", url_for("index"))
            return redirect(next_url)
        except Exception as e:
            flash("Invalid email or password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("You have been signed out.", "info")
    return redirect(url_for("index"))



# ─── MAIN PAGES ─────────────────────────────────────────────

@app.route("/")
def index():
    featured = Location.query.filter_by(featured=True).order_by(Location.rating_avg.desc()).limit(6).all()
    categories = Category.query.all()
    return render_template("index.html",
                           featured_locations=featured,
                           categories=categories)


@app.route("/locations")
def locations():
    category_slug = request.args.get("category", "")
    search_query = request.args.get("q", "").strip()

    query = Location.query

    if category_slug:
        cat = Category.query.filter_by(slug=category_slug).first()
        if cat:
            query = query.filter_by(category_id=cat.id)

    if search_query:
        search_filter = f"%{search_query}%"
        query = query.filter(
            (Location.name.ilike(search_filter)) |
            (Location.city.ilike(search_filter)) |
            (Location.region.ilike(search_filter)) |
            (Location.description.ilike(search_filter))
        )

    results = query.order_by(Location.featured.desc(), Location.rating_avg.desc()).all()
    categories = Category.query.all()

    return render_template("locations.html",
                           locations=results,
                           categories=categories,
                           active_category=category_slug,
                           search_query=search_query)


@app.route("/location/<slug>")
def location_detail(slug):
    loc = Location.query.filter_by(slug=slug).first()
    if not loc:
        flash("Location not found.", "error")
        return redirect(url_for("locations"))

    reviews = Review.query.filter_by(location_id=loc.id).order_by(Review.created_at.desc()).all()

    user = get_current_user()
    is_favorited = False
    if user:
        fav = Favorite.query.filter_by(user_id=int(user["id"]), location_id=loc.id).first()
        is_favorited = fav is not None

    return render_template("location_detail.html",
                           location=loc,
                           reviews=reviews,
                           is_favorited=is_favorited)


@app.route("/location/<slug>/review", methods=["POST"])
@login_required
def submit_review(slug):
    loc = Location.query.filter_by(slug=slug).first()
    if not loc:
        flash("Location not found.", "error")
        return redirect(url_for("locations"))

    rating_raw = request.form.get("rating", "").strip()
    title = request.form.get("title", "").strip()
    body = request.form.get("body", "").strip()
    visit_date = request.form.get("visit_date", "").strip()

    try:
        rating = int(rating_raw)
    except (TypeError, ValueError):
        rating = None

    if rating is None or not title or not body:
        flash("Rating, title, and review body are required.", "error")
        return redirect(url_for("location_detail", slug=slug))

    if rating < 1 or rating > 5:
        flash("Rating must be between 1 and 5.", "error")
        return redirect(url_for("location_detail", slug=slug))

    user = get_current_user()
    try:
        review = Review(
            location_id=loc.id,
            user_id=int(user["id"]),
            rating=rating,
            title=title,
            body=body,
            visit_date=visit_date if visit_date else None
        )
        db.session.add(review)
        db.session.flush()
        loc.update_rating()
        db.session.commit()
        
        flash("Your review has been submitted!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error submitting review: {str(e)}", "error")

    return redirect(url_for("location_detail", slug=slug))


@app.route("/location/<slug>/favorite", methods=["POST"])
@login_required
def toggle_favorite(slug):
    loc = Location.query.filter_by(slug=slug).first()
    if not loc:
        return jsonify({"error": "Location not found"}), 404

    user = get_current_user()
    user_id = int(user["id"])
    
    existing = Favorite.query.filter_by(user_id=user_id, location_id=loc.id).first()

    try:
        if existing:
            db.session.delete(existing)
            db.session.commit()
            return jsonify({"favorited": False})
        else:
            fav = Favorite(user_id=user_id, location_id=loc.id)
            db.session.add(fav)
            db.session.commit()
            return jsonify({"favorited": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not email or not message:
            flash("Please fill in all required fields.", "error")
        else:
            flash("Thank you for your message! We will get back to you soon.", "success")
            return redirect(url_for("contact"))

    return render_template("contact.html")



@app.route("/admin/dashboard", methods=["GET", "POST"])
@admin_required
def admin_dashboard():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        slug = request.form.get("slug", "").strip().lower()
        city = request.form.get("city", "").strip()
        region = request.form.get("region", "").strip()
        image_url = request.form.get("image_url", "").strip()
        description = request.form.get("description", "").strip()
        category_name = request.form.get("category", "").strip()

        if not all([name, slug, city, region, description, category_name]):
            flash("All location fields are required.", "error")
            return redirect(url_for("admin_dashboard"))

        try:
            existing_location = Location.query.filter_by(slug=slug).first()
            if existing_location:
                flash("A location with that slug already exists.", "error")
                return redirect(url_for("admin_dashboard"))

            category_slug = category_name.lower().replace("&", "and")
            category_slug = re.sub(r"[^a-z0-9]+", "-", category_slug).strip("-")
            category = Category.query.filter_by(slug=category_slug).first()

            if not category:
                category = Category(name=category_name, slug=category_slug)
                db.session.add(category)
                db.session.flush()

            location = Location(
                name=name,
                slug=slug,
                city=city,
                region=region,
                image_url=image_url if image_url else None,
                description=description,
                category_id=category.id
            )
            db.session.add(location)
            db.session.commit()
            flash("Location added successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding location: {str(e)}", "error")

        return redirect(url_for("admin_dashboard"))

    users = Profile.query.order_by(Profile.created_at.desc()).all()
    locations = Location.query.order_by(Location.created_at.desc()).all()
    reviews = (
        Review.query.join(Profile, Review.user_id == Profile.id)
        .join(Location, Review.location_id == Location.id)
        .order_by(Review.created_at.desc())
        .all()
    )
    return render_template("admin_dashboard.html", users=users, locations=locations, reviews=reviews)


@app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def admin_delete_user(user_id):
    target_user = Profile.query.get_or_404(user_id)
    current = get_current_user()

    if int(current["id"]) == target_user.id:
        flash("You cannot delete your own admin account.", "error")
        return redirect(url_for("admin_dashboard"))

    try:
        db.session.delete(target_user)
        db.session.commit()
        flash("User deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting user: {str(e)}", "error")

    return redirect(url_for("admin_dashboard"))


@app.route("/admin/locations/<int:location_id>/delete", methods=["POST"])
@admin_required
def admin_delete_location(location_id):
    location = Location.query.get_or_404(location_id)
    try:
        db.session.delete(location)
        db.session.commit()
        flash("Location deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting location: {str(e)}", "error")

    return redirect(url_for("admin_dashboard"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        ensure_profile_admin_column()
        ensure_location_image_column()
        print("✓ Database tables created/verified")
    
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
