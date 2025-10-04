#!/usr/bin/env python3
"""
Test Script for Enhanced Malnutrition Analysis Features
Tests WHO standards, risk assessment, and chatbot functionality
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_who_standards():
    """Test WHO standards calculations"""
    print("🧪 Testing WHO Standards...")
    
    try:
        from predict.who_standards import WHOStandards
        
        # Test BMI percentile and z-score calculation
        age = 8.0
        bmi = 16.5
        gender = 'male'
        
        percentile, z_score = WHOStandards.calculate_bmi_percentile_and_zscore(age, bmi, gender)
        category = WHOStandards.get_bmi_category(bmi, age, gender)
        
        print(f"✓ Age: {age} years, BMI: {bmi}, Gender: {gender}")
        print(f"✓ Percentile: {percentile:.1f}%")
        print(f"✓ Z-Score: {z_score:.2f}")
        print(f"✓ Category: {category}")
        
        return True
        
    except Exception as e:
        print(f"❌ WHO Standards test failed: {e}")
        return False

def test_risk_assessment():
    """Test malnutrition risk assessment"""
    print("\n🧪 Testing Risk Assessment...")
    
    try:
        from predict.who_standards import MalnutritionRiskAssessment
        
        # Test risk score calculation
        risk_assessment = MalnutritionRiskAssessment.calculate_risk_score(
            bmi_percentile=15.0,  # Below 25th percentile
            bmi_z_score=-1.2,     # Below normal
            skin_health='unhealthy_skin',
            nail_health='healthy_nails',
            skin_confidence=0.7,
            nail_confidence=0.8,
            age_years=8.0
        )
        
        print(f"✓ Risk Score: {risk_assessment['risk_score']}/100")
        print(f"✓ Risk Level: {risk_assessment['risk_level']}")
        print(f"✓ BMI Risk: {risk_assessment['bmi_risk']}")
        print(f"✓ Z-Score Risk: {risk_assessment['z_score_risk']}")
        print(f"✓ Skin Risk: {risk_assessment['skin_risk']}")
        print(f"✓ Nail Risk: {risk_assessment['nail_risk']}")
        
        # Test recommendations
        recommendations = MalnutritionRiskAssessment.generate_recommendations(
            risk_assessment, 'Underweight'
        )
        
        print(f"✓ Professional Consultation: {recommendations['professional_consultation']}")
        print(f"✓ Dietary: {len(recommendations['dietary_recommendations'])} chars")
        print(f"✓ Lifestyle: {len(recommendations['lifestyle_recommendations'])} chars")
        print(f"✓ Hydration: {len(recommendations['hydration_tips'])} chars")
        
        return True
        
    except Exception as e:
        print(f"❌ Risk Assessment test failed: {e}")
        return False

def test_chatbot():
    """Test chatbot functionality"""
    print("\n🧪 Testing Chatbot...")
    
    try:
        from predict.chatbot import MalnutritionChatbot
        
        # Initialize chatbot
        chatbot = MalnutritionChatbot()
        
        # Test greeting
        greeting = chatbot.get_greeting()
        print(f"✓ Greeting: {len(greeting)} chars")
        
        # Test message processing
        response = chatbot.process_message("Hello")
        print(f"✓ Hello response: {len(response)} chars")
        
        # Test with context
        report_data = {
            'report': {
                'nutrition_status': 'At Risk',
                'skin_pred': 'unhealthy_skin',
                'nail_pred': 'healthy_nails',
                'bmi_category': 'Underweight',
                'bmi_percentile': 15.0,
                'bmi_z_score': -1.2,
                'malnutrition_risk_score': 45,
                'risk_level': 'Medium'
            },
            'patient': {
                'child_name': 'Test Child',
                'age_months': 96,
                'bmi': 16.5
            }
        }
        
        response = chatbot.process_message("Explain the report", report_data)
        print(f"✓ Report explanation: {len(response)} chars")
        
        # Test quick actions
        quick_actions = chatbot.get_quick_actions()
        print(f"✓ Quick actions: {len(quick_actions)} available")
        
        return True
        
    except Exception as e:
        print(f"❌ Chatbot test failed: {e}")
        return False

def test_models():
    """Test model imports and basic functionality"""
    print("\n🧪 Testing Model Imports...")
    
    try:
        # Test WHO standards import
        from predict.who_standards import WHOStandards, MalnutritionRiskAssessment
        print("✓ WHO Standards imported successfully")
        
        # Test chatbot import
        from predict.chatbot import MalnutritionChatbot
        print("✓ Chatbot imported successfully")
        
        # Test model import
        from predict.model import get_predictor
        print("✓ ML Models imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Model import test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Enhanced Malnutrition Analysis System - Feature Tests")
    print("=" * 60)
    
    tests = [
        ("Model Imports", test_models),
        ("WHO Standards", test_who_standards),
        ("Risk Assessment", test_risk_assessment),
        ("Chatbot", test_chatbot)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced features are working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
