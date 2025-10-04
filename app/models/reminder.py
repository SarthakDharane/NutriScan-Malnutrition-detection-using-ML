from __future__ import annotations

from datetime import datetime
from ..extensions import db


class Reminder(db.Model):
    __tablename__ = "reminders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    report_id = db.Column(db.Integer, db.ForeignKey("reports.id"), nullable=True)
    reminder_date = db.Column(db.DateTime, nullable=False)
    reminder_type = db.Column(db.String(50), default="checkup")  # checkup, follow_up, etc.
    notes = db.Column(db.Text)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship("User", backref="reminders")
    patient = db.relationship("Patient", backref="reminders")
    report = db.relationship("Report", backref="reminders")
