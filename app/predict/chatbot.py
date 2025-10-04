"""
NutriScan Chatbot Assistant
Provides interactive explanations and personalized recommendations
"""

import re
from typing import Dict, Any, List, Tuple
from datetime import datetime


class MalnutritionChatbot:
    """Interactive chatbot for explaining NutriScan reports and providing guidance"""
    
    def __init__(self):
        self.conversation_history = []
        self.user_context = {}
        
    def add_to_history(self, message: str, is_user: bool = True):
        """Add message to conversation history"""
        timestamp = datetime.now().strftime("%H:%M")
        self.conversation_history.append({
            'message': message,
            'is_user': is_user,
            'timestamp': timestamp
        })
    
    def get_greeting(self) -> str:
        """Get initial greeting message"""
        greeting = (
            "👋 Hello! I'm your NutriScan Assistant. "
            "I can help explain your child's nutrition report and provide personalized recommendations. "
            "What would you like to know about?"
        )
        self.add_to_history(greeting, is_user=False)
        return greeting
    
    def process_message(self, user_message: str, report_data: Dict[str, Any] = None) -> str:
        """
        Process user message and generate appropriate response
        
        Args:
            user_message: User's input message
            report_data: Report data for context-aware responses
            
        Returns:
            Bot's response message
        """
        self.add_to_history(user_message, is_user=True)
        
        # Store report context if provided
        if report_data:
            self.user_context = report_data
        
        # Process the message
        response = self._generate_response(user_message.lower())
        self.add_to_history(response, is_user=False)
        
        return response
    
    def _generate_response(self, message: str) -> str:
        """Generate response based on user message"""
        
        # Greeting patterns
        if any(word in message for word in ['hello', 'hi', 'hey', 'start']):
            return self._get_greeting_response()
        
        # Report explanation patterns
        if any(word in message for word in ['explain', 'what does', 'mean', 'understand', 'report']):
            return self._explain_report()
        
        # BMI related questions
        if any(word in message for word in ['bmi', 'weight', 'height', 'percentile', 'z-score']):
            return self._explain_bmi()
        
        # Risk assessment questions
        if any(word in message for word in ['risk', 'dangerous', 'serious', 'critical', 'level']):
            return self._explain_risk()
        
        # Recommendation patterns
        if any(word in message for word in ['recommend', 'advice', 'what should', 'help', 'improve']):
            return self._provide_recommendations()
        
        # Professional consultation
        if any(word in message for word in ['doctor', 'hospital', 'professional', 'consult', 'medical']):
            return self._explain_consultation()
        
        # General nutrition questions
        if any(word in message for word in ['nutrition', 'food', 'diet', 'healthy', 'eating']):
            return self._explain_nutrition()
        
        # Default response
        return self._get_default_response()
    
    def _get_greeting_response(self) -> str:
        """Generate greeting response"""
        return (
            "👋 Great to see you! I'm here to help you understand your child's nutrition report. "
            "I can explain:\n"
            "• What the results mean\n"
            "• BMI and growth patterns\n"
            "• Risk levels and what they indicate\n"
            "• Personalized recommendations\n"
            "• When to consult professionals\n\n"
            "What would you like me to explain first?"
        )
    
    def _explain_report(self) -> str:
        """Explain the overall report"""
        if not self.user_context:
            return "I don't have access to a specific report yet. Please upload images and get a report first, then I can explain it to you."
        
        patient = self.user_context.get('patient', {})
        report = self.user_context.get('report', {})
        
        child_name = patient.get('child_name', 'your child')
        age_months = patient.get('age_months', 0)
        age_years = age_months / 12.0
        
        response = f"📊 Let me explain {child_name}'s nutrition report:\n\n"
        
        # Overall status
        nutrition_status = report.get('nutrition_status', 'Unknown')
        if nutrition_status == 'Normal':
            response += "✅ Overall Status: Your child appears to have normal nutrition status.\n"
        else:
            response += f"⚠️ Overall Status: {nutrition_status} - This indicates some concerns that need attention.\n"
        
        # BMI information
        bmi = patient.get('bmi', 0)
        bmi_category = report.get('bmi_category', 'Unknown')
        response += f"📏 BMI: {bmi:.1f} - This places {child_name} in the '{bmi_category}' category.\n"
        
        # Age context
        if age_years < 5:
            response += f"👶 At {age_years:.1f} years old, this is a critical growth period. Proper nutrition is essential for development.\n"
        elif age_years < 12:
            response += f"🧒 At {age_years:.1f} years old, {child_name} is in the school-age growth phase.\n"
        else:
            response += f"👦 At {age_years:.1f} years old, {child_name} is in adolescence with increased nutritional needs.\n"
        
        response += "\nWould you like me to explain any specific part in more detail?"
        
        return response
    
    def _explain_bmi(self) -> str:
        """Explain BMI and related measurements"""
        if not self.user_context:
            return "I need to see a report to explain BMI details. Please get a report first."
        
        patient = self.user_context.get('patient', {})
        report = self.user_context.get('report', {})
        
        child_name = patient.get('child_name', 'your child')
        bmi = patient.get('bmi', 0)
        bmi_percentile = report.get('bmi_percentile', 0)
        bmi_z_score = report.get('bmi_z_score', 0)
        bmi_category = report.get('bmi_category', 'Unknown')
        
        response = "📊 Let me explain the BMI measurements:\n\n"
        
        response += f"**BMI Value: {bmi:.1f}**\n"
        response += f"This is {child_name}'s Body Mass Index, calculated from height and weight.\n\n"
        
        response += f"**WHO Percentile: {bmi_percentile:.1f}**\n"
        if bmi_percentile < 5:
            response += "This is below the 5th percentile, indicating significant underweight.\n"
        elif bmi_percentile < 25:
            response += "This is below the 25th percentile, indicating mild underweight.\n"
        elif bmi_percentile < 75:
            response += "This is in the normal range (25th-75th percentile).\n"
        elif bmi_percentile < 95:
            response += "This is above the 75th percentile, indicating overweight.\n"
        else:
            response += "This is above the 95th percentile, indicating obesity.\n"
        
        response += f"\n**Z-Score: {bmi_z_score:.2f}**\n"
        if abs(bmi_z_score) < 1.0:
            response += "This is within normal range (±1 standard deviation).\n"
        elif abs(bmi_z_score) < 2.0:
            response += "This is moderately outside normal range (±1-2 standard deviations).\n"
        else:
            response += "This is significantly outside normal range (±2+ standard deviations).\n"
        
        response += f"\n**Category: {bmi_category}**\n"
        response += "This is the WHO classification based on age and gender standards.\n"
        
        return response
    
    def _explain_risk(self) -> str:
        """Explain risk assessment"""
        if not self.user_context:
            return "I need to see a report to explain risk levels. Please get a report first."
        
        report = self.user_context.get('report', {})
        risk_score = report.get('malnutrition_risk_score', 0)
        risk_level = report.get('risk_level', 'Unknown')
        
        response = "⚠️ Let me explain the risk assessment:\n\n"
        
        response += f"**Risk Score: {risk_score}/100**\n"
        response += f"**Risk Level: {risk_level}**\n\n"
        
        if risk_level == "Low":
            response += "🟢 Low Risk: Your child's nutrition status appears healthy. Continue current habits and monitor growth.\n"
        elif risk_level == "Medium":
            response += "🟡 Medium Risk: Some concerns detected. Consider minor adjustments to diet and lifestyle.\n"
        elif risk_level == "High":
            response += "🟠 High Risk: Significant concerns detected. Immediate attention and changes recommended.\n"
        elif risk_level == "Critical":
            response += "🔴 Critical Risk: Serious concerns detected. Professional medical consultation strongly recommended.\n"
        
        response += "\n**What contributes to this risk:**\n"
        
        # Explain contributing factors
        skin_health = report.get('skin_pred', 'Unknown')
        nail_health = report.get('nail_pred', 'Unknown')
        
        if 'unhealthy' in skin_health:
            response += "• Skin condition indicates potential nutritional deficiencies\n"
        if 'unhealthy' in nail_health:
            response += "• Nail condition suggests possible iron or protein issues\n"
        
        bmi_percentile = report.get('bmi_percentile', 50)
        if bmi_percentile < 10 or bmi_percentile > 90:
            response += "• BMI is outside healthy range for age\n"
        
        return response
    
    def _provide_recommendations(self) -> str:
        """Provide personalized recommendations"""
        if not self.user_context:
            return "I need to see a report to provide personalized recommendations. Please get a report first."
        
        report = self.user_context.get('report', {})
        
        response = "💡 Here are personalized recommendations based on the analysis:\n\n"
        
        # Dietary recommendations
        dietary = report.get('dietary_recommendations', '')
        if dietary:
            response += "**🍎 Dietary Recommendations:**\n"
            response += f"{dietary}\n\n"
        
        # Lifestyle recommendations
        lifestyle = report.get('lifestyle_recommendations', '')
        if lifestyle:
            response += "**🏃 Lifestyle Recommendations:**\n"
            response += f"{lifestyle}\n\n"
        
        # Hydration tips
        hydration = report.get('hydration_tips', '')
        if hydration:
            response += "**💧 Hydration Tips:**\n"
            response += f"{hydration}\n\n"
        
        # Professional consultation
        if report.get('professional_consultation', False):
            response += "**🏥 Professional Consultation:**\n"
            response += "Based on the assessment, consulting a healthcare professional is recommended.\n"
        
        response += "\nWould you like me to explain any of these recommendations in more detail?"
        
        return response
    
    def _explain_consultation(self) -> str:
        """Explain when to consult professionals"""
        response = "🏥 **When to Consult Healthcare Professionals:**\n\n"
        
        response += "**Immediate Consultation (Within 1-2 weeks):**\n"
        response += "• BMI below 5th or above 95th percentile\n"
        response += "• Rapid weight loss or gain\n"
        response += "• Persistent fatigue or weakness\n"
        response += "• Severe skin or nail problems\n\n"
        
        response += "**Regular Monitoring (Every 3-6 months):**\n"
        response += "• BMI between 5th-10th or 90th-95th percentile\n"
        response += "• Mild nutritional concerns\n"
        response += "• Family history of nutrition issues\n\n"
        
        response += "**What to Bring:**\n"
        response += "• Growth charts and measurements\n"
        response += "• Photos of skin/nail conditions\n"
        response += "• Food diary (if available)\n"
        response += "• Family medical history\n\n"
        
        response += "Remember: Early intervention is key to preventing long-term health issues!"
        
        return response
    
    def _explain_nutrition(self) -> str:
        """Explain general nutrition concepts"""
        response = "🥗 **General Nutrition Guidelines for Children:**\n\n"
        
        response += "**Essential Nutrients:**\n"
        response += "• Protein: Building blocks for growth (meat, fish, eggs, legumes)\n"
        response += "• Carbohydrates: Energy source (whole grains, fruits, vegetables)\n"
        response += "• Healthy Fats: Brain development (nuts, avocados, olive oil)\n"
        response += "• Vitamins & Minerals: Overall health (colorful fruits and vegetables)\n\n"
        
        response += "**Daily Recommendations:**\n"
        response += "• 5+ servings of fruits and vegetables\n"
        response += "• 3 servings of protein-rich foods\n"
        response += "• 6-8 glasses of water\n"
        response += "• Limit processed foods and sugary drinks\n\n"
        
        response += "**Growth Monitoring:**\n"
        response += "• Regular height and weight measurements\n"
        response += "• Track growth patterns over time\n"
        response += "• Consult growth charts for age and gender\n"
        
        return response
    
    def _get_default_response(self) -> str:
        """Get default response for unrecognized messages"""
        responses = [
            "I'm not sure I understood that. Could you rephrase your question?",
            "I can help explain the report, BMI measurements, risk levels, or provide recommendations. What would you like to know?",
            "Try asking me to 'explain the report' or 'what are the recommendations?'",
            "I'm here to help! Ask me about the nutrition analysis, risk assessment, or dietary advice."
        ]
        
        import random
        return random.choice(responses)
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history for display"""
        return self.conversation_history
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        self.user_context = {}
    
    def get_quick_actions(self) -> List[Dict[str, str]]:
        """Get quick action buttons for the UI"""
        return [
            {"text": "Explain Report", "action": "explain_report"},
            {"text": "BMI Details", "action": "explain_bmi"},
            {"text": "Risk Assessment", "action": "explain_risk"},
            {"text": "Get Recommendations", "action": "get_recommendations"},
            {"text": "When to See Doctor", "action": "consultation_advice"}
        ]
