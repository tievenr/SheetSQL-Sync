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
    

    def _authenticate(self):
        """Handle OAuth2 authentication and return Sheets service."""
        creds = None
        
        # Check if token exists
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # Auto-refresh expired token
                creds.refresh(Request())
            else:
                # Open browser for login
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save token for next time
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        # Build Sheets API service
        service = build('sheets', 'v4', credentials=creds)
        logger.info("sheets_authenticated", token_exists=os.path.exists(self.token_path))
        return service

    def get_all_data(self) -> pd.DataFrame:
        """Fetch all data from the sheet as a DataFrame."""
        try:
            # Read all values from the sheet
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range='A:Z'  # Get all columns, all rows
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                logger.warning("sheets_empty", sheet_id=self.sheet_id[:20])
                return pd.DataFrame()
            
            # First row is header, rest is data
            headers = values[0]
            data_rows = values[1:]
            
            # Pad rows to match header length (Sheets API omits trailing empty cells)
            padded_rows = []
            for row in data_rows:
                padded_row = row + [''] * (len(headers) - len(row))  # ← ADD THIS
                padded_rows.append(padded_row)
            
            # Convert to DataFrame
            df = pd.DataFrame(data_rows, columns=headers)
            
            logger.info("sheets_data_fetched", rows=len(df), sheet_id=self.sheet_id[:20])
            return df
            
        except HttpError as e:
            logger.error("sheets_fetch_failed", error=str(e), sheet_id=self.sheet_id[:20])
            raise
    
    def _find_row_by_pk(self, pk_value: Any) -> int:
        """Find the row number for a given primary key value."""
        try:
            df = self.get_all_data()
            
            # Find row where primary key matches
            for idx, row in df.iterrows():
                if str(row[self.primary_key_column]) == str(pk_value):
                    # +2 because: DataFrame is 0-indexed, and row 1 is header
                    return idx + 2
            
            raise ValueError(f"No row found with {self.primary_key_column}={pk_value}")
            
        except Exception as e:
            logger.error("sheets_find_row_failed", pk=pk_value, error=str(e))
            raise

    def update_row_by_pk(self, pk_value: Any, data: Dict[str, Any]) -> None:
        """Update an existing row by primary key value."""
        try:
            # Find which row number has this primary key
            row_num = self._find_row_by_pk(pk_value)
            
            # Get headers to know column positions
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range='A1:Z1'
            ).execute()
            headers = result.get('values', [[]])[0]
            
            # Build update for each column that changed
            for column_name, new_value in data.items():
                if column_name in headers:
                    col_index = headers.index(column_name)
                    col_letter = chr(65 + col_index)  # A=65, B=66, etc.
                    
                    # Update single cell
                    self.service.spreadsheets().values().update(
                        spreadsheetId=self.sheet_id,
                        range=f"{col_letter}{row_num}",
                        valueInputOption='USER_ENTERED',
                        body={'values': [[new_value]]}
                    ).execute()
            
            logger.info("sheets_row_updated", pk=pk_value, row=row_num, 
                        updated_fields=list(data.keys()))
            
        except Exception as e:
            logger.error("sheets_update_failed", pk=pk_value, error=str(e))
            raise

    def insert_row(self, data: Dict[str, Any]) -> None:
        """Insert a new row at the end of the sheet."""
        try:
            # Get headers to know column order
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range='A1:Z1'
            ).execute()
            headers = result.get('values', [[]])[0]
            
            # Build row values in correct column order
            row_values = []
            for header in headers:
                row_values.append(data.get(header, ''))  # Empty string if not provided
            
            # Append row to end
            self.service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range='A:Z',
                valueInputOption='USER_ENTERED',
                body={'values': [row_values]}
            ).execute()
            
            logger.info("sheets_row_inserted", data=data)
            
        except Exception as e:
            logger.error("sheets_insert_failed", error=str(e), data=data)
            raise
    
    def delete_row_by_pk(self, pk_value: Any) -> None:
        """Delete a row by primary key value."""
        try:
            # Find which row number to delete
            row_num = self._find_row_by_pk(pk_value)
            
            # Delete the row using batchUpdate
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.sheet_id,
                body={
                    'requests': [{
                        'deleteDimension': {
                            'range': {
                                'sheetId': 0,  # First sheet
                                'dimension': 'ROWS',
                                'startIndex': row_num - 1,  # 0-indexed for API
                                'endIndex': row_num
                            }
                        }
                    }]
                }
            ).execute()
            
            logger.info("sheets_row_deleted", pk=pk_value, row=row_num)
            
        except Exception as e:
            logger.error("sheets_delete_failed", pk=pk_value, error=str(e))
            raise

    def clear_all(self) -> None:
        """Clear all data except the header row."""
        try:
            # Clear from row 2 onwards (keep header)
            self.service.spreadsheets().values().clear(
                spreadsheetId=self.sheet_id,
                range='A2:Z'  
            ).execute()
            
            logger.info("sheets_cleared", sheet_id=self.sheet_id[:20])
            
        except Exception as e:
            logger.error("sheets_clear_failed", error=str(e))
            raise


    def write_all(self, df: pd.DataFrame) -> None:
        """Overwrite all data in the sheet with DataFrame contents."""
        try:
            # Clear existing data first
            self.clear_all()
            
            # Convert DataFrame to list of lists
            values = df.values.tolist()
            
            # Write all rows at once
            self.service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range='A2:Z',
                valueInputOption='USER_ENTERED',
                body={'values': values}
            ).execute()
            
            logger.info("sheets_written", rows=len(df), sheet_id=self.sheet_id[:20])
            
        except Exception as e:
            logger.error("sheets_write_failed", error=str(e), rows=len(df))
            raise