# Google Sheets ↔ MySQL Bidirectional Sync

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/Docker-Required-2496ED.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A robust, production-ready Python system that automatically synchronizes data between MySQL databases and Google Sheets in real-time. Perfect for teams that need to bridge the gap between technical databases and collaborative spreadsheets.

## 🌟 Features

- ** Bidirectional Sync**: Changes in either MySQL or Google Sheets are automatically reflected in the other
- ** Real-time Updates**: Configurable sync intervals (default: 5 seconds) ensure near-instant data consistency
- ** Smart Conflict Resolution**: Timestamp-based "last-write-wins" strategy handles simultaneous edits
- ** Error Resilience**: Gracefully handles network issues, incomplete data, and API failures
- ** Status Tracking**: Monitor sync cycles, conflicts resolved, and error states
- ** Change Detection**: Efficiently detects INSERT, UPDATE, and DELETE operations
- ** Structured Logging**: JSON-formatted logs for easy debugging and monitoring

## 🏗️ Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│                 │         │                  │         │                 │
│  MySQL Database │◄────────┤   Sync Engine    ├────────►│  Google Sheets  │
│                 │         │                  │         │                 │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                     │
                            ┌────────┴────────┐
                            │                 │
                      ┌─────▼──────┐    ┌─────▼──────┐
                      │  Change    │    │  Conflict  │
                      │  Detector  │    │  Resolver  │
                      └────────────┘    └────────────┘
```

**Core Components:**
- **Sync Engine**: Orchestrates the entire sync process with configurable intervals
- **MySQL Client**: Handles database operations with connection pooling via SQLAlchemy
- **Sheets Client**: Manages Google Sheets API authentication and operations
- **Change Detector**: Compares data snapshots to identify deltas (INSERT/UPDATE/DELETE)
- **Conflict Resolver**: Resolves conflicts using timestamp-based last-write-wins strategy

##  Prerequisites

- **Python 3.8+**
- **Docker & Docker Compose** (for MySQL)
- **Google Cloud Project** with Sheets API enabled
- **OAuth 2.0 Credentials** from Google Cloud Console

##  Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/google-sheets-mysql-sync.git
cd google-sheets-mysql-sync
```

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 3. Set Up Google Sheets API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Google Sheets API**
4. Create OAuth 2.0 credentials:
   - Go to **APIs & Services** → **Credentials**
   - Click **Create Credentials** → **OAuth client ID**
   - Choose **Desktop app** as application type
   - Download the JSON file and save it as `credentials.json` in the project root

5. Create a Google Sheet:
   - Create a new spreadsheet in Google Sheets
   - Add headers in the first row: `id`, `name`, `email`, `status`, `last_modified`
   - Copy the Sheet ID from the URL: `https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit`

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Google Sheets Configuration
GOOGLE_SHEET_ID=your_sheet_id_here
GOOGLE_CREDENTIALS_PATH=credentials.json
PRIMARY_KEY_COLUMN=id

# MySQL Configuration  
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=rootpassword
MYSQL_DATABASE=syncdb
MYSQL_TABLE=synced_data

# Sync Configuration
SYNC_INTERVAL_SECONDS=5
```

### 5. Start MySQL Database

```bash
docker-compose up -d
```

This will:
- Start a MySQL 8.0 container
- Create the `syncdb` database
- Initialize the `synced_data` table with sample data
- Expose MySQL on port 3306


### 6. Run the Real Sync Engine

Once you've configured everything:

```bash
python test_sync_engine.py
```

The sync engine will:
1. Perform initial sync (MySQL → Sheets)
2. Start continuous bidirectional sync every 5 seconds
3. Display real-time status updates
4. Press `Ctrl+C` to stop gracefully

##  Usage Examples

### Basic Sync Setup

```python
from backend.clients import MySQLClient, SheetsClient
from backend.core import SyncEngine

# Initialize clients
mysql_client = MySQLClient()
sheets_client = SheetsClient()

# Create sync engine
engine = SyncEngine(
    mysql_client=mysql_client,
    sheets_client=sheets_client,
    sync_interval=5,  # Sync every 5 seconds
    initial_sync_source="mysql"  # Copy from MySQL to Sheets first
)

# Start syncing (runs indefinitely)
engine.start()
```

### Custom Configuration

```python
# Custom MySQL configuration
mysql_client = MySQLClient(
    host="db.example.com",
    port=3306,
    user="admin",
    password="secret",
    database="production",
    table="users",
    primary_key="user_id"
)

# Custom Sheets configuration
sheets_client = SheetsClient(
    sheet_id="your-sheet-id",
    primary_key_column="user_id",
    credentials_path="custom_credentials.json"
)
```

### Monitoring Sync Status

```python
# Check sync status
status = engine.status

