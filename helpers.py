import os
from anthropic import Anthropic
from config import ANTHROPIC_API_KEY, USE_MOCK_RESPONSE

# Initialize the Anthropic client with your API key
client = Anthropic(api_key=ANTHROPIC_API_KEY)

def generate_ai_response(user_input):
    """Generate a response using Anthropic's Claude API"""
    try:
        # Create a specific prompt for the symptom checker
        symptom_prompt = f"""
        Based on the following symptoms, provide a brief assessment:
        
        {user_input}
        
        Format your response with:
        1. A summary of the symptoms
        2. Urgency level (Mild, Moderate, or Severe)
        3. A recommendation
        """
        
        # Make the API call
        response = client.messages.create(
            model="claude-3-haiku-20240307",  # You can also use other Claude models
            max_tokens=300,
            messages=[
                {
                    "role": "user", 
                    "content": symptom_prompt
                }
            ]
        )
        
        # Extract and return the response content
        return response.content[0].text
    except Exception as e:
        return f"Sorry, I couldn't analyze your symptoms: {str(e)}"

# Mock response function for development/testing
def generate_mock_response(user_input):
    """Generate a dynamic mock response based on the symptoms provided"""
    # Convert to lowercase for easier matching
    symptoms = user_input.lower()
    
    # Define some symptom categories for matching
    respiratory = ['cough', 'breathing', 'short of breath', 'shortness of breath', 'wheeze']
    digestive = ['stomach', 'nausea', 'vomit', 'diarrhea', 'constipation', 'abdomen', 'abdominal']
    head_related = ['headache', 'migraine', 'dizziness', 'vertigo', 'head', 'vision']
    pain = ['pain', 'ache', 'sore', 'hurt', 'aching']
    fever = ['fever', 'temperature', 'chills', 'sweating']
    skin = ['rash', 'itchy', 'itch', 'skin', 'hives', 'red', 'swelling']
    emergency = ['chest pain', 'cannot breathe', 'unconscious', 'passed out', 
                'stroke', 'numbness', 'seizure', 'allergic reaction']
    
    # Evaluate urgency level
    urgency = "Mild"
    
    # Check for emergency symptoms
    if any(term in symptoms for term in emergency):
        urgency = "Severe"
    # Check for fever combined with other symptoms
    elif any(term in symptoms for term in fever) and (
        any(term in symptoms for term in respiratory) or 
        any(term in symptoms for term in digestive)):
        urgency = "Moderate"
    # Check for multiple symptom categories
    elif sum(any(term in symptoms for term in category) for category in 
            [respiratory, digestive, head_related, pain, fever, skin]) >= 3:
        urgency = "Moderate"
    
    # Generate response based on symptom categories
    response_parts = ["Based on your symptoms:\n\n"]
    
    # Extract mentioned symptoms
    mentioned_symptoms = []
    
    if any(term in symptoms for term in respiratory):
        respiratory_symptoms = [term for term in respiratory if term in symptoms]
        mentioned_symptoms.extend(respiratory_symptoms)
        if "cough" in symptoms:
            if "dry" in symptoms:
                mentioned_symptoms.append("dry cough")
            elif "phlegm" in symptoms or "mucus" in symptoms:
                mentioned_symptoms.append("productive cough")
    
    if any(term in symptoms for term in digestive):
        digestive_symptoms = [term for term in digestive if term in symptoms]
        mentioned_symptoms.extend(digestive_symptoms)
    
    if any(term in symptoms for term in head_related):
        head_symptoms = [term for term in head_related if term in symptoms]
        mentioned_symptoms.extend(head_symptoms)
    
    if any(term in symptoms for term in fever):
        mentioned_symptoms.append("fever")
    
    if any(term in symptoms for term in skin):
        skin_symptoms = [term for term in skin if term in symptoms]
        mentioned_symptoms.extend(skin_symptoms)
    
    # If we didn't match any specific symptoms, use their input
    if not mentioned_symptoms:
        response_parts.append(f"Symptoms: {user_input}\n")
    else:
        # Remove duplicates and format nicely
        unique_symptoms = list(set(mentioned_symptoms))
        response_parts.append(f"Symptoms: {', '.join(unique_symptoms)}\n")
    
    # Add urgency level
    response_parts.append(f"Urgency level: {urgency}\n")
    
    # Add recommendations based on urgency
    if urgency == "Severe":
        response_parts.append("Recommendation: Please seek immediate medical attention. Consider visiting an emergency room or calling emergency services.")
    elif urgency == "Moderate":
        response_parts.append("Recommendation: You should consult with a healthcare provider within the next 24-48 hours. These symptoms warrant professional evaluation.")
    else:  # Mild
        response_parts.append("Recommendation: Monitor your symptoms. Rest, stay hydrated, and use over-the-counter medications as appropriate. If symptoms worsen or persist for more than a few days, consult with a healthcare provider.")
    
    # Add disclaimer
    response_parts.append("\nNote: This is an AI-generated assessment and should not replace professional medical advice.")
    
    return "\n".join(response_parts)