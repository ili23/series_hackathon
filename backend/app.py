"""
Series iMessage Service Backend
A Flask backend that consumes Kafka events from the Series iMessage Service
"""
import logging
from flask import Flask
from config import FLASK_CONFIG
from kafka_client import initialize_kafka, close_kafka_connections
from event_handlers import process_kafka_event
from routes import register_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Reduce Kafka library verbosity (only show WARNING and above)
logging.getLogger('kafka').setLevel(logging.WARNING)

# Initialize Flask app
app = Flask(__name__)

# Register routes
register_routes(app)

# Initialize Kafka on app startup
initialize_kafka(process_kafka_event)

# Cleanup on shutdown
@app.teardown_appcontext
def teardown_kafka(exception):
    """Close Kafka connections on app shutdown"""
    close_kafka_connections()


if __name__ == '__main__':
    # Run Flask app
    app.run(
        host=FLASK_CONFIG['host'],
        port=FLASK_CONFIG['port'],
        debug=FLASK_CONFIG['debug']
    )
