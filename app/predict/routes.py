import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models.patient import Patient
from app.models.report import Report
from app.extensions import db
from app.predict.model import get_predictor, predict_nail, predict_skin
from app.predict.who_standards import WHOStandards, MalnutritionRiskAssessment
from app.predict.chatbot import MalnutritionChatbot
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

predict_bp = Blueprint('predict', __name__, url_prefix='/predict')

UPLOAD_FOLDER = 'app/static/uploads'
PLOTS_FOLDER = 'app/static/plots'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PLOTS_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_bmi_chart(patient_id, height, weight, age, gender):
    """Generate enhanced BMI chart with WHO standards"""
    try:
        # Calculate BMI
        height_m = height / 100
        bmi = weight / (height_m ** 2)
        
        # Get WHO data
        gender_data = WHOStandards.BMI_REFERENCE_DATA[gender.lower()]
        ages = np.array(gender_data['ages'])
        
        # Create BMI chart with proper backend
        plt.switch_backend('Agg')  # Ensure we're using the correct backend
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Plot WHO reference curves
        ax.plot(ages, gender_data['p3'], 'r--', label='3rd percentile (WHO)', alpha=0.7, linewidth=2)
        ax.plot(ages, gender_data['p5'], 'orange', label='5th percentile (WHO)', alpha=0.7, linewidth=2)
        ax.plot(ages, gender_data['p25'], 'yellow', label='25th percentile (WHO)', alpha=0.7, linewidth=2)
        ax.plot(ages, gender_data['p50'], 'green', label='50th percentile (WHO)', alpha=0.7, linewidth=2)
        ax.plot(ages, gender_data['p75'], 'lightblue', label='75th percentile (WHO)', alpha=0.7, linewidth=2)
        ax.plot(ages, gender_data['p95'], 'blue', label='95th percentile (WHO)', alpha=0.7, linewidth=2)
        ax.plot(ages, gender_data['p97'], 'purple', label='97th percentile (WHO)', alpha=0.7, linewidth=2)
        
        # Plot patient's BMI
        ax.scatter(age, bmi, color='red', s=150, label=f'Patient BMI: {bmi:.1f}', zorder=5)
        
        # Color coding based on BMI status
        if bmi < 18.5:
            ax.axhspan(0, 18.5, alpha=0.2, color='red', label='Underweight Zone')
        elif bmi < 25:
            ax.axhspan(18.5, 25, alpha=0.2, color='green', label='Normal Weight Zone')
        else:
            ax.axhspan(25, 35, alpha=0.2, color='orange', label='Overweight Zone')
        
        ax.set_xlabel('Age (years)', fontsize=12)
        ax.set_ylabel('BMI (kg/m²)', fontsize=12)
        ax.set_title(f'BMI-for-Age Chart - Patient {patient_id}\nWHO Growth Standards Reference', fontsize=14, fontweight='bold')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        ax.set_xlim(2, 19)
        ax.set_ylim(10, 30)
        
        # Save chart
        chart_path = os.path.join(PLOTS_FOLDER, f'bmi_{patient_id}.png')
        fig.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close(fig)  # Close the figure properly
        
        return f'bmi_{patient_id}.png'
    except Exception as e:
        print(f"Error generating BMI chart: {e}")
        import traceback
        traceback.print_exc()
        return None

def determine_severity(prediction, confidence):
    """Determine severity level based on prediction and confidence"""
    if 'unhealthy' in prediction:
        # Higher confidence in an unhealthy prediction implies more severe concern
        if confidence >= 0.8:
            return "Severe"
        elif confidence >= 0.6:
            return "Moderate"
        else:
            return "Mild"
    else:
        if confidence < 0.7:
            return "Mild"  # Low confidence in healthy prediction
        else:
            return "Normal"

def simple_image_heuristic(image_path):
    """Simple heuristic for image analysis as fallback"""
    try:
        from PIL import Image
        import numpy as np
        
        img = Image.open(image_path).convert('HSV')
        img_array = np.array(img)
        
        # Analyze saturation and value channels
        avg_saturation = np.mean(img_array[:, :, 1])
        avg_value = np.mean(img_array[:, :, 2])
        
        # Simple rules for health assessment
        if avg_saturation < 50 and avg_value < 100:
            return "unhealthy", 0.8
        elif avg_saturation > 100 and avg_value > 150:
            return "healthy", 0.7
        else:
            return "healthy", 0.6
            
    except Exception as e:
        print(f"Error in heuristic analysis: {e}")
        return "healthy", 0.5

