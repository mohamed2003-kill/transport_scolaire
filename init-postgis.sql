-- Initialize PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create tables for location service if they don't exist
CREATE TABLE IF NOT EXISTS locations (
    id SERIAL PRIMARY KEY,
    entity_id VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50) NOT NULL, -- 'student' or 'bus'
    coordinates GEOMETRY(POINT, 4326) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on entity_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_locations_entity_id ON locations(entity_id);

-- Create index on coordinates for geospatial queries
CREATE INDEX IF NOT EXISTS idx_locations_coordinates ON locations USING GIST(coordinates);

-- Create table for notification history
CREATE TABLE IF NOT EXISTS notification_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(50) NOT NULL, -- 'sent', 'failed', 'pending'
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on user_id for faster notification history queries
CREATE INDEX IF NOT EXISTS idx_notification_history_user_id ON notification_history(user_id);