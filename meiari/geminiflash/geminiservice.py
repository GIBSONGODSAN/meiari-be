import google.generativeai as genai
from django.conf import settings

# Configure the API key
genai.configure(api_key=settings.GOOGLE_GEMINI_API_KEY)

def get_gemini_response(prompt):
    """
    Function to interact with Gemini Flash API.
    """
    model = genai.GenerativeModel("gemini-1.5-flash")  # Use "gemini-pro" or "gemini-flash"
    response = model.generate_content(prompt)
    return response.text

def sample_gemini_response(sender, receiver, content_body_1, content_body_2):
    """
    Function to generate a sample response from Gemini Flash API.
    """
    prompt = f"From: {sender}\nTo: {receiver}\n\n{content_body_1}\n\n{content_body_2} create a report using this data."
    response = get_gemini_response(prompt)
    return response
