-- ============================================================================
-- Seed Data: supabase/seed.sql
-- Description: Seed realistic categories, products, and historical sales
-- ============================================================================

-- 1. Seed Categories
INSERT INTO public.categories (id, name)
VALUES 
    ('c0000000-0000-0000-0000-000000000001', 'Poster'),
    ('c0000000-0000-0000-0000-000000000002', 'Keychain'),
    ('c0000000-0000-0000-0000-000000000003', 'Sticker'),
    ('c0000000-0000-0000-0000-000000000004', 'Accessory')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;

-- 2. Seed Products (12 items matching frontend & API mock datasets)
INSERT INTO public.products (id, name, sku, category_id, price, stock, units_sold, image_path, description, is_active)
VALUES
    (
        'a0000000-0000-0000-0000-000000000101',
        'Anime Poster Collection',
        'PST-ANM-001',
        'c0000000-0000-0000-0000-000000000001',
        250.00,
        45,
        126,
        'assets/images/placeholder-poster-main.svg',
        'Set of 6 high-definition aesthetic anime wall art posters with matte lamination.',
        TRUE
    ),
    (
        'a0000000-0000-0000-0000-000000000102',
        'Sunset Landscape Poster',
        'PST-SNT-002',
        'c0000000-0000-0000-0000-000000000001',
        250.00,
        18,
        42,
        'assets/images/placeholder-wave.svg',
        'Vibrant sunset landscape artwork printed on 300 GSM thick premium art paper.',
        TRUE
    ),
    (
        'a0000000-0000-0000-0000-000000000103',
        'Vintage Car Poster',
        'PST-VTC-003',
        'c0000000-0000-0000-0000-000000000001',
        220.00,
        5,
        89,
        'assets/images/placeholder-car.svg',
        'Classic vintage retro automobile illustration poster with distressed grunge border.',
        TRUE
    ),
    (
        'a0000000-0000-0000-0000-000000000104',
        'Minimal Wave Poster',
        'PST-MWV-004',
        'c0000000-0000-0000-0000-000000000001',
        200.00,
        8,
        64,
        'assets/images/placeholder-wave.svg',
        'Japanese inspired minimalist ocean wave decorative wall print.',
        TRUE
    ),
    (
        'a0000000-0000-0000-0000-000000000105',
        'Black Dragon Keychain',
        'KCH-BDG-001',
        'c0000000-0000-0000-0000-000000000002',
        150.00,
        3,
        95,
        'assets/images/placeholder-keychain.svg',
        'Solid zinc alloy black matte dragon charm keychain with reinforced ring.',
        TRUE
    ),
    (
        'a0000000-0000-0000-0000-000000000106',
        'Aesthetic Keychain',
        'KCH-AST-002',
        'c0000000-0000-0000-0000-000000000002',
        180.00,
        24,
        110,
        'assets/images/placeholder-keychain.svg',
        'Double-sided acrylic aesthetic pastel keychain for bags, keys, and backpacks.',
        TRUE
    ),
    (
        'a0000000-0000-0000-0000-000000000107',
        'Minimalist Keychain',
        'KCH-MNM-003',
        'c0000000-0000-0000-0000-000000000002',
        160.00,
        0,
        78,
        'assets/images/placeholder-keychain.svg',
        'Ultra-light aerospace titanium finish minimalist carabiner keychain.',
        TRUE
    ),
    (
        'a0000000-0000-0000-0000-000000000108',
        'Space Explorer Stickers',
        'STK-SPC-001',
        'c0000000-0000-0000-0000-000000000003',
        120.00,
        7,
        154,
        'assets/images/placeholder-space.svg',
        'Pack of 15 waterproof vinyl stickers featuring planets, astronauts, and rockets.',
        TRUE
    ),
    (
        'a0000000-0000-0000-0000-000000000109',
        'Cute Stickers Pack',
        'STK-CTE-002',
        'c0000000-0000-0000-0000-000000000003',
        120.00,
        32,
        180,
        'assets/images/placeholder-space.svg',
        '25 assorted cute kawaii animal die-cut stickers for laptops and phone cases.',
        TRUE
    ),
    (
        'a0000000-0000-0000-0000-000000000110',
        'BTS Photo Card Set',
        'ACC-BTS-001',
        'c0000000-0000-0000-0000-000000000004',
        200.00,
        15,
        98,
        'assets/images/placeholder-poster-main.svg',
        '55-piece glossy LOMO collectible photo cards set in a protective presentation box.',
        TRUE
    ),
    (
        'a0000000-0000-0000-0000-000000000111',
        'Retro Game Sticker Pack',
        'STK-RGM-003',
        'c0000000-0000-0000-0000-000000000003',
        140.00,
        0,
        67,
        'assets/images/placeholder-space.svg',
        '8-bit retro arcade gaming pixel vinyl decals with UV resistance.',
        TRUE
    ),
    (
        'a0000000-0000-0000-0000-000000000112',
        'Custom Name Keychain',
        'KCH-CST-004',
        'c0000000-0000-0000-0000-000000000002',
        220.00,
        12,
        53,
        'assets/images/placeholder-keychain.svg',
        'Personalized laser-engraved acrylic block keychain with metallic lobster clasp.',
        TRUE
    )
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    sku = EXCLUDED.sku,
    category_id = EXCLUDED.category_id,
    price = EXCLUDED.price,
    stock = EXCLUDED.stock,
    units_sold = EXCLUDED.units_sold,
    image_path = EXCLUDED.image_path,
    description = EXCLUDED.description,
    is_active = EXCLUDED.is_active;

