from flask import Blueprint, render_template
from flask_login import login_required


analytics_bp = Blueprint("analytics", __name__, url_prefix="/analytics")


@analytics_bp.route("/")
@login_required
def index():
    # Placeholder page for charts and aggregated stats
    return render_template("analytics/index.html")


