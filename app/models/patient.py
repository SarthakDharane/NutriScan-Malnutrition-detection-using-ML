from __future__ import annotations

from ..extensions import db


class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    child_name = db.Column(db.String(120), nullable=False)
    age_months = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    height_cm = db.Column(db.Float, nullable=False)
    weight_kg = db.Column(db.Float, nullable=False)

    reports = db.relationship("Report", backref="patient", lazy=True)

    @property
    def bmi(self) -> float:
        height_m = (self.height_cm or 0) / 100.0
        if height_m <= 0:
            return 0.0
        return (self.weight_kg or 0.0) / (height_m * height_m)