@predict_bp.route('/', methods=['GET', 'POST'])
@login_required
def predict():
    if request.method == 'POST':
        try:
            # Get form data (support both old and new field names)
            child_name = request.form.get('child_name', '').strip()
            gender = request.form.get('gender', '').strip()

            # Age handling: prefer months if provided, convert to years for charts
            age_months_val = request.form.get('age_months')
            age_years_val = request.form.get('age')
            if age_months_val:
                age = float(age_months_val) / 12.0
            elif age_years_val:
                age = float(age_years_val)
            else:
                raise ValueError('Age is required')

            # Height and weight handling
            height_val = request.form.get('height_cm') or request.form.get('height')
            weight_val = request.form.get('weight_kg') or request.form.get('weight')
            if not height_val or not weight_val:
                raise ValueError('Height and Weight are required')
            height = float(height_val)
            weight = float(weight_val)
            
            # Validate inputs
            if age < 0 or age > 18 or height < 30 or height > 220 or weight < 1 or weight > 200:
                flash('Invalid input values. Please check age, height, and weight.', 'error')
                return render_template('predict/form.html')
            
            # Check if files were uploaded
            if 'skin_image' not in request.files or 'nail_image' not in request.files:
                flash('Please upload both skin and nail images.', 'error')
                return render_template('predict/form.html')
            
            skin_file = request.files['skin_image']
            nail_file = request.files['nail_image']
            
            if skin_file.filename == '' or nail_file.filename == '':
                flash('Please select both skin and nail images.', 'error')
                return render_template('predict/form.html')
            if not allowed_file(skin_file.filename) or not allowed_file(nail_file.filename):
                flash('Unsupported file type. Please upload images only.', 'error')
                return render_template('predict/form.html')
            
            # Create patient record (persist months/cm/kg as per model schema)
            computed_age_months = int(round(age * 12.0))
            patient = Patient(
                user_id=current_user.id,
                child_name=child_name,
                age_months=computed_age_months,
                gender=gender,
                height_cm=height,
                weight_kg=weight
            )
            db.session.add(patient)
            db.session.commit()
            
            # Save uploaded images
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
            
            skin_filename = f"skin_{patient.id}_{timestamp}_{secure_filename(skin_file.filename)}"
            nail_filename = f"nail_{patient.id}_{timestamp}_{secure_filename(nail_file.filename)}"
            
            skin_path = os.path.join(UPLOAD_FOLDER, skin_filename)
            nail_path = os.path.join(UPLOAD_FOLDER, nail_filename)
            
            skin_file.save(skin_path)
            nail_file.save(nail_path)
            
            # Generate enhanced BMI chart
            bmi_chart = generate_bmi_chart(patient.id, height, weight, age, gender)
            
            # Get predictions using pretrained CNN feature extractors
            try:
                skin_pred, skin_conf = predict_skin(skin_path)
                nail_pred, nail_conf = predict_nail(nail_path)
            except Exception as e:
                print(f"Error with pretrained models: {e}")
                # Fallback to heuristic
                skin_pred, skin_conf = simple_image_heuristic(skin_path)
                nail_pred, nail_conf = simple_image_heuristic(nail_path)
            
            # Calculate WHO standards
            bmi = patient.bmi
            try:
                bmi_percentile, bmi_z_score = WHOStandards.calculate_bmi_percentile_and_zscore(age, bmi, gender)
                bmi_category = WHOStandards.get_bmi_category(bmi, age, gender)
            except Exception as e:
                print(f"Error calculating WHO standards: {e}")
                # Fallback values
                bmi_percentile = 50.0
                bmi_z_score = 0.0
                bmi_category = "Normal"
            
            # Determine severity levels
            skin_severity = determine_severity(skin_pred, skin_conf)
            nail_severity = determine_severity(nail_pred, nail_conf)
            
            # Calculate malnutrition risk score
            risk_assessment = MalnutritionRiskAssessment.calculate_risk_score(
                bmi_percentile, bmi_z_score, skin_pred, nail_pred, 
                skin_conf, nail_conf, age
            )
            
            # Generate recommendations
            recommendations = MalnutritionRiskAssessment.generate_recommendations(
                risk_assessment, bmi_category
            )
            
            # Determine overall nutrition status
            if risk_assessment['risk_level'] == 'Critical':
                nutrition_status = "Severe"
            elif risk_assessment['risk_level'] == 'High':
                nutrition_status = "Moderate"
            elif risk_assessment['risk_level'] == 'Medium':
                nutrition_status = "At Risk"
            elif "unhealthy" in skin_pred or "unhealthy" in nail_pred:
                nutrition_status = "At Risk"
            else:
                nutrition_status = "Normal"
            
            # Create comprehensive report
            notes = f"BMI chart: {bmi_chart}" if bmi_chart else None
            report = Report(
                patient_id=patient.id,
                skin_pred=skin_pred,
                nail_pred=nail_pred,
                nutrition_status=nutrition_status,
                notes=notes,
                skin_image_path=skin_filename,
                nail_image_path=nail_filename,
                
                # Advanced reporting fields
                skin_severity=skin_severity,
                nail_severity=nail_severity,
                skin_confidence=skin_conf,
                nail_confidence=nail_conf,
                
                # WHO standards
                bmi_percentile=bmi_percentile,
                bmi_z_score=bmi_z_score,
                bmi_category=bmi_category,
                
                # Malnutrition risk assessment
                malnutrition_risk_score=risk_assessment['risk_score'],
                risk_level=risk_assessment['risk_level'],
                
                # Recommendations
                dietary_recommendations=recommendations['dietary_recommendations'],
                lifestyle_recommendations=recommendations['lifestyle_recommendations'],
                hydration_tips=recommendations['hydration_tips'],
                professional_consultation=recommendations['professional_consultation']
            )
            db.session.add(report)
            db.session.commit()
            
            return redirect(url_for('predict.result', report_id=report.id))
            
        except Exception as e:
            flash(f'Error processing prediction: {str(e)}', 'error')
            return render_template('predict/form.html')
    
    return render_template('predict/form.html')

