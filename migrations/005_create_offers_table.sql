-- =============================================================================
-- Migration 005: Create Offers & Promotions Table
-- Description: Stores dynamic promotional offers, discount schemes, and badges.
-- Compatible with PostgreSQL & SQLite.
-- =============================================================================

CREATE TABLE IF NOT EXISTS offers (
    id VARCHAR(255) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    subtitle VARCHAR(255),
    badge_text VARCHAR(100),
    discount_text VARCHAR(100),
    description TEXT,
    coupon_code VARCHAR(100),
    cta_text VARCHAR(100) DEFAULT 'Explore Deals',
    cta_link VARCHAR(255) DEFAULT '#categorySection',
    bg_gradient VARCHAR(100) DEFAULT 'orange',
    banner_image TEXT,
    is_active INTEGER DEFAULT 1,
    display_order INTEGER DEFAULT 0,
    created_at VARCHAR(64),
    updated_at VARCHAR(64)
);

-- Seed initial professional offers for Tarang Radios
INSERT INTO offers (
    id, title, subtitle, badge_text, discount_text, description,
    coupon_code, cta_text, cta_link, bg_gradient, is_active, display_order, created_at, updated_at
) VALUES 
(
    'offer-b2b-bulk-deal',
    'Mega B2B Wholesale Deal',
    'Capacitors, Relays, ICs & Connectors',
    '🔥 SPECIAL SCHEME',
    'UP TO 25% OFF',
    'Special tiered trade discounts for electronics repair centers, dealers & industrial bulk buyers across Central India.',
    'BULK25',
    'View Wholesale Catalog',
    '#categorySection',
    'orange',
    1,
    1,
    '2026-09-06T00:00:00',
    '2026-09-06T00:00:00'
),
(
    'offer-soldering-combo',
    'Soldering & Workstation Kits',
    'Precision Soldering Irons, Elements & Accessories',
    '⚡ FLASH PROMO',
    'EXTRA 15% OFF',
    'Premium genuine soldering stations, heat-resistant bits, flux and stands at exclusive promotional prices.',
    'SOLDER15',
    'Explore Soldering Solutions',
    '#categorySection',
    'gold',
    1,
    2,
    '2026-09-06T00:00:00',
    '2026-09-06T00:00:00'
),
(
    'offer-dj-audio-spares',
    'DJ & Professional Audio Spares',
    'High-Grade Neutrik-Style Connectors & Cables',
    '💎 DEAL OF THE MONTH',
    'FLAT ₹300 OFF',
    'Stock up on heavy-duty XLR, Speakon, 6.35mm jacks and pro audio replacement spare parts with verified quality.',
    'AUDIOPRO',
    'Contact For DJ Spares',
    '#contactSection',
    'emerald',
    1,
    3,
    '2026-09-06T00:00:00',
    '2026-09-06T00:00:00'
)
ON CONFLICT DO NOTHING;

