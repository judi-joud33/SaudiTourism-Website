"""
Seed the local SQLite database for the Saudi Tourism Website.

This script:
- creates all tables with app.app_context()
- creates 4 core categories
- creates 8+ Saudi locations assigned to those categories
- creates a test user with a hashed password
- creates sample reviews and updates rating averages
- avoids duplicates when re-running
"""

from app import app, db, Profile, Category, Location, Review, ensure_profile_admin_column, ensure_location_image_column
from werkzeug.security import generate_password_hash


def create_tables():
    db.create_all()
    ensure_profile_admin_column()
    ensure_location_image_column()
    print("✓ Tables created/verified")


def seed_categories():
    categories = [
        {"name": "Historic Sites", "slug": "historic-sites"},
        {"name": "Modern Landmarks", "slug": "modern-landmarks"},
        {"name": "Natural Wonders", "slug": "natural-wonders"},
        {"name": "Cultural Experiences", "slug": "cultural-experiences"},
    ]

    created = 0
    for cat in categories:
        existing = Category.query.filter_by(slug=cat["slug"]).first()
        if existing:
            print(f"  ⊘ Category already exists: {cat['name']}")
        else:
            db.session.add(Category(name=cat["name"], slug=cat["slug"]))
            created += 1
    if created:
        db.session.commit()
    print(f"✓ Categories seeded ({created} new)")


def seed_locations():
    location_definitions = [
        {
            "slug": "diriyah-historical-site",
            "name": "Diriyah Historical Site",
            "city": "Riyadh",
            "region": "Riyadh",
            "image_url": "https://images.unsplash.com/photo-1467269204594-9661b134dd2b?auto=format&fit=crop&w=1400&q=80",
            "description": "A restored mud-brick city and UNESCO World Heritage site, celebrating Saudi Arabia's early history.",
            "category_slug": "historic-sites",
            "featured": True,
        },
        {
            "slug": "alula-heritage-village",
            "name": "AlUla Heritage Village",
            "city": "AlUla",
            "region": "Madinah",
            "image_url": "https://images.unsplash.com/photo-1682686580391-615b1f28e1b8?auto=format&fit=crop&w=1400&q=80",
            "description": "An ancient oasis city with rock formations, tombs, and living heritage attractions.",
            "category_slug": "historic-sites",
            "featured": True,
        },
        {
            "slug": "neom-coast",
            "name": "NEOM Coastal Zone",
            "city": "NEOM",
            "region": "Tabuk",
            "image_url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1400&q=80",
            "description": "A futuristic coastal destination blending sustainable design, luxury resorts, and marine activities.",
            "category_slug": "modern-landmarks",
            "featured": True,
        },
        {
            "slug": "boulevard-city-riyadh",
            "name": "Boulevard City Riyadh",
            "city": "Riyadh",
            "region": "Riyadh",
            "image_url": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=1400&q=80",
            "description": "A large entertainment and leisure district with shopping, dining, and nightly events.",
            "category_slug": "modern-landmarks",
            "featured": False,
        },
        {
            "slug": "elephant-rock-jeddah",
            "name": "Elephant Rock",
            "city": "Jeddah",
            "region": "Makkah",
            "image_url": "https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=1400&q=80",
            "description": "A dramatic natural sandstone formation on the Red Sea coast, shaped like an elephant.",
            "category_slug": "natural-wonders",
            "featured": True,
        },
        {
            "slug": "red-sea-project",
            "name": "The Red Sea Project",
            "city": "Umluj",
            "region": "Tabuk",
            "image_url": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?auto=format&fit=crop&w=1400&q=80",
            "description": "A luxury island and coral reef destination offering diving, beaches, and desert adventure.",
            "category_slug": "natural-wonders",
            "featured": False,
        },
        {
            "slug": "al-balad-jeddah",
            "name": "Al-Balad Jeddah",
            "city": "Jeddah",
            "region": "Makkah",
            "image_url": "https://images.unsplash.com/photo-1467269204594-9661b134dd2b?auto=format&fit=crop&w=1400&q=80",
            "description": "The historic old town of Jeddah, famous for its narrow alleys, coral stone buildings, and cultural markets.",
            "category_slug": "cultural-experiences",
            "featured": False,
        },
        {
            "slug": "green-dome-medina",
            "name": "Islamic Heritage Trail",
            "city": "Medina",
            "region": "Madinah",
            "image_url": "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=1400&q=80",
            "description": "A cultural route connecting historic sites, mosques, and heritage landmarks through the heart of Medina.",
            "category_slug": "cultural-experiences",
            "featured": False,
        },
    ]

    created = 0
    for location in location_definitions:
        existing = Location.query.filter_by(slug=location["slug"]).first()
        if existing:
            if not existing.image_url and location.get("image_url"):
                existing.image_url = location["image_url"]
                db.session.commit()
                print(f"  ↺ Updated image for existing location: {location['name']}")
            else:
                print(f"  ⊘ Location already exists: {location['name']}")
            continue

        category = Category.query.filter_by(slug=location["category_slug"]).first()
        if not category:
            print(f"  ⚠ Missing category for location: {location['name']}")
            continue

        loc = Location(
            slug=location["slug"],
            name=location["name"],
            city=location["city"],
            region=location["region"],
            image_url=location.get("image_url"),
            description=location["description"],
            featured=location["featured"],
            category_id=category.id,
            rating_avg=0.0,
        )
        db.session.add(loc)
        created += 1

    if created:
        db.session.commit()
    print(f"✓ Locations seeded ({created} new)")


