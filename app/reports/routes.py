from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models.patient import Patient
from ..models.report import Report
from ..extensions import db


reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("/")
@login_required
def list_reports():
    patient_ids = [p.id for p in Patient.query.filter_by(user_id=current_user.id).all()]
    reports = Report.query.filter(Report.patient_id.in_(patient_ids)).order_by(Report.created_at.desc()).all()
    return render_template("reports/list.html", reports=reports)


@reports_bp.route("/<int:report_id>/delete", methods=["POST"])
@login_required
def delete_report(report_id: int):
    """Delete a report owned by the current user."""
    report = Report.query.get_or_404(report_id)
    patient = Patient.query.get_or_404(report.patient_id)
    if patient.user_id != current_user.id:
        flash("Access denied.", "error")
        return redirect(url_for("reports.list_reports"))
    try:
        db.session.delete(report)
        db.session.commit()
        flash("Report deleted.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to delete report: {str(e)}", "error")
    return redirect(url_for("reports.list_reports"))

