from flask import Blueprint, render_template

about_bp = Blueprint('about', __name__, url_prefix='/about')

@about_bp.route('/')
def index():
    """About us page"""
    return render_template('about/index.html')

