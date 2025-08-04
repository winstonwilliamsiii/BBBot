# Bentley Bot: Fiscal Budget Dashboard

This is a Streamlit-based web application that:

- Ingests 36 months of personal and small-business income/expense data from Google Sheets.
- Syncs bank and billing transactions via QuickBooks API (or alternative financial aggregators).
- Stores and transforms data in MySQL (self-hosted or Appwrite BaaS) using Airbyte.
- Orchestrates notifications with Zapier and AI workflows with n8n.
- Presents an interactive dashboard with charts for spending categories (Shopping, Bank Fees, Miscellaneous, etc.) and upcoming-bill email alerts.
- Embeds a chatbot for macro-economic forecasts, US demographic comparisons, and global scenario analysis.

## Database Setup

The application now includes a MySQL database with the following configuration:

### Connection Details
- **Database Name**: Bentley_Budget
- **Host**: 127.0.0.1 (localhost) or mysql (Docker)
- **Port**: 3306
- **User**: root
- **Password**: rootpassword
- **MySQL Version**: 8.0.40

### Database Schema
The database includes two main tables:
1. **gdp_data**: Raw GDP data with year columns (1960-2022)
2. **gdp_yearly_data**: Normalized table for efficient querying

### Running with Docker
```bash
# Start the application with MySQL database
docker-compose up --build

# Access the application
# Web UI: http://localhost:8501
# MySQL: localhost:3306
```

# Process Flow Image

https://app.diagrams.net/#G1puqYkLeP-SrmQ8khMA-ualIAiFyEnBJj#%7B%22pageId%22%3A%22V-6in7jooW1nca1V13b-%22%7D
<img width="460" height="373" alt="image" src="https://github.com/user-attachments/assets/433b4e08-945b-4ec0-b9f9-9a7b8085e602" />