@predict_bp.route('/result/<int:report_id>')
@login_required
def result(report_id):
    report = Report.query.get_or_404(report_id)
    patient = Patient.query.get_or_404(report.patient_id)
    
    # Ensure user can only see their own reports
    if patient.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Build BMI chart URL if present
    plot_filename = f"bmi_{patient.id}.png"
    plot_url = url_for('static', filename=f'plots/{plot_filename}')
    
    return render_template('predict/result.html', report=report, patient=patient, plot_url=plot_url)

@predict_bp.route('/chatbot', methods=['POST'])
@login_required
def chatbot():
    """Chatbot API endpoint using the previous rule-based assistant"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        report_id = data.get('report_id')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Initialize chatbot
        bot = MalnutritionChatbot()
        
        # Get report context if provided
        report_data = None
        if report_id:
            report = Report.query.get_or_404(report_id)
            patient = Patient.query.get_or_404(report.patient_id)
            
            # Ensure user can only access their own reports
            if patient.user_id != current_user.id:
                return jsonify({'error': 'Access denied'}), 403
            
            report_data = {
                'report': {
                    'nutrition_status': report.nutrition_status,
                    'skin_pred': report.skin_pred,
                    'nail_pred': report.nail_pred,
                    'bmi_category': report.bmi_category,
                    'bmi_percentile': report.bmi_percentile,
                    'bmi_z_score': report.bmi_z_score,
                    'malnutrition_risk_score': report.malnutrition_risk_score,
                    'risk_level': report.risk_level,
                    'dietary_recommendations': report.dietary_recommendations,
                    'lifestyle_recommendations': report.lifestyle_recommendations,
                    'hydration_tips': report.hydration_tips,
                    'professional_consultation': report.professional_consultation
                },
                'patient': {
                    'child_name': patient.child_name,
                    'age_months': patient.age_months,
                    'bmi': patient.bmi
                }
            }
        
        # Process message
        response = bot.process_message(message, report_data)
        
        return jsonify({
            'response': response,
            'conversation_history': bot.get_conversation_history()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@predict_bp.route('/api/predict', methods=['POST'])
def api_predict():
    """REST API endpoint for predictions"""
    # This would be implemented for mobile app integration
    pass

@predict_bp.route('/export_pdf/<int:report_id>')
@login_required
def export_pdf(report_id):
    """Export report as PDF"""
    try:
        report = Report.query.get_or_404(report_id)
        patient = Patient.query.get_or_404(report.patient_id)
        
        # Ensure user can only export their own reports
        if patient.user_id != current_user.id:
            flash('Access denied.', 'error')
            return redirect(url_for('dashboard.index'))
        
        # Create PDF
        response = make_response()
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=nutriscan_report_{patient.child_name}_{report.created_at.strftime("%Y%m%d")}.pdf'
        
        # Generate PDF content
        pdf_content = generate_pdf_report(report, patient)
        response.data = pdf_content
        
        return response
        
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('predict.result', report_id=report_id))

def generate_pdf_report(report, patient):
    """Generate comprehensive PDF report using ReportLab with all content from result.html"""
    from io import BytesIO
    import os
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#007bff')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.HexColor('#495057')
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=14,
        spaceAfter=8,
        textColor=colors.HexColor('#6c757d')
    )
    
    # Build PDF content
    story = []
    
    # Title
    story.append(Paragraph("NutriScan Malnutrition Analysis Report", title_style))
    story.append(Paragraph("Comprehensive malnutrition analysis with WHO standards and AI-powered insights", 
                          ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=12, alignment=TA_CENTER, textColor=colors.grey)))
    story.append(Spacer(1, 20))
    
    # Risk Assessment Overview
    story.append(Paragraph("Malnutrition Risk Assessment", heading_style))
    
    # Risk level with visual indicator
    risk_level = report.risk_level or 'Low'
    risk_score = report.malnutrition_risk_score or 0
    bmi_percentile = report.bmi_percentile or 50
    bmi_z_score = report.bmi_z_score or 0
    
    risk_data = [
        ['Risk Level:', risk_level],
        ['Risk Score:', f"{risk_score}/100"],
        ['WHO Percentile:', f"{bmi_percentile:.1f}%"],
        ['Z-Score:', f"{bmi_z_score:.2f}"]
    ]
    
    risk_table = Table(risk_data, colWidths=[2*inch, 3*inch])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#fff3cd')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(risk_table)
    story.append(Spacer(1, 20))
    
    # Overall Status
    story.append(Paragraph("Overall Nutrition Status", heading_style))
    nutrition_status = report.nutrition_status or 'Unknown'
    status_text = f"Based on comprehensive analysis of BMI, skin, and nail health: {nutrition_status}"
    story.append(Paragraph(status_text, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Patient Information
    story.append(Paragraph("Patient Information", heading_style))
    patient_data = [
        ['Name:', patient.child_name],
        ['Gender:', patient.gender.title()],
        ['Age:', f"{patient.age_months / 12:.1f} years ({patient.age_months} months)"],
        ['Height:', f"{patient.height_cm:.1f} cm"],
        ['Weight:', f"{patient.weight_kg:.1f} kg"],
        ['BMI:', f"{patient.bmi:.2f}"],
        ['BMI Category:', report.bmi_category or 'Unknown']
    ]
    
    patient_table = Table(patient_data, colWidths=[2*inch, 3*inch])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(patient_table)
    story.append(Spacer(1, 20))
    
    # Image Analysis Results
    story.append(Paragraph("Image Analysis Results", heading_style))
    
    # Skin Analysis
    story.append(Paragraph("Skin Health Analysis", subheading_style))
    skin_pred = report.skin_pred.replace('_', ' ').title() if report.skin_pred else 'Unknown'
    skin_severity = report.skin_severity or 'Normal'
    skin_confidence = (report.skin_confidence or 0.5) * 100
    
    skin_data = [
        ['Prediction:', skin_pred],
        ['Severity:', skin_severity],
        ['Confidence:', f"{skin_confidence:.1f}%"]
    ]
    
    skin_table = Table(skin_data, colWidths=[2*inch, 3*inch])
    skin_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8d7da')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(skin_table)
    
    # Add skin image if available
    if report.skin_image_path:
        skin_image_path = os.path.join('app', 'static', 'uploads', report.skin_image_path)
        if os.path.exists(skin_image_path):
            try:
                skin_img = Image(skin_image_path, width=3*inch, height=2*inch)
                story.append(Spacer(1, 10))
                story.append(skin_img)
            except:
                pass  # Skip image if there's an error
    
    story.append(Spacer(1, 15))
    
    # Nail Analysis
    story.append(Paragraph("Nail Health Analysis", subheading_style))
    nail_pred = report.nail_pred.replace('_', ' ').title() if report.nail_pred else 'Unknown'
    nail_severity = report.nail_severity or 'Normal'
    nail_confidence = (report.nail_confidence or 0.5) * 100
    
    nail_data = [
        ['Prediction:', nail_pred],
        ['Severity:', nail_severity],
        ['Confidence:', f"{nail_confidence:.1f}%"]
    ]
    
    nail_table = Table(nail_data, colWidths=[2*inch, 3*inch])
    nail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#d4edda')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(nail_table)
    
    # Add nail image if available
    if report.nail_image_path:
        nail_image_path = os.path.join('app', 'static', 'uploads', report.nail_image_path)
        if os.path.exists(nail_image_path):
            try:
                nail_img = Image(nail_image_path, width=3*inch, height=2*inch)
                story.append(Spacer(1, 10))
                story.append(nail_img)
            except:
                pass  # Skip image if there's an error
    
    story.append(Spacer(1, 20))
    
    # WHO Standards Chart
    story.append(Paragraph("BMI-for-Age Growth Chart (WHO Standards)", heading_style))
    
    # Add BMI chart if available
    plot_filename = f"bmi_{patient.id}.png"
    plot_path = os.path.join('app', 'static', 'plots', plot_filename)
    if os.path.exists(plot_path):
        try:
            bmi_chart = Image(plot_path, width=6*inch, height=4*inch)
            story.append(bmi_chart)
        except:
            story.append(Paragraph("BMI chart not available", styles['Normal']))
    else:
        story.append(Paragraph("BMI chart not available", styles['Normal']))
    
    # WHO Standards Summary
    who_summary_data = [
        ['Your Child\'s BMI:', f"{patient.bmi:.1f}"],
        ['WHO Percentile:', f"{bmi_percentile:.1f}%"],
        ['Z-Score:', f"{bmi_z_score:.2f}"],
        ['Category:', report.bmi_category or 'Unknown']
    ]
    
    who_summary_table = Table(who_summary_data, colWidths=[2*inch, 3*inch])
    who_summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#d1ecf1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(Spacer(1, 15))
    story.append(who_summary_table)
    story.append(Spacer(1, 20))
    
    # Personalized Recommendations
    story.append(Paragraph("Personalized Recommendations", heading_style))
    
    if report.dietary_recommendations:
        story.append(Paragraph("Dietary Recommendations", subheading_style))
        story.append(Paragraph(report.dietary_recommendations, styles['Normal']))
        story.append(Spacer(1, 12))
    
    if report.lifestyle_recommendations:
        story.append(Paragraph("Lifestyle Recommendations", subheading_style))
        story.append(Paragraph(report.lifestyle_recommendations, styles['Normal']))
        story.append(Spacer(1, 12))
    
    if report.hydration_tips:
        story.append(Paragraph("Hydration Tips", subheading_style))
        story.append(Paragraph(report.hydration_tips, styles['Normal']))
        story.append(Spacer(1, 12))
    
    # Professional consultation notice
    if report.professional_consultation:
        story.append(Paragraph("Important Notice", subheading_style))
        story.append(Paragraph(
            "Based on this assessment, consulting a healthcare professional is recommended for further evaluation and guidance.",
            styles['Normal']
        ))
        story.append(Spacer(1, 20))
    
    # Digital Skin & Nail Health Analysis Report
    story.append(Paragraph("Digital Skin & Nail Health Analysis Report", heading_style))
    
    # Report metadata
    report_metadata = [
        ['Patient Name:', patient.child_name],
        ['Age:', f"{patient.age_months / 12:.1f} years"],
        ['Gender:', patient.gender.title()],
        ['Date of Report:', report.created_at.strftime('%Y-%m-%d') if report.created_at else ''],
        ['Report ID:', f"SKN-{patient.id:04d}-{report.id:04d}"]
    ]
    
    report_metadata_table = Table(report_metadata, colWidths=[2*inch, 3*inch])
    report_metadata_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e9ecef')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(report_metadata_table)
    story.append(Spacer(1, 15))
    
    # Image Summary
    story.append(Paragraph("Image Summary", subheading_style))
    image_summary_data = [
        ['Area', 'Notes'],
        ['Skin', f"{skin_pred} ({skin_severity})"],
        ['Nail', f"{nail_pred} ({nail_severity})"]
    ]
    
    image_summary_table = Table(image_summary_data, colWidths=[2*inch, 4*inch])
    image_summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007bff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 1), (1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(image_summary_table)
    story.append(Spacer(1, 15))
    
    # Findings & Interpretation
    story.append(Paragraph("Findings & Interpretation", subheading_style))
    
    # Determine if skin/nail are unhealthy
    skin_unhealthy = 'unhealthy' in (report.skin_pred or '')
    nail_unhealthy = 'unhealthy' in (report.nail_pred or '')
    
    # Skin findings
    story.append(Paragraph("Skin Health Findings:", styles['Normal']))
    if skin_unhealthy:
        skin_findings = [
            "• Texture or color patterns suggest potential nutritional or dermatologic concern.",
            "• Consider hydration optimization and review for micronutrient gaps (vitamin A/E, zinc).",
            "• If persistent for >2 weeks or symptomatic (itching, pain), seek clinician review."
        ]
    else:
        skin_findings = [
            "• No suspicious lesions or dyschromia detected by the model.",
            "• Maintain sun protection and routine moisturization."
        ]
    
    for finding in skin_findings:
        story.append(Paragraph(finding, styles['Normal']))
    
    story.append(Spacer(1, 10))
    
    # Nail findings
    story.append(Paragraph("Nail Health Findings:", styles['Normal']))
    if nail_unhealthy:
        nail_findings = [
            "• Surface features may reflect iron/protein deficiency or mechanical trauma.",
            "• Check for brittleness, discoloration, or periungual swelling over the next weeks.",
            "• Discuss diet rich in iron, protein, biotin; seek care if changes progress."
        ]
    else:
        nail_findings = [
            "• Color and attachment appear within expected range.",
            "• Maintain trimming hygiene; avoid prolonged moisture exposure."
        ]
    
    for finding in nail_findings:
        story.append(Paragraph(finding, styles['Normal']))
    
    story.append(Spacer(1, 15))
    
    # Overall assessment
    if skin_unhealthy and nail_unhealthy:
        assessment_text = "Combined skin and nail findings increase the likelihood of nutritional imbalance. Review dietary intake, hydration, and consider clinician follow-up."
        assessment_color = colors.HexColor('#856404')
    elif skin_unhealthy or nail_unhealthy:
        assessment_text = "One area shows abnormalities. Monitor 2–4 weeks and reinforce diet, sleep, hydration, and hygiene. Escalate if symptoms worsen."
        assessment_color = colors.HexColor('#0c5460')
    else:
        assessment_text = "Skin and nail findings are within normal limits. Continue healthy routines and periodic monitoring."
        assessment_color = colors.HexColor('#155724')
    
    story.append(Paragraph(assessment_text, 
                          ParagraphStyle('Assessment', parent=styles['Normal'], 
                                       fontSize=10, textColor=assessment_color, 
                                       backColor=colors.HexColor('#f8f9fa'),
                                       borderColor=assessment_color,
                                       borderWidth=1,
                                       borderPadding=10)))
    
    story.append(Spacer(1, 20))
    
    # Footer
    story.append(Spacer(1, 30))
    story.append(Paragraph(
        f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by NutriScan AI",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.grey)
    ))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