def seed_test_user():
    email = "testuser@example.com"
    existing = Profile.query.filter_by(email=email).first()
    if existing:
        print(f"  ⊘ Test user already exists: {email}")
        return existing

    user = Profile(
        email=email,
        password_hash=generate_password_hash("test1234"),
        full_name="Test User",
        nationality="Saudi Arabia",
    )
    db.session.add(user)
    db.session.commit()
    print(f"✓ Created test user: {email}")
    return user


def seed_reviews(user):
    sample_reviews = [
        {
            "location_slug": "diriyah-historical-site",
            "rating": 5,
            "title": "A captivating journey into Saudi history",
            "body": "The restoration of Diriyah is beautiful and the guided route is easy to follow.",
            "visit_date": "2025-10-12",
        },
        {
            "location_slug": "alula-heritage-village",
            "rating": 4,
            "title": "Stunning desert heritage",
            "body": "AlUla is magnificent at sunset and the historic sites are unforgettable.",
            "visit_date": "2025-11-05",
        },
        {
            "location_slug": "neom-coast",
            "rating": 4,
            "title": "Futuristic coastal vision",
            "body": "NEOM feels like a modern wonder, with impressive seaside planning.",
            "visit_date": "2026-01-18",
        },
        {
            "location_slug": "elephant-rock-jeddah",
            "rating": 5,
            "title": "Absolutely iconic",
            "body": "Elephant Rock is one of the most unique natural sights in the region.",
            "visit_date": "2025-09-22",
        },
    ]

    created = 0
    for review_data in sample_reviews:
        location = Location.query.filter_by(slug=review_data["location_slug"]).first()
        if not location:
            print(f"  ⚠ Location not found for review: {review_data['location_slug']}")
            continue

        existing = Review.query.filter_by(
            location_id=location.id,
            user_id=user.id,
            title=review_data["title"],
        ).first()
        if existing:
            print(f"  ⊘ Review already exists for {location.name}: '{review_data['title']}'")
            continue

        review = Review(
            location_id=location.id,
            user_id=user.id,
            rating=review_data["rating"],
            title=review_data["title"],
            body=review_data["body"],
            visit_date=review_data["visit_date"],
        )
        db.session.add(review)
        created += 1

    if created:
        db.session.commit()
        print(f"✓ Created {created} sample reviews")

        # Update rating_avg for reviewed locations
        updated = 0
        for review_data in sample_reviews:
            location = Location.query.filter_by(slug=review_data["location_slug"]).first()
            if location:
                location.update_rating()
                updated += 1
        print(f"✓ Updated rating_avg for {updated} locations")
    else:
        print("✓ No new reviews were added")


def main():
    with app.app_context():
        print("Starting seed_db.py...")
        create_tables()
        seed_categories()
        seed_locations()
        user = seed_test_user()
        seed_reviews(user)
        print("Database seeding complete.")
        print("Test user credentials: testuser@example.com / test1234")


if __name__ == "__main__":
    main()
