from flask import Flask, render_template, request, jsonify
import os
import random
import re
from collections import Counter

app = Flask(__name__)

# Set to True to use mock responses (no API calls)
USE_MOCK_RESPONSE = True

# Initialize the OpenAI client if needed
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "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"))
except ImportError:
    client = None
    if not USE_MOCK_RESPONSE:
        print("Warning: OpenAI package not installed but USE_MOCK_RESPONSE is False")

# Database of health conditions organized by body systems
mock_health_database = {
    "respiratory": [
        "Common Cold", "Seasonal Allergies", "Bronchitis", 
        "Asthma", "Sinusitis", "Upper Respiratory Infection"
    ],
    "digestive": [
        "Gastroenteritis", "Acid Reflux", "Irritable Bowel Syndrome", 
        "Food Poisoning", "Indigestion", "Gastritis"
    ],
    "nervous": [
        "Tension Headache", "Migraine", "Stress", 
        "Anxiety", "Insomnia", "Vertigo"
    ],
    "musculoskeletal": [
        "Muscle Strain", "Joint Inflammation", "Tendonitis", 
        "Arthritis", "Back Pain", "Fibromyalgia"
    ],
    "skin": [
        "Contact Dermatitis", "Eczema", "Allergic Reaction", 
        "Heat Rash", "Fungal Infection", "Hives"
    ],
    "general": [
        "Fatigue", "Viral Infection", "Dehydration", 
        "Vitamin Deficiency", "Minor Infection", "Seasonal Illness"
    ]
}

# Advice templates that can be customized
advice_templates = [
    "Rest and stay hydrated. {specific_advice}",
    "Consider over-the-counter remedies like {otc_options}. {additional_advice}",
    "Apply {treatment_method} to affected areas. {additional_advice}",
    "Monitor symptoms and {monitoring_advice}",
    "Avoid {avoid_items} until symptoms improve. {additional_advice}"
]

# Specific advice by system
specific_advice = {
    "respiratory": [
        "Use a humidifier to ease congestion", 
        "Try saline nasal spray to clear sinuses",
        "Honey in warm water may help soothe a cough or sore throat",
        "Keep your head elevated while sleeping to reduce congestion"
    ],
    "digestive": [
        "Eat smaller, more frequent meals", 
        "Stick to bland foods like bananas, rice, and toast",
        "Avoid spicy, acidic or fatty foods temporarily",
        "Try probiotics to help restore gut balance"
    ],
    "nervous": [
        "Practice relaxation techniques like deep breathing", 
        "Minimize screen time, especially before bed",
        "Try a cold or warm compress on the forehead for headaches",
        "Maintain a regular sleep schedule"
    ],
    "musculoskeletal": [
        "Apply ice for the first 48 hours, then switch to heat", 
        "Consider gentle stretching exercises",
        "Avoid activities that worsen the pain",
        "Make sure to maintain good posture"
    ],
    "skin": [
        "Avoid scratching affected areas", 
        "Use gentle, fragrance-free soaps",
        "Apply a cold compress to reduce itching",
        "Keep the affected area clean and dry"
    ],
    "general": [
        "Make sure you're getting enough sleep", 
        "Consider a balanced diet rich in nutrients",
        "Stay active with light exercise if you feel up to it",
        "Take time to reduce stress through mindfulness or relaxation"
    ]
}

# OTC options by system
otc_options = {
    "respiratory": "decongestants, antihistamines, or throat lozenges",
    "digestive": "antacids, anti-diarrheal medication, or digestive enzymes",
    "nervous": "acetaminophen, ibuprofen, or tension relief products",
    "musculoskeletal": "pain relievers, anti-inflammatory medication, or muscle rubs",
    "skin": "hydrocortisone cream, calamine lotion, or antihistamines",
    "general": "multivitamins, electrolyte solutions, or mild pain relievers"
}

# Items to avoid by system
avoid_items = {
    "respiratory": "allergens, cold air, and irritants like smoke",
    "digestive": "dairy, caffeine, alcohol, and spicy foods",
    "nervous": "caffeine, alcohol, and high-stress situations",
    "musculoskeletal": "high-impact activities, heavy lifting, and prolonged sitting",
    "skin": "harsh soaps, hot water, and known allergens",
    "general": "excessive exertion, dehydrating beverages, and irregular sleep patterns"
}

# Monitoring advice by system
monitoring_advice = {
    "respiratory": "seek medical attention if breathing becomes difficult or symptoms worsen after 7-10 days",
    "digestive": "consult a doctor if symptoms persist beyond 48 hours or include severe pain or blood",
    "nervous": "consider medical help if headaches are severe, sudden, or accompanied by other symptoms",
    "musculoskeletal": "see a healthcare provider if pain is severe, doesn't improve within a week, or limits mobility",
    "skin": "visit a doctor if the rash spreads rapidly, blisters, or is accompanied by fever",
    "general": "contact a healthcare professional if symptoms worsen or don't improve within a few days"
}

