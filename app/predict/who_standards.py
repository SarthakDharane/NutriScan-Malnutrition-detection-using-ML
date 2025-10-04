"""
WHO Standards and Malnutrition Risk Assessment Module
Provides calculations for BMI-for-age percentiles, z-scores, and risk assessment
based on World Health Organization standards.
"""

import numpy as np
from typing import Tuple, Dict, Any


class WHOStandards:
    """WHO growth standards for children and adolescents (2-19 years)"""
    
    # WHO BMI-for-age reference data (simplified version)
    # In production, use complete WHO growth reference data
    BMI_REFERENCE_DATA = {
        'male': {
            'ages': [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
            'p3': [14.1, 13.9, 13.8, 13.7, 13.6, 13.5, 13.4, 13.3, 13.2, 13.1, 13.0, 12.9, 12.8, 12.7, 12.6, 12.5, 12.4, 12.3],
            'p5': [14.5, 14.3, 14.2, 14.1, 14.0, 13.9, 13.8, 13.7, 13.6, 13.5, 13.4, 13.3, 13.2, 13.1, 13.0, 12.9, 12.8, 12.7],
            'p10': [15.0, 14.8, 14.7, 14.6, 14.5, 14.4, 14.3, 14.2, 14.1, 14.0, 13.9, 13.8, 13.7, 13.6, 13.5, 13.4, 13.3, 13.2],
            'p25': [15.8, 15.6, 15.5, 15.4, 15.3, 15.2, 15.1, 15.0, 14.9, 14.8, 14.7, 14.6, 14.5, 14.4, 14.3, 14.2, 14.1, 14.0],
            'p50': [16.5, 16.3, 16.2, 16.1, 16.0, 15.9, 15.8, 15.7, 15.6, 15.5, 15.4, 15.3, 15.2, 15.1, 15.0, 14.9, 14.8, 14.7],
            'p75': [17.3, 17.1, 17.0, 16.9, 16.8, 16.7, 16.6, 16.5, 16.4, 16.3, 16.2, 16.1, 16.0, 15.9, 15.8, 15.7, 15.6, 15.5],
            'p90': [18.2, 18.0, 17.9, 17.8, 17.7, 17.6, 17.5, 17.4, 17.3, 17.2, 17.1, 17.0, 16.9, 16.8, 16.7, 16.6, 16.5, 16.4],
            'p95': [19.0, 18.8, 18.7, 18.6, 18.5, 18.4, 18.3, 18.2, 18.1, 18.0, 17.9, 17.8, 17.7, 17.6, 17.5, 17.4, 17.3, 17.2],
            'p97': [19.8, 19.6, 19.5, 19.4, 19.3, 19.2, 19.1, 19.0, 18.9, 18.8, 18.7, 18.6, 18.5, 18.4, 18.3, 18.2, 18.1, 18.0]
        },
        'female': {
            'ages': [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
            'p3': [13.9, 13.7, 13.6, 13.5, 13.4, 13.3, 13.2, 13.1, 13.0, 12.9, 12.8, 12.7, 12.6, 12.5, 12.4, 12.3, 12.2, 12.1],
            'p5': [14.3, 14.1, 14.0, 13.9, 13.8, 13.7, 13.6, 13.5, 13.4, 13.3, 13.2, 13.1, 13.0, 12.9, 12.8, 12.7, 12.6, 12.5],
            'p10': [14.8, 14.6, 14.5, 14.4, 14.3, 14.2, 14.1, 14.0, 13.9, 13.8, 13.7, 13.6, 13.5, 13.4, 13.3, 13.2, 13.1, 13.0],
            'p25': [15.6, 15.4, 15.3, 15.2, 15.1, 15.0, 14.9, 14.8, 14.7, 14.6, 14.5, 14.4, 14.3, 14.2, 14.1, 14.0, 13.9, 13.8],
            'p50': [16.3, 16.1, 16.0, 15.9, 15.8, 15.7, 15.6, 15.5, 15.4, 15.3, 15.2, 15.1, 15.0, 14.9, 14.8, 14.7, 14.6, 14.5],
            'p75': [17.1, 16.9, 16.8, 16.7, 16.6, 16.5, 16.4, 16.3, 16.2, 16.1, 16.0, 15.9, 15.8, 15.7, 15.6, 15.5, 15.4, 15.3],
            'p90': [18.0, 17.8, 17.7, 17.6, 17.5, 17.4, 17.3, 17.2, 17.1, 17.0, 16.9, 16.8, 16.7, 16.6, 16.5, 16.4, 16.3, 16.2],
            'p95': [18.8, 18.6, 18.5, 18.4, 18.3, 18.2, 18.1, 18.0, 17.9, 17.8, 17.7, 17.6, 17.5, 17.4, 17.3, 17.2, 17.1, 17.0],
            'p97': [19.6, 19.4, 19.3, 19.2, 19.1, 19.0, 18.9, 18.8, 18.7, 18.6, 18.5, 18.4, 18.3, 18.2, 18.1, 18.0, 17.9, 17.8]
        }
    }
    
    @classmethod
    def calculate_bmi_percentile_and_zscore(cls, age_years: float, bmi: float, gender: str) -> Tuple[float, float]:
        """
        Calculate BMI-for-age percentile and z-score using WHO standards
        
        Args:
            age_years: Age in years
            bmi: BMI value
            gender: 'male' or 'female'
            
        Returns:
            Tuple of (percentile, z_score)
        """
        if gender.lower() not in ['male', 'female']:
            raise ValueError("Gender must be 'male' or 'female'")
        
        if age_years < 2 or age_years > 19:
            raise ValueError("Age must be between 2 and 19 years")
        
        gender_data = cls.BMI_REFERENCE_DATA[gender.lower()]
        ages = np.array(gender_data['ages'])
        percentiles = ['p3', 'p5', 'p10', 'p25', 'p50', 'p75', 'p90', 'p95', 'p97']
        
        # Find closest age in reference data
        age_idx = np.argmin(np.abs(ages - age_years))
        reference_age = ages[age_idx]
        
        # Get BMI values for this age
        bmi_values = [gender_data[p][age_idx] for p in percentiles]
        
        # Calculate percentile using interpolation
        if bmi <= bmi_values[0]:  # Below 3rd percentile
            percentile = 3.0 * (bmi / bmi_values[0])
        elif bmi >= bmi_values[-1]:  # Above 97th percentile
            percentile = 97.0 + (3.0 * (bmi - bmi_values[-1]) / bmi_values[-1])
        else:
            # Find the two percentiles to interpolate between
            for i in range(len(bmi_values) - 1):
                if bmi_values[i] <= bmi <= bmi_values[i + 1]:
                    p1, p2 = float(percentiles[i][1:]), float(percentiles[i + 1][1:])
                    bmi1, bmi2 = bmi_values[i], bmi_values[i + 1]
                    percentile = p1 + (p2 - p1) * (bmi - bmi1) / (bmi2 - bmi1)
                    break
            else:
                percentile = 50.0  # Default to median
        
        # Calculate z-score (approximate)
        # Using the relationship between percentile and z-score
        if percentile <= 50:
            z_score = -np.abs(np.percentile(np.random.standard_normal(10000), percentile))
        else:
            z_score = np.abs(np.percentile(np.random.standard_normal(10000), 100 - percentile))
        
        return percentile, z_score
    
    @classmethod
    def get_bmi_category(cls, bmi: float, age_years: float, gender: str) -> str:
        """
        Get BMI category based on WHO standards
        
        Args:
            bmi: BMI value
            age_years: Age in years
            gender: 'male' or 'female'
            
        Returns:
            BMI category string
        """
        try:
            percentile, z_score = cls.calculate_bmi_percentile_and_zscore(age_years, bmi, gender)
            
            # WHO child/adolescent categories:
            # Underweight: <5th, Normal: 5th–<85th, Overweight: 85th–<97th, Obese: ≥97th
            if percentile < 5:
                return "Underweight"
            elif percentile < 85:
                return "Normal"
            elif percentile < 97:
                return "Overweight"
            else:
                return "Obese"
        except:
            # Fallback to adult standards if WHO calculation fails
            if bmi < 18.5:
                return "Underweight"
            elif bmi < 25:
                return "Normal"
            elif bmi < 30:
                return "Overweight"
            else:
                return "Obese"


class MalnutritionRiskAssessment:
    """Calculate malnutrition risk score based on multiple factors"""
    
    @staticmethod
    def calculate_risk_score(
        bmi_percentile: float,
        bmi_z_score: float,
        skin_health: str,
        nail_health: str,
        skin_confidence: float,
        nail_confidence: float,
        age_years: float
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive malnutrition risk score
        
        Args:
            bmi_percentile: WHO BMI percentile
            bmi_z_score: WHO BMI z-score
            skin_health: 'healthy_skin' or 'unhealthy_skin'
            nail_health: 'healthy_nails' or 'unhealthy_nails'
            skin_confidence: Confidence score for skin prediction
            nail_confidence: Confidence score for nail prediction
            age_years: Age in years
            
        Returns:
            Dictionary with risk assessment results
        """
        risk_score = 0
        
        # BMI-based risk (40 points)
        if bmi_percentile < 5:
            risk_score += 40  # Severe underweight
        elif bmi_percentile < 10:
            risk_score += 30  # Moderate underweight
        elif bmi_percentile < 25:
            risk_score += 20  # Mild underweight
        elif bmi_percentile >= 97:
            risk_score += 35  # Obese
        elif bmi_percentile >= 85:
            risk_score += 25  # Overweight
        
        # Z-score risk (20 points)
        if abs(bmi_z_score) > 2.0:
            risk_score += 20
        elif abs(bmi_z_score) > 1.5:
            risk_score += 15
        elif abs(bmi_z_score) > 1.0:
            risk_score += 10
        
        # Skin health risk (20 points)
        if 'unhealthy' in skin_health:
            risk_score += int(20 * (1 - skin_confidence))  # Higher risk if low confidence
        else:
            risk_score += int(5 * (1 - skin_confidence))  # Lower risk but still some if low confidence
        
        # Nail health risk (20 points)
        if 'unhealthy' in nail_health:
            risk_score += int(20 * (1 - nail_confidence))
        else:
            risk_score += int(5 * (1 - nail_confidence))
        
        # Age-specific risk adjustments
        if age_years < 5:  # Early childhood critical period
            risk_score = int(risk_score * 1.2)
        elif age_years > 15:  # Adolescence growth spurt
            risk_score = int(risk_score * 1.1)
        
        # Cap at 100
        risk_score = min(100, risk_score)
        
        # Determine risk level
        if risk_score < 20:
            risk_level = "Low"
        elif risk_score < 40:
            risk_level = "Medium"
        elif risk_score < 60:
            risk_level = "High"
        else:
            risk_level = "Critical"
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'bmi_risk': min(40, risk_score),
            'z_score_risk': min(20, risk_score),
            'skin_risk': min(20, risk_score),
            'nail_risk': min(20, risk_score)
        }
    
    @staticmethod
    def generate_recommendations(risk_assessment: Dict[str, Any], bmi_category: str) -> Dict[str, str]:
        """
        Generate personalized recommendations based on risk assessment
        
        Args:
            risk_assessment: Risk assessment results
            bmi_category: BMI category
            
        Returns:
            Dictionary with recommendations
        """
        risk_level = risk_assessment['risk_level']
        risk_score = risk_assessment['risk_score']
        
        # Dietary recommendations
        if bmi_category == "Underweight":
            dietary = (
                "Increase caloric intake with nutrient-dense foods. "
                "Focus on protein-rich foods, healthy fats, and complex carbohydrates. "
                "Consider 5-6 small meals per day. Include dairy, eggs, lean meats, "
                "nuts, and whole grains."
            )
        elif bmi_category == "Overweight" or bmi_category == "Obese":
            dietary = (
                "Focus on portion control and balanced nutrition. "
                "Increase vegetables, fruits, and lean proteins. "
                "Reduce processed foods, sugary drinks, and excessive fats. "
                "Aim for regular meal timing and avoid skipping meals."
            )
        else:
            dietary = (
                "Maintain balanced nutrition with variety. "
                "Include all food groups: proteins, carbohydrates, healthy fats, "
                "vitamins, and minerals. Focus on whole foods over processed options."
            )
        
        # Lifestyle recommendations
        if risk_score > 60:
            lifestyle = (
                "Immediate attention required. Establish regular sleep patterns, "
                "reduce screen time, and increase physical activity. "
                "Consider stress management techniques and family counseling."
            )
        elif risk_score > 40:
            lifestyle = (
                "Moderate lifestyle changes needed. Increase physical activity to "
                "60 minutes daily, improve sleep hygiene, and reduce sedentary behavior. "
                "Establish regular routines."
            )
        else:
            lifestyle = (
                "Maintain healthy habits. Continue regular physical activity, "
                "adequate sleep (8-10 hours), and balanced daily routines. "
                "Monitor growth patterns regularly."
            )
        
        # Hydration tips
        if risk_score > 50:
            hydration = (
                "Ensure adequate hydration: 6-8 glasses of water daily. "
                "Monitor urine color (should be light yellow). "
                "Increase fluids during physical activity and hot weather."
            )
        else:
            hydration = (
                "Maintain good hydration habits: 6-8 glasses of water daily. "
                "Include water-rich foods like fruits and vegetables."
            )
        
        # Professional consultation recommendation
        professional_consultation = risk_score > 40 or bmi_category in ["Underweight", "Obese"]
        
        return {
            'dietary_recommendations': dietary,
            'lifestyle_recommendations': lifestyle,
            'hydration_tips': hydration,
            'professional_consultation': professional_consultation
        }
