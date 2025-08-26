from app import create_app, db
import os
import webbrowser
from threading import Timer

# Change to production for deployment
app = create_app("production")  # ✅ Use production, not development

def open_browser():
    # Optional: Only open browser on laptop, not phone
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Creates tables if they don’t exist

    # Optional: Remove Timer if you don’t want auto-open
    Timer(1, open_browser).start()

    # ✅ Make the app visible on your phone
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
