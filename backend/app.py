from pathlib import Path
import sys

from flask import Flask, abort, send_from_directory

if __package__ is None or __package__ == "":
    PROJECT_ROOT = Path(__file__).resolve().parent.parent

    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import get_db
from backend.routes.bill_routes import bill_bp
from backend.routes.dashboard_routes import dashboard_bp
from backend.routes.pantry_routes import pantry_bp
from backend.routes.sales_routes import sales_bp

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIST_DIR = BASE_DIR.parent / "frontend" / "dist"
FRONTEND_ASSETS_DIR = FRONTEND_DIST_DIR / "assets"

app = Flask(__name__)


@app.route("/")
@app.route("/<path:path>")
def index(path=""):
    if not FRONTEND_DIST_DIR.exists():
        abort(503, description="Frontend build not found. Run `npm run build` in the frontend directory.")
    requested_file = FRONTEND_DIST_DIR / path

    if path and requested_file.exists() and requested_file.is_file():
        return send_from_directory(FRONTEND_DIST_DIR, path)

    return send_from_directory(FRONTEND_DIST_DIR, "index.html")


@app.route("/assets/<path:filename>")
def frontend_assets(filename):
    return send_from_directory(FRONTEND_ASSETS_DIR, filename)


app.register_blueprint(pantry_bp)
app.register_blueprint(bill_bp)
app.register_blueprint(sales_bp)
app.register_blueprint(dashboard_bp)

if __name__ == '__main__':

    db = get_db()
    print("Database connected successfully")
    db.close()

    app.run(debug=True)
