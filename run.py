from app import create_app, db
import os

app = create_app("production")

if __name__ == "__main__":
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables created successfully")
        except Exception as e:
            print(f"❌ Database error: {e}")
    
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)