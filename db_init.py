"""
Database Initialization Script
This script creates all database tables and seeds them with initial sample data.
Run this ONCE after installation to set up your local environment.

Features:
- Creates all SQLAlchemy model tables
- Prevents duplicate data insertion
- Seeds 3+ categories with 2+ locations each
- Creates an admin user account
- Provides helpful feedback during execution
"""

from app import app, db, Category, Location, Profile
from werkzeug.security import generate_password_hash


def seed_categories():
    """Create sample categories if they don't exist"""
    categories_data = [
        {
            "name": "Historical Sites",
            "slug": "historical-sites"
        },
        {
            "name": "Mountains & Nature",
            "slug": "mountains-nature"
        },
        {
            "name": "Beaches & Coastal",
            "slug": "beaches-coastal"
        },
        {
            "name": "Modern & Urban",
            "slug": "modern-urban"
        },
        {
            "name": "Religious Sites",
            "slug": "religious-sites"
        },
    ]
    
    created_count = 0
    for cat_data in categories_data:
        # Check if category already exists
        existing = Category.query.filter_by(slug=cat_data["slug"]).first()
        if existing:
            print(f"  ⊘ Category '{cat_data['name']}' already exists")
        else:
            category = Category(name=cat_data["name"], slug=cat_data["slug"])
            db.session.add(category)
            created_count += 1
    
    if created_count > 0:
        db.session.commit()
        print(f"  ✓ Created {created_count} new categories")
    
    return created_count > 0


def seed_locations():
    """Create sample locations if they don't exist"""
    # Get all categories
    categories = Category.query.all()
    if not categories:
        print("  ⚠ No categories found. Run seed_categories() first.")
        return False
    
    # Create a mapping of category slugs to location lists
    locations_by_category = {
        "historical-sites": [
            {
                "slug": "diriyah-historical-site",
                "name": "Diriyah Historical Site",
                "city": "Riyadh",
                "region": "Riyadh",
                "description": "UNESCO World Heritage Site and the former capital of the First Saudi State, featuring traditional mud-brick architecture.",
                "featured": True,
                "rating_avg": 4.7
            },
            {
                "slug": "alula-ancient-city",
                "name": "AlUla Ancient City",
                "city": "AlUla",
                "region": "Madinah",
                "description": "Ancient oasis city with stunning rock formations and historical sites dating back centuries.",
                "featured": True,
                "rating_avg": 4.8
            }
        ],
        "mountains-nature": [
            {
                "slug": "asir-national-park",
                "name": "Asir National Park",
                "city": "Abha",
                "region": "Asir",
                "description": "Saudi Arabia's most scenic mountain range with lush forests, waterfalls, and breathtaking views.",
                "featured": True,
                "rating_avg": 4.6
            },
            {
                "slug": "madain-saleh",
                "name": "Madain Saleh",
                "city": "AlUla",
                "region": "Madinah",
                "description": "Nabatean archaeological site with stunning rock-cut tombs and ancient petroglyphs.",
                "featured": False,
                "rating_avg": 4.5
            }
        ],
        "beaches-coastal": [
            {
                "slug": "corniche-jeddah",
                "name": "Jeddah Corniche",
                "city": "Jeddah",
                "region": "Makkah",
                "description": "Beautiful seaside promenade along the Red Sea with parks, restaurants, and recreational facilities.",
                "featured": True,
                "rating_avg": 4.4
            },
            {
                "slug": "farasan-islands",
                "name": "Farasan Islands",
                "city": "Jizan",
                "region": "Jizan",
                "description": "Pristine islands in the Red Sea known for pristine beaches, coral reefs, and marine life.",
                "featured": False,
                "rating_avg": 4.3
            }
        ],
        "modern-urban": [
            {
                "slug": "kingdom-tower",
                "name": "Kingdom Tower",
                "city": "Riyadh",
                "region": "Riyadh",
                "description": "Iconic skyscraper in downtown Riyadh with observation deck and shopping mall.",
                "featured": True,
                "rating_avg": 4.5
            },
            {
                "slug": "qiddiya-entertainment",
                "name": "Qiddiya Entertainment City",
                "city": "Riyadh",
                "region": "Riyadh",
                "description": "World-class entertainment destination with theme parks, sports facilities, and nature reserves.",
                "featured": True,
                "rating_avg": 4.4
            }
        ],
        "religious-sites": [
            {
                "slug": "al-masjid-al-haram",
                "name": "Al-Masjid Al-Haram",
                "city": "Mecca",
                "region": "Makkah",
                "description": "The holiest mosque in Islam, housing the Kaaba, the central place of worship for Muslims worldwide.",
                "featured": True,
                "rating_avg": 4.9
            },
            {
                "slug": "al-masjid-al-nabawi",
                "name": "Al-Masjid Al-Nabawi",
                "city": "Medina",
                "region": "Madinah",
                "description": "The second holiest mosque in Islam, built by Prophet Muhammad, featuring beautiful Islamic architecture.",
                "featured": True,
                "rating_avg": 4.8
            }
        ]
    }
    
    created_count = 0
    
    for cat in categories:
        locations = locations_by_category.get(cat.slug, [])
        
        for loc_data in locations:
            # Check if location already exists
            existing = Location.query.filter_by(slug=loc_data["slug"]).first()
            if existing:
                print(f"  ⊘ Location '{loc_data['name']}' already exists")
            else:
                location = Location(
                    slug=loc_data["slug"],
                    name=loc_data["name"],
                    city=loc_data["city"],
                    region=loc_data["region"],
                    description=loc_data["description"],
                    featured=loc_data["featured"],
                    rating_avg=loc_data["rating_avg"],
                    category_id=cat.id
                )
                db.session.add(location)
                created_count += 1
    
    if created_count > 0:
        db.session.commit()
        print(f"  ✓ Created {created_count} new locations")
    
    return created_count > 0


