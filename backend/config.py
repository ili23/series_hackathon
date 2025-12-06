"""
Configuration settings for the Series iMessage Service Backend
"""
import os


# Kafka Configuration
KAFKA_CONFIG = {
    'bootstrap_servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'pkc-619z3.us-east1.gcp.confluent.cloud:9092'),
    'topic_name': os.getenv('KAFKA_TOPIC', 'team.team.f6e0a95387f7417b90fe88a08a39caec'),
    'consumer_group': os.getenv('KAFKA_CONSUMER_GROUP', 'team-cg-f6e0a95387f7417b90fe88a08a39caec'),
    'api_key': os.getenv('KAFKA_API_KEY', 'b9f131d7-0172-4749-afdd-f01e753b664f'),
    'api_secret': os.getenv('KAFKA_API_SECRET', 'cfltTIivf3OHq6tr9fpASLxV4pp7vzPfvnz3cwT8+NAoOAJUCZwRuxuk1sSZTK+w'),
    'sasl_username': os.getenv('KAFKA_SASL_USERNAME', 'QRHNR6BCKVHD4M3U'),
    'security_protocol': 'SASL_SSL',
    'sasl_mechanism': 'PLAIN',
}

# Flask Configuration
FLASK_CONFIG = {
    'host': '0.0.0.0',
    'port': int(os.getenv('PORT', 5000)),
    'debug': os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
}

# Series API Configuration
SERIES_API_CONFIG = {
    'base_url': os.getenv('SERIES_API_BASE_URL', 'https://api.series.im'),  # Update if different
    'api_key': KAFKA_CONFIG['api_key'],  # Same API key
    'sender_number': os.getenv('SENDER_NUMBER', '+16463230991'),
}

