from __future__ import annotations

from datetime import datetime
from ..extensions import db


class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Basic predictions
    skin_pred = db.Column(db.String(50))
    nail_pred = db.Column(db.String(50))
    nutrition_status = db.Column(db.String(50))  # Normal, At Risk, Moderate, Severe
    notes = db.Column(db.Text)

    # Image paths
    skin_image_path = db.Column(db.String(255))
    nail_image_path = db.Column(db.String(255))
    
    # Advanced reporting fields
    skin_severity = db.Column(db.String(20))  # Mild, Moderate, Severe
    nail_severity = db.Column(db.String(20))  # Mild, Moderate, Severe
    skin_confidence = db.Column(db.Float)  # 0.0 to 1.0
    nail_confidence = db.Column(db.Float)  # 0.0 to 1.0
    
    # WHO standards
    bmi_percentile = db.Column(db.Float)  # WHO percentile (0-100)
    bmi_z_score = db.Column(db.Float)  # WHO z-score
    bmi_category = db.Column(db.String(20))  # Underweight, Normal, Overweight, Obese
    
    # Malnutrition risk assessment
    malnutrition_risk_score = db.Column(db.Integer)  # 0-100
    risk_level = db.Column(db.String(20))  # Low, Medium, High, Critical
    
    # Recommendations
    dietary_recommendations = db.Column(db.Text)
    lifestyle_recommendations = db.Column(db.Text)
    hydration_tips = db.Column(db.Text)
    professional_consultation = db.Column(db.Boolean, default=False)


