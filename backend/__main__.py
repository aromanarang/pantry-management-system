from backend.app import app, get_db


if __name__ == "__main__":
    db = get_db()
    print("Database connected successfully")
    db.close()
    app.run(debug=True)
