"""
Flask routes for the Series iMessage Service Backend
"""
import logging
from flask import jsonify, request
from backend.kafka_client import get_kafka_consumer, is_kafka_consumer_ready

logger = logging.getLogger(__name__)


def register_routes(app):
    """Register all routes with the Flask app"""
    
    @app.route('/')
    def health_check():
        """Health check endpoint"""
        consumer = get_kafka_consumer()
        consumer_ready = is_kafka_consumer_ready()
        
        return jsonify({
            'status': 'healthy',
            'service': 'Series iMessage Backend',
            'kafka_consumer': {
                'exists': consumer is not None,
                'ready': consumer_ready,
                'assigned_partitions': len(consumer.assignment()) if consumer else 0
            }
        })
    
    @app.route('/api/events', methods=['GET'])
    def get_recent_events():
        """Get recent events (placeholder - implement your own storage)"""
        return jsonify({
            'message': 'Event storage not implemented yet',
            'hint': 'Store events in a database or cache as they arrive'
        })
    
    @app.route('/api/send-message', methods=['POST'])
    def send_message():
        """Send a message via Kafka (if needed)"""
        # Note: This is a placeholder. Actual message sending should use the Series API
        # This endpoint is just for demonstration
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        logger.info(f"Received send message request: {data}")
        
        # TODO: Use Series API to send messages instead of Kafka
        # POST /api/chats with Authorization: Bearer <API_KEY>
        
        return jsonify({
            'message': 'Message send endpoint - use Series API directly',
            'received_data': data
        })

