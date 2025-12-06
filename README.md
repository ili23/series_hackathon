# series_hackathon

## Setup Instructions

### 1. Create a Virtual Environment

Create a Python virtual environment to isolate project dependencies:

```bash
python3 -m venv venv
```

### 2. Activate the Virtual Environment

**On macOS/Linux:**

```bash
source venv/bin/activate
```

**On Windows:**

```bash
venv\Scripts\activate
```

### 3. Install Dependencies

Install all required packages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 4. Run the Application

Start the Flask backend server:

```bash
python backend/app.py
```

The application will start on `http://0.0.0.0:5000` by default (or the port specified in the `PORT` environment variable).

### Optional: Environment Variables

The application uses environment variables for configuration. You can set these in a `.env` file or export them in your shell:

- `KAFKA_BOOTSTRAP_SERVERS` - Kafka server address
- `KAFKA_TOPIC` - Kafka topic name
- `KAFKA_CONSUMER_GROUP` - Kafka consumer group
- `KAFKA_API_KEY` - Kafka API key
- `KAFKA_API_SECRET` - Kafka API secret
- `PORT` - Flask server port (default: 5000)
- `FLASK_DEBUG` - Enable debug mode (default: False)
- `SERIES_API_BASE_URL` - Series API base URL
- `SENDER_NUMBER` - Sender phone number

If not set, the application will use default values from `backend/config.py`.

## Running Tests

To run the test suite:

```bash
pytest
```

To run tests with coverage:

```bash
pytest --cov=backend
```
