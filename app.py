from flask import Flask, request, jsonify, render_template, redirect, url_for
from helpers import generate_ai_response, generate_mock_response
from config import USE_MOCK_RESPONSE, MAPMYINDIA_API_KEY, MAPMYINDIA_CLIENT_ID, MAPMYINDIA_CLIENT_SECRET
from math import pow
# from PIL import Image
# import pytesseract
import requests
import math
import os

app = Flask(__name__)

# Use environment variable or fallback to the hardcoded value as a last resort
LOCATIONIQ_API_KEY = os.getenv("LOCATIONIQ_API_KEY", "pk.0362f2355d5bdc89246e0e1a51dfd9e0")

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

# Route for the medical facilities finder page
@app.route("/medical-facilities")
def medical_facilities():
    return render_template('hospitals.html')

@app.route("/nearby-facilities")
def nearby_facilities():
    # Get parameters from the request
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    facility_type = request.args.get('type', 'hospital')

    if not lat or not lng:
        return jsonify({"error": "Latitude and longitude are required"})

    # For development/testing, use mock data if needed
    if USE_MOCK_RESPONSE:
        return generate_mock_facilities(lat, lng, facility_type)

    try:
        # Map the facility type to LocationIQ's search keywords
        keyword_mapping = {
            'hospital': 'hospital near',
            'doctor': 'doctor clinic near',
            'pharmacy': 'pharmacy near'
        }

        keyword = keyword_mapping.get(facility_type, 'hospital near')

        # Calculate viewbox for area restriction (approximately 10km radius)
        # 0.1 degrees is roughly 11km at the equator
        viewbox = f"{float(lng)-0.1},{float(lat)-0.1},{float(lng)+0.1},{float(lat)+0.1}"

        # LocationIQ API endpoints
        search_url = "https://us1.locationiq.com/v1/search"

        params = {
            'key': LOCATIONIQ_API_KEY,
            'q': keyword,
            'lat': lat,
            'lon': lng,
            'format': 'json',
            'limit': 15,
            'radius': 10000,  # 10km radius
            'dedupe': 1,      # Remove duplicates
            'viewbox': viewbox,
            'bounded': 1      # Force results within the viewbox
        }

        print(f"Searching for {keyword} near {lat}, {lng}")
        response = requests.get(search_url, params=params)

        if response.status_code != 200:
            print(f"LocationIQ API error: {response.status_code}")
            print(f"Response: {response.text}")
            return jsonify({"error": f"Failed to fetch data from LocationIQ (Status: {response.status_code})"})

        data = response.json()
        print(f"Found {len(data)} results from LocationIQ")

        facilities = []

        for place in data:
            # Calculate distance between user and facility
            distance = calculate_distance(
                float(lat), float(lng), 
                float(place['lat']), float(place['lon'])
            )
            
            # Only include facilities within 20km
            if distance <= 20:
                # Extract name from display_name (first part before the comma)
                display_name = place.get('display_name', 'Unknown Location')
                name_parts = display_name.split(',')
                short_name = name_parts[0].strip() if len(name_parts) > 0 else display_name
                
                # Create facility object
                facility = {
                    'name': short_name,
                    'address': ', '.join(name_parts[1:3]) if len(name_parts) > 2 else display_name,
                    'lat': place['lat'],
                    'lng': place['lon'],
                    'distance': round(distance, 2),
                    'phone': 'N/A'  # LocationIQ doesn't typically provide phone numbers
                }
                
                facilities.append(facility)

        print(f"Filtered to {len(facilities)} relevant facilities within 20km")
        
        # If we still don't have facilities, fall back to mock data
        if len(facilities) == 0:
            print("No nearby facilities found, falling back to mock data")
            mock_response = generate_mock_facilities(lat, lng, facility_type)
            return mock_response
            
        return jsonify({"facilities": facilities})

    except Exception as e:
        print(f"Error in nearby_facilities: {str(e)}")
        return jsonify({"error": "An error occurred while fetching nearby facilities"})

def generate_mock_facilities(lat, lng, facility_type):
    """Generate mock facility data for testing"""
    import random
    
    # Create some random facilities around the user location
    facilities = []
    
    # Map facility type to names
    type_names = {
        'hospital': ['General Hospital', 'Community Hospital', 'Medical Center', 'Emergency Care'],
        'doctor': ['Family Clinic', 'Dr. Smith Practice', 'Medical Associates', 'Health Center'],
        'pharmacy': ['City Pharmacy', 'MediStore', 'HealthDrugs', 'PharmaCare']
    }
    
    names = type_names.get(facility_type, ['Medical Facility'])
    
    # Generate 5 random facilities
    for i in range(5):
        # Create slight variations in lat/lng for the mock facilities
        # Using smaller offsets to ensure they're actually nearby (0.001 is roughly 100m)
        facility_lat = float(lat) + (random.random() - 0.5) * 0.005
        facility_lng = float(lng) + (random.random() - 0.5) * 0.005
        
        # Calculate a mock distance (0.5-3 km)
        distance = round(random.uniform(0.5, 3.0), 2)
        
        # Generate random name
        name = f"{random.choice(names)} {i+1}"
        
        # Add mock phone number
        phone = f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        
        facility = {
            'name': name,
            'address': f"{random.randint(100, 999)} Example St, City",
            'lat': facility_lat,
            'lng': facility_lng,
            'distance': distance,
            'phone': phone if random.random() > 0.3 else "N/A"  # Some facilities might not have phone numbers
        }
        
        facilities.append(facility)
    
    print(f"Generated {len(facilities)} mock facilities")
    return jsonify({"facilities": facilities})

# Helper function to calculate distance between two points
def calculate_distance(lat1, lon1, lat2, lon2):
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    
    # Haversine formula
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371  # Radius of earth in kilometers
    
    return c * r

#   @app.route("/extract-text", methods=["POST"])
# def extract_text():
#     if 'image' not in request.files:
#         return jsonify({"error": "No image uploaded"}), 400

#     image_file = request.files['image']

#     if image_file.filename == '':
#         return jsonify({"error": "Empty filename"}), 400

#     try:
#         img = Image.open(image_file)
#         text = pytesseract.image_to_string(img)
#         return jsonify({"text": text})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

#     # Perform OCR
#     text = pytesseract.image_to_string(img)
#     cleaned_text = text.strip()

#     # Check for blank or non-meaningful output (like just '\f')
#     if not cleaned_text or cleaned_text == '\f':
#         return jsonify({"error": "The image appears to be blank or contains no recognizable text."}), 400

#     lines = cleaned_text.splitlines()
#     symptoms_text = "\n".join(lines)

#     # Use the appropriate response generator based on config
#     response = generate_ai_response(symptoms_text)
    
#     print("final_response", response)

#     return jsonify({
#         "result": response
#     }), 200

if __name__ == "__main__":
    app.run(debug=True)