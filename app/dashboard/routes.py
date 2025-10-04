from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from ..models.patient import Patient
from ..models.report import Report
from ..models.reminder import Reminder
from ..extensions import db
from sqlalchemy import func, desc
import random
from datetime import datetime, timedelta


dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

# Educational tips for the dashboard
NUTRITION_TIPS = [
    "🍎 Encourage your child to eat a variety of colorful fruits and vegetables daily.",
    "💧 Ensure your child drinks plenty of water throughout the day.",
    "🥛 Include calcium-rich foods like milk, cheese, and yogurt for strong bones.",
    "🥜 Add healthy fats from nuts, seeds, and avocados to support brain development.",
    "🌾 Choose whole grains over refined grains for better nutrition.",
    "🥚 Include protein-rich foods like eggs, lean meat, and beans in meals.",
    "🍊 Vitamin C from citrus fruits helps boost the immune system.",
    "🥬 Dark leafy greens are packed with iron and folate for healthy growth.",
    "🐟 Omega-3 fatty acids from fish support brain and eye development.",
    "🥕 Beta-carotene in orange vegetables supports healthy vision.",
    "🍌 Potassium-rich foods like bananas help maintain healthy blood pressure.",
    "🥜 Iron-rich foods help prevent anemia and support energy levels.",
    "🥛 Vitamin D from fortified milk helps with calcium absorption.",
    "🍓 Antioxidants in berries help protect cells from damage.",
    "🌰 Zinc from nuts and seeds supports immune function and growth."
]


@dashboard_bp.route("/")
@login_required
def index():
    # Get user's patients
    patients = Patient.query.filter_by(user_id=current_user.id).all()
    patient_ids = [p.id for p in patients]
    
    # Get all reports for user's patients
    reports = Report.query.filter(Report.patient_id.in_(patient_ids)).all()
    
    # Calculate status breakdown for pie chart
    status_counts = {}
    for report in reports:
        status = report.nutrition_status or 'Unknown'
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Get patients to watch (at risk or severe from latest reports)
    patients_to_watch = []
    for patient in patients:
        latest_report = Report.query.filter_by(patient_id=patient.id)\
            .order_by(desc(Report.created_at)).first()
        if latest_report and latest_report.nutrition_status in ['At Risk', 'Severe']:
            patients_to_watch.append({
                'patient': patient,
                'latest_report': latest_report
            })
    
    # Get random tip of the day
    tip_of_day = random.choice(NUTRITION_TIPS)
    
    # Get recent reports (last 5)
    recent_reports = Report.query.filter(Report.patient_id.in_(patient_ids))\
        .order_by(desc(Report.created_at)).limit(5).all()
    
    # Get upcoming reminders (next 7 days)
    upcoming_reminders = Reminder.query.filter(
        Reminder.user_id == current_user.id,
        Reminder.reminder_date >= datetime.utcnow(),
        Reminder.reminder_date <= datetime.utcnow() + timedelta(days=7),
        Reminder.is_completed == False
    ).order_by(Reminder.reminder_date.asc()).all()
    
    # Build full patients list with latest status for display
    all_patients_with_status = []
    for patient in patients:
        latest_report = Report.query.filter_by(patient_id=patient.id) \
            .order_by(desc(Report.created_at)).first()
        all_patients_with_status.append({
            'patient': patient,
            'latest_report': latest_report,
            'latest_status': (latest_report.nutrition_status if latest_report else 'No Reports')
        })
    
    return render_template("dashboard/index.html", 
                         user=current_user,
                         status_counts=status_counts,
                         patients_to_watch=patients_to_watch,
                         all_patients=all_patients_with_status,
                         tip_of_day=tip_of_day,
                         recent_reports=recent_reports,
                         upcoming_reminders=upcoming_reminders,
                         total_patients=len(patients),
                         total_reports=len(reports))


@dashboard_bp.route("/api/status-breakdown")
@login_required
def status_breakdown():
    """API endpoint for status breakdown data"""
    patients = Patient.query.filter_by(user_id=current_user.id).all()
    patient_ids = [p.id for p in patients]
    
    reports = Report.query.filter(Report.patient_id.in_(patient_ids)).all()
    
    status_counts = {}
    for report in reports:
        status = report.nutrition_status or 'Unknown'
        status_counts[status] = status_counts.get(status, 0) + 1
    
    return jsonify(status_counts)


@dashboard_bp.route("/api/create-reminder", methods=["POST"])
@login_required
def create_reminder():
    """Create a new reminder for a patient"""
    try:
        data = request.get_json()
        patient_id = data.get('patient_id')
        report_id = data.get('report_id')
        reminder_date_str = data.get('reminder_date')
        notes = data.get('notes', '')
        
        # Validate patient ownership
        patient = Patient.query.filter_by(id=patient_id, user_id=current_user.id).first()
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
        
        # Parse reminder date
        reminder_date = datetime.fromisoformat(reminder_date_str.replace('Z', '+00:00'))
        
        # Create reminder
        reminder = Reminder(
            user_id=current_user.id,
            patient_id=patient_id,
            report_id=report_id,
            reminder_date=reminder_date,
            notes=notes
        )
        
        db.session.add(reminder)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'reminder_id': reminder.id,
            'message': 'Reminder created successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route("/api/complete-reminder/<int:reminder_id>", methods=["POST"])
@login_required
def complete_reminder(reminder_id):
    """Mark a reminder as completed"""
    try:
        reminder = Reminder.query.filter_by(
            id=reminder_id, 
            user_id=current_user.id
        ).first()
        
        if not reminder:
            return jsonify({'error': 'Reminder not found'}), 404
        
        reminder.is_completed = True
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Reminder marked as completed'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500



@dashboard_bp.route("/api/delete-patient/<int:patient_id>", methods=["POST"])
@login_required
def delete_patient(patient_id: int):
    """Delete a patient owned by the current user, along with their reports and reminders."""
    try:
        patient = Patient.query.filter_by(id=patient_id, user_id=current_user.id).first()
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404

        # Delete reminders linked to this patient (including those linked to any reports)
        Reminder.query.filter_by(patient_id=patient.id).delete(synchronize_session=False)

        # Delete reports for this patient
        Report.query.filter_by(patient_id=patient.id).delete(synchronize_session=False)

        # Finally delete the patient
        db.session.delete(patient)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Patient deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