def seed_users():
    """Create admin and demo user accounts if they don't exist"""
    users_data = [
        {
            "email": "admin@example.com",
            "password": "admin123",
            "full_name": "Admin User",
            "nationality": "Saudi Arabia",
            "label": "Admin"
        },
        {
            "email": "demo@example.com",
            "password": "demo123",
            "full_name": "Demo User",
            "nationality": "Saudi Arabia",
            "label": "Demo"
        }
    ]
    
    created_count = 0
    
    for user_data in users_data:
        # Check if user already exists
        existing = Profile.query.filter_by(email=user_data["email"]).first()
        if existing:
            print(f"  ⊘ {user_data['label']} user already exists")
        else:
            profile = Profile(
                email=user_data["email"],
                password_hash=generate_password_hash(user_data["password"]),
                full_name=user_data["full_name"],
                nationality=user_data["nationality"]
            )
            db.session.add(profile)
            created_count += 1
    
    if created_count > 0:
        db.session.commit()
        print(f"  ✓ Created {created_count} new user accounts")
        print(f"\n  User Credentials:")
        print(f"  ├─ Email: admin@example.com | Password: admin123")
        print(f"  └─ Email: demo@example.com  | Password: demo123")
    
    return created_count > 0


def init_db():
    """Main database initialization function"""
    with app.app_context():
        print("\n" + "="*60)
        print("  DATABASE INITIALIZATION")
        print("="*60 + "\n")
        
        # Step 1: Create all tables
        print("📊 Creating database tables...")
        db.create_all()
        print("  ✓ All tables created successfully\n")
        
        # Step 2: Seed categories
        print("📂 Seeding categories...")
        seed_categories()
        print()
        
        # Step 3: Seed locations
        print("📍 Seeding locations...")
        seed_locations()
        print()
        
        # Step 4: Seed users
        print("👤 Seeding user accounts...")
        seed_users()
        print()
        
        # Summary
        print("="*60)
        print("✅ DATABASE INITIALIZATION COMPLETE!")
        print("="*60)
        print("\n🚀 Next steps:")
        print("  1. Run the app: python app.py")
        print("  2. Visit: http://127.0.0.1:5000")
        print("  3. Login with admin or demo credentials\n")


if __name__ == "__main__":
    init_db()
