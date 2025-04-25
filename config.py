import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Set to True for development/testing without making API calls
# Set to False to use the actual Anthropic API
USE_MOCK_RESPONSE = False

# Get API keys from environment variables
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MAPMYINDIA_API_KEY = os.getenv("MAPMYINDIA_API_KEY")
MAPMYINDIA_CLIENT_ID = os.getenv("MAPMYINDIA_CLIENT_ID")
MAPMYINDIA_CLIENT_SECRET = os.getenv("MAPMYINDIA_CLIENT_SECRET")
LOCATIONIQ_API_KEY = os.getenv("LOCATIONIQ_API_KEY", "pk.0362f2355d5bdc89246e0e1a51dfd9e0")

# Verify that the API keys are available
if not ANTHROPIC_API_KEY and not USE_MOCK_RESPONSE:
    print("WARNING: Anthropic API key not found and mock responses are disabled.")
    print("Either add your API key to the .env file or set USE_MOCK_RESPONSE to True.")

if not LOCATIONIQ_API_KEY:
    print("WARNING: LocationIQ API key not found. The medical facilities finder feature will not work properly.")
    print("Add your LocationIQ API key to the .env file.")