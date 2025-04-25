from flask import Flask, request, jsonify, render_template
from helpers import generate_ai_response, generate_mock_response
from config import USE_MOCK_RESPONSE
from math import pow

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/check-symptoms", methods=["POST"])
def check_symptoms():
    symptoms = request.form.get("symptoms")
    
    # Use the appropriate response generator based on config
    if USE_MOCK_RESPONSE:
        response = generate_mock_response(symptoms)
    else:
        response = generate_ai_response(symptoms)
    
    return jsonify({"result": response})

@app.route('/bmi-calculator', methods=['GET', 'POST'])
def bmi_calculator():
    bmi = None
    category = None
    body_fat = None
    risk = None
    age = None
    gender = None

    if request.method == 'POST':
        try:
            weight = float(request.form['weight'])
            height = float(request.form['height'])
            age = int(request.form['age'])
            gender = request.form['gender']  # 'male' or 'female'

            if weight <= 0 or height <= 0 or age <= 0:
                raise ValueError("Weight, height, and age must be positive numbers.")

            # BMI Calculation
            bmi = weight / pow(height / 100, 2)  # Height in meters for proper calculation

            # BMI Categories with more detailed descriptions
            if bmi < 16:
                category = "Severe Underweight"
            elif 16 <= bmi < 17:
                category = "Moderate Underweight"
            elif 17 <= bmi < 18.5:
                category = "Mild Underweight"
            elif 18.5 <= bmi < 21.0:
                category = "Lower Normal Weight"
            elif 21.0 <= bmi < 23.5:
                category = "Mid Normal Weight"
            elif 23.5 <= bmi < 25:
                category = "Upper Normal Weight"
            elif 25 <= bmi < 27.5:
                category = "Overweight Class I"
            elif 27.5 <= bmi < 30:
                category = "Overweight Class II"
            elif 30 <= bmi < 35:
                category = "Obesity Class I (Moderate)"
            elif 35 <= bmi < 40:
                category = "Obesity Class II (Severe)"
            else:
                category = "Obesity Class III (Very Severe)"
            
            # Calculate Body Fat Percentage (BFP) - using more accurate formulas
            if gender == 'male':
                # Improved BFP formula for men
                body_fat = (1.20 * bmi) + (0.23 * age) - 16.2
                
                # Ensure realistic ranges
                if body_fat < 2:
                    body_fat = 2  # Minimum essential fat for men
                elif body_fat > 50:
                    body_fat = 50  # Realistic upper limit
            elif gender == 'female':
                # Improved BFP formula for women
                body_fat = (1.20 * bmi) + (0.23 * age) - 5.4
                
                # Ensure realistic ranges
                if body_fat < 10:
                    body_fat = 10  # Minimum essential fat for women
                elif body_fat > 60:
                    body_fat = 60  # Realistic upper limit

            # Detailed Health Risk Assessment Based on BMI, Age, and Gender
            if bmi < 16:
                risk = "Severe health risk due to significant underweight status. Possible malnutrition, weakened immune system, and hormonal disruptions."
            elif 16 <= bmi < 18.5:
                risk = "Increased risk associated with being underweight. May experience nutritional deficiencies, decreased muscle strength, and compromised immune function."
            elif 18.5 <= bmi < 25:
                if age > 65:
                    risk = "Healthy weight range. For older adults, maintaining this BMI is beneficial for mobility and independence."
                else:
                    risk = "Healthy weight range with lowest risk of weight-related health issues. Maintain regular physical activity and balanced nutrition."
            elif 25 <= bmi < 30:
                if age > 65:
                    risk = "Slightly elevated health risk. For older adults, a slightly higher BMI may be protective against frailty."
                else:
                    risk = "Moderately increased risk of heart disease, type 2 diabetes, high blood pressure, and certain cancers. Consider gradual weight reduction through lifestyle changes."
            elif 30 <= bmi < 35:
                risk = "High risk of cardiovascular disease, metabolic syndrome, sleep apnea, and joint problems. Medical evaluation recommended."
            elif 35 <= bmi < 40:
                risk = "Very high risk of serious health conditions including heart disease, stroke, diabetes, and certain cancers. Medical supervision strongly advised."
            else:
                risk = "Extremely high risk of severe health complications. Immediate medical consultation is strongly recommended for a comprehensive health assessment and intervention plan."
                
            # Add body fat context to risk assessment
            if gender == 'male':
                if body_fat < 6:
                    risk += " Body fat percentage is extremely low, which can affect hormone function and overall health."
                elif 6 <= body_fat <= 13:
                    risk += " Body fat percentage is in the athletic range."
                elif 14 <= body_fat <= 17:
                    risk += " Body fat percentage is in the fitness range."
                elif 18 <= body_fat <= 24:
                    risk += " Body fat percentage is in the acceptable range."
                else:
                    risk += " Body fat percentage is elevated, which may increase metabolic health risks."
            elif gender == 'female':
                if body_fat < 16:
                    risk += " Body fat percentage is extremely low, which can affect hormone function and reproductive health."
                elif 16 <= body_fat <= 20:
                    risk += " Body fat percentage is in the athletic range."
                elif 21 <= body_fat <= 24:
                    risk += " Body fat percentage is in the fitness range."
                elif 25 <= body_fat <= 31:
                    risk += " Body fat percentage is in the acceptable range."
                else:
                    risk += " Body fat percentage is elevated, which may increase metabolic health risks."

        except ValueError as e:
            category = f"Error: {str(e)}"

    return render_template('bmi_calculator.html', bmi=bmi, category=category, body_fat=body_fat, risk=risk, age=age, gender=gender)


if __name__ == "__main__":
    app.run(debug=True)