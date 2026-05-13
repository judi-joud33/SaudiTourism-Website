# SQLite Migration Guide

This guide explains the migration from Supabase to SQLite with Flask-SQLAlchemy.

## What Changed

### 1. **Dependencies** (requirements.txt)

- ❌ Removed: `supabase==2.13.0`
- ✅ Added: `Flask-SQLAlchemy==3.1.1`

### 2. **Database Configuration** (app.py)

- Replaced Supabase client initialization with SQLAlchemy ORM
- Local SQLite database: `site.db` (created automatically in project root)
- No more environment variables needed for Supabase (SUPABASE_URL, SUPABASE_KEY)

### 3. **Database Models**

Created SQLAlchemy models for all tables:

```python
- Profile: User accounts with email, password hash, full name, nationality
- Category: Location categories (Historical, Mountains, Beaches, etc.)
- Location: Tourism locations with details and ratings
- Review: User reviews for locations
- Favorite: User favorites tracking
```

### 4. **All Database Queries Updated**

- Changed from Supabase SDK calls to SQLAlchemy ORM queries
- Example:

  ```python
  # OLD (Supabase)
  get_supabase().table("profiles").select("*").eq("email", email).execute()

  # NEW (SQLAlchemy)
  Profile.query.filter_by(email=email).first()
  ```

## Setup Instructions

### Step 1: Install Dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Step 2: Initialize Database

```bash
python db_init.py
```

This script will:

- ✓ Create all database tables
- ✓ Create sample categories (5 types)
- ✓ Create sample locations (3 popular sites)
- ✓ Create a demo user account

**Demo Account:**

- Email: `demo@example.com`
- Password: `demo123`

### Step 3: Run the Application

```bash
python app.py
```

The app runs on: `http://127.0.0.1:5000`

## Database Schema

### profiles table

```
- id (INTEGER PRIMARY KEY)
- email (VARCHAR UNIQUE)
- password_hash (VARCHAR)
- full_name (VARCHAR)
- nationality (VARCHAR)
- created_at (DATETIME)
```

### categories table

```
- id (INTEGER PRIMARY KEY)
- name (VARCHAR)
- slug (VARCHAR UNIQUE)
```

### locations table

```
- id (INTEGER PRIMARY KEY)
- slug (VARCHAR UNIQUE)
- name (VARCHAR)
- city (VARCHAR)
- region (VARCHAR)
- description (TEXT)
- featured (BOOLEAN)
- rating_avg (FLOAT)
- category_id (FOREIGN KEY → categories)
- created_at (DATETIME)
```

### reviews table

```
- id (INTEGER PRIMARY KEY)
- location_id (FOREIGN KEY → locations)
- user_id (FOREIGN KEY → profiles)
- rating (INTEGER 1-5)
- title (VARCHAR)
- body (TEXT)
- visit_date (VARCHAR)
- created_at (DATETIME)
```

### favorites table

```
- id (INTEGER PRIMARY KEY)
- user_id (FOREIGN KEY → profiles)
- location_id (FOREIGN KEY → locations)
- created_at (DATETIME)
- UNIQUE(user_id, location_id)
```

## Key Features

✅ **Auto-rating calculation**: Average rating updates automatically when reviews are submitted
✅ **Cascade deletes**: Deleting a user removes their reviews and favorites automatically
✅ **Index optimization**: Email and slug fields are indexed for faster queries
✅ **Unique constraints**: Prevents duplicate emails and user-location combinations

## Troubleshooting

### Database Not Created

If `site.db` is not created, run:

```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### Want to Reset Database

Delete `site.db` and run `db_init.py` again:

```bash
del site.db
python db_init.py
```

### Adding More Sample Data

Edit `db_init.py` and add more Category, Location, or Profile objects in the respective sections.

## Additional Notes

- No need to update `.env` file (Supabase variables are no longer used)
- Templates remain unchanged - models return the same data structure
- All validation logic remains the same
- Error handling has been updated to use SQLAlchemy exceptions
