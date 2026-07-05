import os

from app import create_app
from app.db_init import database_is_initialized, init_database

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        if not database_is_initialized():
            print("Database tables not found. Initializing...")
            init_database(
                seed_sample_doctors=os.environ.get("SEED_SAMPLE_DOCTORS", "0") == "1"
            )

    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    port = int(os.environ.get("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=debug)
