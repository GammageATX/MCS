-- Connect to micro_cold_spray database
\c micro_cold_spray;

-- Insert test spray events
INSERT INTO spray_events (
    spray_index,
    sequence_id,
    material_type,
    pattern_name,
    operator,
    start_time,
    end_time,
    powder_size,
    powder_lot,
    manufacturer,
    nozzle_type,
    chamber_pressure_start,
    chamber_pressure_end,
    nozzle_pressure_start,
    nozzle_pressure_end,
    main_flow,
    feeder_flow,
    feeder_frequency,
    pattern_type,
    completed
) VALUES 
-- Successful spray event
(1, 'test-sequence-001', 
 'copper', 'linear-pattern-1', 'test-operator',
 NOW() - interval '1 hour',
 NOW() - interval '45 minutes',
 '45-90um', 'LOT123456',
 'Praxair', 'MOC-Type-A',
 2.5, 2.4, 3.0, 2.9,
 50.0, 10.0, 60.0,
 'linear', true),

-- Failed spray event
(2, 'test-sequence-001',
 'copper', 'linear-pattern-2', 'test-operator',
 NOW() - interval '30 minutes',
 NOW() - interval '25 minutes',
 '45-90um', 'LOT123456',
 'Praxair', 'MOC-Type-A',
 2.5, 0.0, 3.0, 0.0,
 50.0, 10.0, 60.0,
 'linear', false),

-- In-progress spray event
(1, 'test-sequence-002',
 'titanium', 'zigzag-pattern-1', 'test-operator',
 NOW() - interval '5 minutes',
 NULL,
 '45-90um', 'LOT789012',
 'Oerlikon', 'MOC-Type-B',
 2.8, NULL, 3.2, NULL,
 55.0, 12.0, 65.0,
 'zigzag', false);

-- Add error message to failed event
UPDATE spray_events 
SET error = 'Chamber pressure dropped below minimum threshold'
WHERE sequence_id = 'test-sequence-001' 
AND spray_index = 2; 