import os
import pickle
from typing import Any, Dict, List, Optional
import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

from backend.utils import logger

# Load environment variables
load_dotenv()

# Google Sheets API scope 
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']