# Additional generic advice pieces
additional_advice = [
    "If symptoms persist for more than a few days, consider consulting a healthcare professional.",
    "Make sure to get adequate rest while your body recovers.",
    "Stay hydrated by drinking plenty of water throughout the day.",
    "Consider monitoring your symptoms and keeping a log to share with your doctor if needed.",
    "Wash hands frequently to prevent spreading any potential infection."
]

# List of medically irrelevant words that should not trigger a medical response
irrelevant_keywords = [
    "hello", "test", "testing", "hi", "hey", "what", "how", "why", "when", "computer", "phone",
    "website", "app", "check", "try", "example", "sample", "nothing", "random", "asdf", "qwerty",
    "garbage", "nonsense", "lorem", "ipsum", "foo", "bar", "baz", "xyz", "abc", "junk", "blah",
    "help", "please", "thanks", "thank", "you", "okay", "ok", "good", "bad", "yes", "no", "maybe",
    "program", "software", "system", "device", "desktop", "laptop", "tablet", "game", "play", "fun"
]

# Symptom keywords with their weights (higher weight = more significant)
symptom_keywords = {
    "respiratory": {
        "cough": 5, "breathing": 5, "breath": 4, "sneeze": 4, "sneezing": 5, "nose": 3, 
        "runny nose": 5, "stuffy nose": 5, "sore throat": 5, "throat": 4, "lung": 4, 
        "chest": 4, "sinus": 5, "nasal": 4, "phlegm": 5, "congestion": 5, "wheeze": 5,
        "mucus": 5, "difficulty breathing": 6, "shortness of breath": 6
    },
    "digestive": {
        "stomach": 4, "nausea": 5, "vomit": 5, "vomiting": 5, "diarrhea": 5, "constipation": 5, 
        "bowel": 4, "digest": 3, "digestion": 4, "abdominal": 4, "abdomen": 4, "gut": 4, 
        "food": 2, "appetite": 4, "bloating": 5, "gas": 4, "acid reflux": 5, "heartburn": 5,
        "stomachache": 5, "belching": 5, "indigestion": 5
    },
    "nervous": {
        "headache": 5, "migraine": 5, "dizzy": 5, "dizziness": 5, "nerve": 3, "anxiety": 5, 
        "anxious": 5, "stress": 4, "stressed": 4, "sleep": 3, "insomnia": 5, "depression": 5, 
        "depressed": 5, "tired": 3, "fatigue": 4, "exhausted": 4, "exhaustion": 4,
        "vertigo": 5, "lightheaded": 5, "confusion": 5, "memory": 4
    },
    "musculoskeletal": {
        "muscle": 4, "joint": 4, "pain": 3, "ache": 4, "aching": 4, "back": 3, "back pain": 5, 
        "knee": 4, "shoulder": 4, "neck": 4, "strain": 4, "sprain": 5, "sore": 4, "soreness": 4,
        "stiffness": 5, "cramp": 5, "swelling": 4, "inflammation": 5, "arthritis": 5, "fibromyalgia": 5
    },
    "skin": {
        "rash": 5, "itch": 4, "itching": 5, "skin": 3, "bump": 4, "hive": 5, "hives": 5, 
        "redness": 4, "red": 3, "swelling": 4, "dry": 3, "dryness": 4, "flaky": 5, "irritation": 4,
        "irritated": 4, "burning": 4, "acne": 5, "eczema": 5, "dermatitis": 5, "blister": 5
    },
    "general": {
        "fever": 5, "chills": 5, "sweating": 4, "malaise": 5, "weakness": 4, "weak": 3,
        "fatigue": 4, "tired": 3, "weight loss": 5, "weight gain": 5, "dehydration": 5,
        "thirst": 4, "appetite": 4, "swollen": 4, "infection": 5, "sick": 3, "illness": 4
    }
}

# Combinations of symptoms that indicate higher urgency
high_urgency_combinations = [
    ["fever", "chest pain", "difficulty breathing"],
    ["chest pain", "arm pain", "shortness of breath"],
    ["sudden", "severe", "headache"],
    ["difficulty", "breathing"],
    ["chest", "pain"],
    ["high", "fever"],
    ["severe", "pain"],
    ["unable", "move"],
    ["blood", "stool"],
    ["blood", "vomit"],
    ["unconscious"],
    ["seizure"],
    ["stroke"],
    ["heart", "attack"],
    ["anaphylaxis"],
    ["allergy", "swelling", "throat"]
]

def is_medically_relevant(text):
    """Check if the text contains medically relevant information"""
    # Convert to lowercase and remove punctuation
    text = re.sub(r'[^\w\s]', '', text.lower())
    words = text.split()
    
    # Count how many words match our irrelevant keywords
    irrelevant_count = sum(1 for word in words if word in irrelevant_keywords)
    
    # If more than half of the words are irrelevant, or the text is too short, consider it irrelevant
    if len(words) < 3 or irrelevant_count > len(words) / 2:
        return False
        
    # Check if there are any medically relevant words at all
    all_symptom_words = set()
    for system in symptom_keywords:
        all_symptom_words.update(symptom_keywords[system].keys())
    
    # Look for any medical terms in the text
    for symptom in all_symptom_words:
        if symptom in text:
            return True
            
    # Look for common symptom phrases
    common_phrases = ["feel sick", "not feeling well", "have pain", "hurts", "having trouble"]
    for phrase in common_phrases:
        if phrase in text:
            return True
            
    return False

