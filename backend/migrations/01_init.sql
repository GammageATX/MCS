-- Initialize micro_cold_spray database
CREATE DATABASE IF NOT EXISTS micro_cold_spray;

\c micro_cold_spray;

-- Create spray_events table if it doesn't exist
CREATE TABLE IF NOT EXISTS spray_events (
    id SERIAL PRIMARY KEY,
    spray_index INTEGER NOT NULL,
    sequence_id TEXT NOT NULL CHECK (sequence_id ~ '^[a-zA-Z0-9_-]+$'),
    material_type TEXT NOT NULL,
    pattern_name TEXT NOT NULL,
    operator TEXT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    powder_size TEXT NOT NULL,
    powder_lot TEXT NOT NULL,
    manufacturer TEXT NOT NULL,
    nozzle_type TEXT NOT NULL,
    chamber_pressure_start FLOAT NOT NULL CHECK (chamber_pressure_start >= 0),
    chamber_pressure_end FLOAT NOT NULL CHECK (chamber_pressure_end >= 0),
    nozzle_pressure_start FLOAT NOT NULL CHECK (nozzle_pressure_start >= 0),
    nozzle_pressure_end FLOAT NOT NULL CHECK (nozzle_pressure_end >= 0),
    main_flow FLOAT NOT NULL CHECK (main_flow >= 0),
    feeder_flow FLOAT NOT NULL CHECK (feeder_flow >= 0),
    feeder_frequency FLOAT NOT NULL CHECK (feeder_frequency >= 0),
    pattern_type TEXT NOT NULL,
    completed BOOLEAN NOT NULL,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_spray_events_sequence_id ON spray_events(sequence_id);
CREATE INDEX IF NOT EXISTS idx_spray_events_start_time ON spray_events(start_time);
CREATE INDEX IF NOT EXISTS idx_spray_events_pattern_name ON spray_events(pattern_name);

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE micro_cold_spray TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO postgres; 