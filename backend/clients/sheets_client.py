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

class SheetsClient:
    """Handles all Google Sheets operations."""
    
    def __init__(
        self,
        sheet_id: str = None,
        primary_key_column: str = "id",
        credentials_path: str = "credentials.json",
        token_path: str = "token.json"
    ):
        
        
        # Get configuration
        self.sheet_id = sheet_id or os.getenv('GOOGLE_SHEET_ID')
        self.primary_key_column = primary_key_column or os.getenv('PRIMARY_KEY_COLUMN', 'id')
        self.credentials_path = credentials_path
        self.token_path = token_path
        
        # Authenticate and build service
        self.service = self._authenticate()
        
        logger.info("sheets_client_initialized", sheet_id=self.sheet_id[:20], 
                    primary_key=self.primary_key_column)