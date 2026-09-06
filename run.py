import os
from dotenv import load_dotenv
load_dotenv()

from app import create_app, db

app = create_app(os.environ.get("FLASK_ENV", "development"))


@app.cli.command("init-db")
def init_db():
    """Create all tables (run once against the target DB)."""
    with app.app_context():
        db.create_all()
        print("Database tables created.")


if __name__ == "__main__":
    app.run(debug=True)
