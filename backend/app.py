"""
Series iMessage Service Backend
A Flask backend that consumes Kafka events from the Series iMessage Service
"""
import sys
import os
import logging
from flask import Flask

# Add project root to path to allow absolute imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.config import FLASK_CONFIG
from backend.kafka_client import initialize_kafka_consumer, close_kafka_consumer
from backend.services import process_kafka_event
from backend.routes import register_routes
from backend.db import init_db, close_db_session

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

# Initialize database
init_db()

# Register routes
register_routes(app)

# Initialize Kafka consumer on app startup
initialize_kafka_consumer(process_kafka_event)

# Cleanup on shutdown
@app.teardown_appcontext
def teardown(exception):
    """Close Kafka consumer and database session on app shutdown"""
    close_kafka_consumer()
    close_db_session()


if __name__ == '__main__':
    # Run Flask app
    app.run(
        host=FLASK_CONFIG['host'],
        port=FLASK_CONFIG['port'],
        debug=FLASK_CONFIG['debug']
    )