-- 3. Seed Historical Sales (14 records matching ledger)
INSERT INTO public.sales (id, product_id, quantity, unit_price, total, sold_at)
VALUES
    (
        'b0000000-0000-0000-0000-000000001048',
        'a0000000-0000-0000-0000-000000000106',
        2,
        180.00,
        360.00,
        now() - INTERVAL '30 minutes'
    ),
    (
        'b0000000-0000-0000-0000-000000001047',
        'a0000000-0000-0000-0000-000000000102',
        1,
        250.00,
        250.00,
        now() - INTERVAL '90 minutes'
    ),
    (
        'b0000000-0000-0000-0000-000000001046',
        'a0000000-0000-0000-0000-000000000109',
        3,
        120.00,
        360.00,
        now() - INTERVAL '180 minutes'
    ),
    (
        'b0000000-0000-0000-0000-000000001045',
        'a0000000-0000-0000-0000-000000000110',
        1,
        200.00,
        200.00,
        now() - INTERVAL '240 minutes'
    ),
    (
        'b0000000-0000-0000-0000-000000001044',
        'a0000000-0000-0000-0000-000000000101',
        2,
        250.00,
        500.00,
        now() - INTERVAL '360 minutes'
    ),
    (
        'b0000000-0000-0000-0000-000000001043',
        'a0000000-0000-0000-0000-000000000107',
        2,
        160.00,
        320.00,
        now() - INTERVAL '1 day 1 hour'
    ),
    (
        'b0000000-0000-0000-0000-000000001042',
        'a0000000-0000-0000-0000-000000000108',
        4,
        120.00,
        480.00,
        now() - INTERVAL '1 day 3 hours'
    ),
    (
        'b0000000-0000-0000-0000-000000001041',
        'a0000000-0000-0000-0000-000000000103',
        1,
        220.00,
        220.00,
        now() - INTERVAL '1 day 6 hours'
    ),
    (
        'b0000000-0000-0000-0000-000000001040',
        'a0000000-0000-0000-0000-000000000101',
        3,
        250.00,
        750.00,
        now() - INTERVAL '3 days 2 hours'
    ),
    (
        'b0000000-0000-0000-0000-000000001039',
        'a0000000-0000-0000-0000-000000000112',
        2,
        220.00,
        440.00,
        now() - INTERVAL '4 days 4 hours'
    ),
    (
        'b0000000-0000-0000-0000-000000001038',
        'a0000000-0000-0000-0000-000000000104',
        2,
        200.00,
        400.00,
        now() - INTERVAL '5 days 6 hours'
    ),
    (
        'b0000000-0000-0000-0000-000000001037',
        'a0000000-0000-0000-0000-000000000111',
        5,
        140.00,
        700.00,
        now() - INTERVAL '12 days 2 hours'
    ),
    (
        'b0000000-0000-0000-0000-000000001036',
        'a0000000-0000-0000-0000-000000000105',
        2,
        150.00,
        300.00,
        now() - INTERVAL '18 days 5 hours'
    ),
    (
        'b0000000-0000-0000-0000-000000001035',
        'a0000000-0000-0000-0000-000000000102',
        2,
        250.00,
        500.00,
        now() - INTERVAL '24 days 8 hours'
    )
ON CONFLICT (id) DO UPDATE SET
    product_id = EXCLUDED.product_id,
    quantity = EXCLUDED.quantity,
    unit_price = EXCLUDED.unit_price,
    total = EXCLUDED.total,
    sold_at = EXCLUDED.sold_at;
