CREATE TABLE IF NOT EXISTS metro_routes (
    route_id TEXT PRIMARY KEY,
    route_short_name TEXT NOT NULL, -- "A", "B", "C"...
    route_long_name TEXT,
    route_color TEXT, -- "199FDA"
    route_text_color TEXT
);

CREATE TABLE IF NOT EXISTS metro_calendar (
    service_id  TEXT PRIMARY KEY,
    monday BOOLEAN NOT NULL,
    tuesday BOOLEAN NOT NULL,
    wednesday BOOLEAN NOT NULL,
    thursday BOOLEAN NOT NULL,
    friday BOOLEAN NOT NULL,
    saturday BOOLEAN NOT NULL,
    sunday BOOLEAN NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS metro_calendar_dates (
    service_id TEXT NOT NULL REFERENCES metro_calendar(service_id),
    date DATE NOT NULL,
    exception_type SMALLINT NOT NULL, -- 1=adicionado, 2=removido
    PRIMARY KEY (service_id, date)
);

CREATE TABLE IF NOT EXISTS metro_stops (
    stop_id TEXT PRIMARY KEY,
    stop_code TEXT,
    stop_name TEXT NOT NULL,
    stop_lat DOUBLE PRECISION NOT NULL,
    stop_lon DOUBLE PRECISION NOT NULL,
    zone_id TEXT -- "PRT1", para tarifas
);

CREATE TABLE IF NOT EXISTS metro_shapes (
    shape_id TEXT NOT NULL,
    shape_pt_lat DOUBLE PRECISION NOT NULL,
    shape_pt_lon DOUBLE PRECISION NOT NULL,
    shape_pt_sequence INTEGER NOT NULL,
    PRIMARY KEY (shape_id, shape_pt_sequence)
);

CREATE TABLE IF NOT EXISTS metro_trips (
    trip_id TEXT PRIMARY KEY,
    route_id TEXT NOT NULL REFERENCES metro_routes(route_id),
    service_id TEXT NOT NULL REFERENCES metro_calendar(service_id),
    trip_headsign TEXT, -- "Póvoa de Varzim"
    direction_id SMALLINT, -- 0=ida, 1=volta
    shape_id TEXT,
    wheelchair_accessible SMALLINT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS metro_stop_times (
    trip_id TEXT NOT NULL REFERENCES metro_trips(trip_id),
    stop_id TEXT NOT NULL REFERENCES metro_stops(stop_id),
    arrival_time TEXT NOT NULL, -- "25:01:00" é possível TEXT é melhor
    departure_time TEXT NOT NULL,
    stop_sequence INTEGER NOT NULL,
    stop_headsign TEXT,
    PRIMARY KEY (trip_id, stop_sequence)
);

CREATE TABLE IF NOT EXISTS metro_fare_attributes (
    fare_id TEXT PRIMARY KEY,
    price NUMERIC(6,2) NOT NULL,
    currency_type TEXT NOT NULL DEFAULT 'EUR',
    payment_method SMALLINT,
    transfers SMALLINT
);

CREATE TABLE IF NOT EXISTS metro_fare_rules (
    fare_id TEXT NOT NULL REFERENCES metro_fare_attributes(fare_id),
    origin_id TEXT, -- zone_id
    destination_id TEXT,
    PRIMARY KEY (fare_id, origin_id, destination_id)
);

CREATE TABLE IF NOT EXISTS metro_transfers (
    from_stop_id TEXT NOT NULL REFERENCES metro_stops(stop_id),
    to_stop_id TEXT NOT NULL REFERENCES metro_stops(stop_id),
    transfer_type SMALLINT NOT NULL,
    PRIMARY KEY (from_stop_id, to_stop_id)
);

-- indices para queries de horários
CREATE INDEX IF NOT EXISTS idx_metro_stop_times_stop ON metro_stop_times(stop_id);
CREATE INDEX IF NOT EXISTS idx_metro_stop_times_trip ON metro_stop_times(trip_id);
CREATE INDEX IF NOT EXISTS idx_metro_trips_route ON metro_trips(route_id);
CREATE INDEX IF NOT EXISTS idx_metro_trips_service ON metro_trips(service_id);