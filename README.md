# Store Monitoring Backend

This project is a backend system designed to monitor the uptime and downtime of restaurant stores based on periodic status polls. It provides a RESTful API to trigger report generation and retrieve the completed reports in CSV format.

The system is built to handle complex time-series data, including timezone conversions and data interpolation, to provide accurate business intelligence for restaurant owners.

---

## Features

* **Asynchronous API:** Built with FastAPI to handle requests efficiently, featuring a non-blocking, trigger-and-poll architecture for report generation.
* **Database Integration:** Uses SQLAlchemy ORM to model and interact with a SQLite database for persistent data storage.
* **Timezone-Aware Logic:** Correctly converts and compares store-local business hours with UTC status polls.
* **Data Interpolation:** Implements a sane logic to extrapolate uptime/downtime for periods between status polls.
* **Background Tasks:** Offloads the heavy report generation process to a background task, ensuring the API remains responsive.
* **Efficient Data Ingestion:** Includes a script that uses bulk-insertion techniques for fast initial data loading from CSV files.
* **Automated API Documentation:** Provides interactive API documentation via Swagger UI and ReDoc.

---

## Tech Stack

* **Language:** Python 3.9+
* **Framework:** FastAPI
* **Database:** SQLite
* **ORM:** SQLAlchemy
* **Data Handling:** Pandas
* **Timezones:** Pytz

---

## Project Structure

The project follows a logical and modular structure to separate concerns:

```
/
|-- /app                    # Main application source code
|   |-- __init__.py
|   |-- crud.py             # Database query functions (Create, Read, Update)
|   |-- database.py         # Database engine and session setup
|   |-- main.py             # FastAPI app, API endpoints
|   |-- models.py           # SQLAlchemy database models (schemas)
|   |-- report_logic.py     # Core business logic for report generation
|
|-- /data                   # Contains the source CSV files
|   |-- store_status.csv
|   |-- menu_hours.csv
|   |-- timezones.csv
|
|-- /generated_reports      # Output directory for CSV reports
|
|-- ingest_data.py          # Standalone script to populate the database
|-- requirements.txt        # Project dependencies
|-- README.md               # This file
```

---

## Setup and Installation

Follow these steps to set up and run the project locally.

### 1. Prerequisites

* Python 3.9 or newer
* `pip` package manager

### 2. Clone the Repository

```bash
git clone https://github.com/CoderKaushik/store-monitoring-system
cd store-monitoring-system
```

### 3. Create a Virtual Environment

It's highly recommended to use a virtual environment to manage project dependencies.

```bash
# Create the virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate
```

### 4. Install Dependencies

Install all required packages from the requirements.txt file.

```bash
pip install -r requirements.txt
```

### Running the Application

The application requires a two-step process to run: first ingest the data, then start the API server.

#### Step 1: Ingest Data

Place your source CSV files (`store_status.csv`, `menu_hours.csv`, `timezones.csv`) inside the `/data` directory. Then, run the ingestion script to populate the SQLite database.

This is a one-time step.

```bash
python ingest_data.py
```

This will create a `store_monitoring.db` file in your project root.

#### Step 2: Start the API Server

Run the Uvicorn server to start the FastAPI application.

```bash
uvicorn app.main:app --reload
```

The API will now be running at [http://127.0.0.1:8000](http://127.0.0.1:8000). The `--reload` flag enables hot-reloading for development.

#### Step 3: Accessing the API

You can interact with the API using any HTTP client or by using the auto-generated interactive documentation:

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## API Endpoints

### 1. Trigger Report Generation

- **Endpoint:** `POST /trigger_report`
- **Description:** Initiates the report generation process in the background.
- **Response:**
    ```json
    {
      "report_id": "a-unique-random-string"
    }
    ```

### 2. Get Report Status / Download Report

- **Endpoint:** `GET /get_report/{report_id}`
- **Description:** Polls the status of the report. If complete, it returns the CSV file.
- **Response (Running):**
    ```json
    {
      "status": "Running"
    }
    ```
- **Response (Complete):**
    - The API will return the generated CSV file for download.

---

## Core Logic Explained

The main challenge of this project was to accurately calculate uptime/downtime within business hours. The approach taken was:

- **Timezone Normalization:** All local business hours are converted to timezone-aware UTC datetime intervals for each day in the reporting period. This creates a universal timeline for comparison.
- **Data Interpolation:** The status of a store at any given time is assumed to be the status of its most recent poll. This allows for the calculation of uptime/downtime for the entire duration between two polls.
- **Interval Overlap:** The core calculation finds the intersection between the "status intervals" (from polls) and the "business hour intervals" to determine the final uptime and downtime values.

---

## requirements.txt

Create a file named `requirements.txt` in your project root and add the following content:

```text
fastapi
uvicorn[standard]
sqlalchemy
pandas
pytz