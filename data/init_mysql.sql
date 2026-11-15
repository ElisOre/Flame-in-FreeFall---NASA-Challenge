CREATE DATABASE IF NOT EXISTS Flame_in_FreeFall_NASA_Challenge;
USE nasa_psi_db;

CREATE TABLE IF NOT EXISTS investigations (
    psi_id VARCHAR(15) PRIMARY KEY,
    acronym VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    doi VARCHAR(100),
    project_type VARCHAR(50),
    flight_platform VARCHAR(100),
    fuel_phase VARCHAR(30),
    hardware_rack VARCHAR(100),
    hardware_apparatus VARCHAR(100),
    safety_pillar VARCHAR(50),
    simulates_partial_gravity TINYINT(1) DEFAULT 0,
    max_o2_tested_pct DECIMAL(5,2)
);

CREATE TABLE IF NOT EXISTS experimental_tests (
    test_uid INT AUTO_INCREMENT PRIMARY KEY,
    psi_id VARCHAR(15),
    sample_or_test_id VARCHAR(100),
    fuel_material VARCHAR(100),
    sample_geometry VARCHAR(100),
    gravity_level VARCHAR(20),
    ambient_pressure_psi DECIMAL(6,2),
    o2_percentage DECIMAL(5,2),
    diluent_or_suppressant VARCHAR(50),
    airflow_velocity_cm_s DECIMAL(6,2),
    burning_or_spread_rate DECIMAL(8,4),
    test_outcome VARCHAR(100),
    FOREIGN KEY (psi_id) REFERENCES investigations(psi_id)
);

INSERT IGNORE INTO investigations VALUES
('PSI-60', 'SPICE Re-Analysis', 'Computational and Experimental Analysis of SPICE Data Sets', '10.60555/mzjm-yv57', 'Ground Investigation', 'Ground', 'Gaseous', 'MSG', 'SPICE Flow Duct', 'Predictive Modeling', 0, 21.00),
('PSI-69', 'FLEX', 'Flame Extinguishment Experiment', '10.60555/mbq8-0451', 'Microgravity Investigation', 'ISS', 'Liquid', 'CIR', 'MDCA', 'Suppression', 0, 30.00),
('PSI-25', 'BASS-II', 'Burning and Suppression of Solids - II', '10.60555/4qc4-de67', 'Microgravity Investigation', 'ISS', 'Solid', 'MSG', 'SPICE Flow Duct', 'Prevention', 0, 21.00),
('PSI-159', 'ACME CFI-G', 'Cool Flames Investigation with Gases', '10.60555/cyt1-kh64', 'Microgravity Investigation', 'ISS', 'Gaseous', 'CIR', 'ACME Burner', 'Prevention', 0, 85.00),
('PSI-EFIELD', 'ACME E-FIELD', 'Electric-Field Effects on Laminar Diffusion Flames', 'N/A', 'Microgravity Investigation', 'ISS', 'Gaseous', 'CIR', 'ACME High-Voltage Mesh', 'Predictive Modeling', 1, 21.00);

INSERT INTO experimental_tests (psi_id, sample_or_test_id, fuel_material, sample_geometry, gravity_level, ambient_pressure_psi, o2_percentage, diluent_or_suppressant, airflow_velocity_cm_s, burning_or_spread_rate, test_outcome) VALUES
('PSI-69', '20CAL08', 'Methanol', 'Droplet 1.69mm', '0g', 14.65, 21.00, 'N2', 0.0, 0.5200, 'Disruption'),
('PSI-69', '20CAL10', 'Methanol', 'Droplet 1.86mm', '0g', 14.73, 21.00, 'N2', 0.0, 0.6000, 'Extinction'),
('PSI-69', '30CAL02', 'Methanol', 'Droplet 2.06mm', '0g', 14.70, 21.00, 'CO2', 0.0, 0.6000, 'Extinction'),
('PSI-25', 'BASS2-PMMA-01', 'Acrylic PMMA', 'Rod', '0g', 14.70, 21.00, 'N2', 15.0, 1.2500, 'Steady Burn'),
('PSI-159', 'CFIG-HI-O2', 'Propane', 'Spherical Burner', '0g', 10.20, 85.00, 'N2', 5.0, 2.4000, 'Cool Flame Transition');