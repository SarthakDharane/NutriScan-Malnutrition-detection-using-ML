from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.patient import Patient
from app.models.report import Report


app = create_app()


@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Database initialized")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5500, debug=True)