print(f"Running: {status.is_running}")
print(f"Total syncs: {status.sync_count}")
print(f"Last sync: {status.last_sync_time}")
print(f"Conflicts resolved: {status.conflicts_resolved}")
print(f"Last error: {status.last_error}")
```

##  Testing

### Manual Testing (Recommended)

The best way to see the sync in action is to manually test it yourself. Here's how:

#### 1. Start the Sync Engine

```bash
python test_sync_engine.py
```

This will start syncing every 5 seconds. Leave it running in one terminal.

#### 2. Test MySQL Operations

Open a new terminal and connect to the Docker MySQL container:

```bash
# Connect to MySQL container
docker exec -it sheets_mysql_sync_db mysql -uroot -prootpassword syncdb

# Or use this one-liner to run queries directly
docker exec -it sheets_mysql_sync_db mysql -uroot -prootpassword syncdb -e "YOUR_QUERY_HERE"
```

**View all data:**
```bash
docker exec -it sheets_mysql_sync_db mysql -uroot -prootpassword syncdb -e "SELECT * FROM synced_data;"
```

**Insert a new row:**
```bash
docker exec -it sheets_mysql_sync_db mysql -uroot -prootpassword syncdb -e "INSERT INTO synced_data (name, email, status) VALUES ('June', 'june@test.com', 'active');"
```

**Update a row:**
```bash
docker exec -it sheets_mysql_sync_db mysql -uroot -prootpassword syncdb -e "UPDATE synced_data SET name='January UPDATED' WHERE id=1;"
```

**Delete a row:**
```bash
docker exec -it sheets_mysql_sync_db mysql -uroot -prootpassword syncdb -e "DELETE FROM synced_data WHERE id=5;"
```

**Count rows:**
```bash
docker exec -it sheets_mysql_sync_db mysql -uroot -prootpassword syncdb -e "SELECT COUNT(*) FROM synced_data;"
```

#### 3. Test Google Sheets Operations

1. Open your Google Sheet in a browser
2. Make changes directly in the spreadsheet:
   - Edit a name or email in any row
   - Delete a row
   - Add a new row at the bottom
3. Watch the terminal where `test_sync_engine.py` is running
4. Within 5 seconds, your changes should sync to MySQL

#### 4. Verify Sync

**Check MySQL reflects your Sheet changes:**
```bash
docker exec -it sheets_mysql_sync_db mysql -uroot -prootpassword syncdb -e "SELECT * FROM synced_data ORDER BY id;"
```

**Check your Google Sheet reflects MySQL changes:**
- Just refresh your browser tab with the Sheet open

#### 5. Test Conflict Resolution

Try this to see the last-write-wins strategy in action:

1. **In MySQL:** Update row 2's name to "MySQL Version"
```bash
docker exec -it sheets_mysql_sync_db mysql -uroot -prootpassword syncdb -e "UPDATE synced_data SET name='MySQL Version' WHERE id=2;"
```

2. **Immediately in Sheets:** Update the same row 2's name to "Sheets Version"

3. **Watch the sync logs:** The version with the newer `last_modified` timestamp wins!


##  Project Structure

```
google-sheets-mysql-sync/
├── backend/
│   ├── clients/
│   │   ├── mysql_client.py      # MySQL database operations
│   │   └── sheets_client.py     # Google Sheets API operations
│   ├── core/
│   │   ├── change_detector.py   # Detects data changes
│   │   ├── conflict_resolver.py # Resolves conflicts
│   │   └── sync_engine.py       # Main sync orchestrator
│   └── utils/
│       ├── logger.py            # Structured logging
│       └── types.py             # Data models and enums
├── logs/                        # Auto-generated log files
├── credentials.json             # Google OAuth credentials (gitignored)
├── token.json                   # OAuth token (auto-generated, gitignored)
├── docker-compose.yml           # MySQL container setup
├── init.sql                     # Database schema and sample data
├── requirements.txt             # Python dependencies
├── .env                         # Configuration (gitignored)
├── demo.py                      # Interactive demo script
├── test_sync_engine.py          # End-to-end test
└── README.md                    # This file
```

##  Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_SHEET_ID` | Your Google Sheet ID from the URL | Required |
| `PRIMARY_KEY_COLUMN` | Column used as primary key | `id` |
| `MYSQL_HOST` | MySQL server hostname | `localhost` |
| `MYSQL_PORT` | MySQL server port | `3306` |
| `MYSQL_USER` | Database username | `root` |
| `MYSQL_PASSWORD` | Database password | Required |
| `MYSQL_DATABASE` | Database name | `syncdb` |
| `MYSQL_TABLE` | Table to sync | `synced_data` |
| `SYNC_INTERVAL_SECONDS` | Seconds between sync cycles | `5` |

### Data Schema

The default schema includes:

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT | Primary key (auto-increment) |
| `name` | VARCHAR(100) | Name field |
| `email` | VARCHAR(100) | Email field |
| `status` | ENUM | `active` or `inactive` |
| `last_modified` | TIMESTAMP | Auto-updated timestamp for conflict resolution |

**Note**: The `last_modified` column is critical for conflict resolution. It must be present and automatically updated.


##  Contributing

Contributions are welcome! Here's how to get started:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `python test_sync_engine.py`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request


##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Made with ❤️ for teams that sync data**
