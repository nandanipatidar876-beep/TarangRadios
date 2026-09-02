-- =============================================================================
-- Migration 003: Seed Default Data
-- Description: Seeds the default super admin and the 7 required brands.
-- =============================================================================

-- Seed the 7 Core Brands in "The Brands We Deal With"
INSERT INTO brands (id, name, display_order, is_enabled, created_at, updated_at)
VALUES 
    ('brand_gillard', 'Gillard', 0, 1, '2026-08-01T00:00:00', '2026-08-01T00:00:00'),
    ('brand_alcop', 'Alcop', 1, 1, '2026-08-01T00:00:00', '2026-08-01T00:00:00'),
    ('brand_dvm', 'DVM', 2, 1, '2026-08-01T00:00:00', '2026-08-01T00:00:00'),
    ('brand_hoki', 'Hoki', 3, 1, '2026-08-01T00:00:00', '2026-08-01T00:00:00'),
    ('brand_noel', 'Noel', 4, 1, '2026-08-01T00:00:00', '2026-08-01T00:00:00'),
    ('brand_kushiro', 'Kushiro', 5, 1, '2026-08-01T00:00:00', '2026-08-01T00:00:00'),
    ('brand_ingco', 'INGCO', 6, 1, '2026-08-01T00:00:00', '2026-08-01T00:00:00')
ON CONFLICT DO NOTHING;