def check_urgency(text):
    """Check if the symptoms indicate a high urgency situation"""
    text = text.lower()
    
    for combo in high_urgency_combinations:
        # Check if all words in the combo are in the text
        if all(word in text for word in combo):
            return "Severe"
    
    # Count how many times severe keywords appear
    severe_keywords = ["severe", "extreme", "unbearable", "worst", "intense", "excruciating"]
    severity_count = sum(1 for word in severe_keywords if word in text)
    
    if severity_count >= 2:
        return "Severe"
    elif severity_count == 1:
        return "Moderate"
        
    return None  # Let the regular system determine urgency

def map_symptoms_to_system(symptoms):
    """Map symptoms to body systems with a more sophisticated approach"""
    if not symptoms or not isinstance(symptoms, str):
        return ["general"]
        
    text = symptoms.lower()
    system_scores = {system: 0 for system in symptom_keywords}
    
    # Score each system based on the presence of keywords
    for system, keywords in symptom_keywords.items():
        for keyword, weight in keywords.items():
            if keyword in text:
                system_scores[system] += weight
    
    # Get systems with non-zero scores, sorted by score (highest first)
    matched_systems = [system for system, score in sorted(
        system_scores.items(), key=lambda x: x[1], reverse=True) if score > 0]
    
    # If no matches, return general
    if not matched_systems:
        return ["general"]
    
    # Return the top 2 systems if multiple matched
    return matched_systems[:2]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/check-symptoms', methods=['POST'])
def check_symptoms():
    symptoms = request.form.get('symptoms', '').strip()
    
    # Check if the input is empty or too short
    if not symptoms or len(symptoms) < 3:
        return jsonify({
            "result": "Please provide more details about your symptoms."
        })
    
    # Check if the input is medically relevant
    if not is_medically_relevant(symptoms):
        return jsonify({
            "result": "I couldn't identify any medical symptoms in your description. Please provide more specific details about how you're feeling physically."
        })
    
    if USE_MOCK_RESPONSE:
        # Check for high urgency situations first
        custom_urgency = check_urgency(symptoms)
        
        # Get the relevant body systems based on symptoms
        relevant_systems = map_symptoms_to_system(symptoms)
        
        # Select the primary system (highest score)
        primary_system = relevant_systems[0]
        
        # Generate urgency level with intelligent assessment
        if custom_urgency:
            urgency = custom_urgency
        elif primary_system in ["respiratory", "nervous"]:
            urgency_options = ["Mild", "Mild", "Moderate", "Moderate", "Severe"]
            urgency = random.choice(urgency_options)
        else:
            urgency_options = ["Mild", "Mild", "Mild", "Moderate", "Moderate"]
            urgency = random.choice(urgency_options)
        
        # Add emergency advice for severe cases
        emergency_advice = ""
        if urgency == "Severe":
            emergency_advice = "\n\nIMPORTANT: If you're experiencing severe symptoms, please consider seeking immediate medical attention or calling emergency services."
        
        # Select conditions from the primary system
        conditions = random.sample(mock_health_database[primary_system], 3)
        
        # Generate advice
        advice_list = []
        
        # Add system-specific advice
        specific = random.choice(specific_advice[primary_system])
        advice_list.append(f"Rest and stay hydrated. {specific}")
        
        # Add OTC advice
        otc = otc_options[primary_system]
        advice_list.append(f"Consider over-the-counter remedies like {otc} as appropriate.")
        
        # Add monitoring advice
        advice_list.append(f"Monitor symptoms and {monitoring_advice[primary_system]}.")
        
        # Format the mock response
        mock_result = f"""Based on the symptoms: "{symptoms}", here's some information:

1. Three possible health conditions (not a diagnosis):
   - {conditions[0]}
   - {conditions[1]}
   - {conditions[2]}

2. Urgency level: {urgency}

3. Simple advice:
   - {advice_list[0]}
   - {advice_list[1]}
   - {advice_list[2]}{emergency_advice}

DISCLAIMER: This is not a medical diagnosis. Always consult a healthcare professional for proper evaluation and treatment.
"""
        return jsonify({"result": mock_result})
    
    # If not using mock response, use OpenAI
    if client:
        prompt = f"""
        The user has the following symptoms: {symptoms}.
        Provide:
        1. Three possible health conditions (not a diagnosis),
        2. Urgency level (Mild / Moderate / Severe),
        3. Simple advice (home remedies or doctor visit).
        
        Add a disclaimer about not being a medical diagnosis.
        If the symptoms are vague or not medical in nature, ask for more specific information.
        """
        
        try:
            # Using the updated ChatCompletion API
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful medical assistant. You do not diagnose but provide general information."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=400
            )
            
            # Extract the response and send it back to the user
            result = response.choices[0].message.content.strip()
            return jsonify({"result": result})
        except Exception as e:
            return jsonify({"error": str(e)})
    else:
        return jsonify({"error": "OpenAI client not configured"})

if __name__ == '__main__':
    app.run(debug=True)