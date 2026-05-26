-- CLICK IX ENTERPRISE REPORT ENGINE
-- Database Schema Initialization
-- Engine: InnoDB | Charset: utf8mb4

CREATE DATABASE IF NOT EXISTS cix_engine CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE cix_engine;

SET FOREIGN_KEY_CHECKS = 0;

-- -----------------------------------------------------------------------------
-- CORE IDENTITY & ACCESS MANAGEMENT
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS user_roles, roles, users;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    initials VARCHAR(10) NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL -- 'admin', 'sales', 'ops', 'finance', 'director'
) ENGINE=InnoDB;

CREATE TABLE user_roles (
    user_id INT,
    role_id INT,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- CRM & LOCATIONS (OUTLETS)
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS outlets, customers, regions;

CREATE TABLE regions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
) ENGINE=InnoDB;

CREATE TABLE customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL, -- e.g., 'MAX'
    name VARCHAR(255) NOT NULL,
    billing_address TEXT,
    shipping_address TEXT,
    license_number VARCHAR(100) NULL,
    license_expiry DATE NULL
) ENGINE=InnoDB;

CREATE TABLE outlets (
    maxis_centre_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    region_id INT NOT NULL,
    maxis_centre_name VARCHAR(255) NOT NULL,
    type ENUM('MC+', 'MC', 'MEP', 'MEP Lite', 'Kiosk', 'Flagship') NOT NULL,
    state ENUM('Johor', 'Kedah', 'Kelantan', 'Melaka', 'Negeri Sembilan', 'Pahang', 'Penang', 'Perak', 'Perlis', 'Sabah', 'Sarawak', 'Selangor', 'Terengganu', 'Kuala Lumpur', 'Labuan', 'Putrajaya') NOT NULL,
    locality VARCHAR(255),
    address TEXT NOT NULL,
    store_pic VARCHAR(255),
    contact_no VARCHAR(50),
    project_ref VARCHAR(50) NOT NULL, -- Format: [SalesInitials][YY]-[ClientCode][NNN]
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE RESTRICT,
    FOREIGN KEY (region_id) REFERENCES regions(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- GLOBAL SEQUENCING & CATALOG
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS catalog_items, number_counters;

CREATE TABLE number_counters (
    scope VARCHAR(32) PRIMARY KEY, -- 'QT', 'DO', 'SR', 'SO', 'GRN', 'PO'
    next_seq BIGINT NOT NULL,
    year SMALLINT NULL,
    month TINYINT NULL
) ENGINE=InnoDB;

CREATE TABLE catalog_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_code VARCHAR(50) UNIQUE NOT NULL, -- MHD-085 (Hardware), MSV-020 (Service), BULK-CABLE (Bulk)
    type ENUM('hardware', 'service', 'bulk') NOT NULL,
    description TEXT NOT NULL,
    default_uom VARCHAR(20) DEFAULT 'UNIT',
    default_unit_price DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    default_tax_code VARCHAR(10) DEFAULT 'S',
    active BOOLEAN DEFAULT TRUE
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- INVENTORY & ASSET LEDGERS
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS inventory_adjustments, inventory_stock, display_licenses, asset_tv_specs, asset_pc_specs, asset_skus;

-- The Stock Book (Bulk Items: Cables, Brackets, Screws)
CREATE TABLE inventory_stock (
    item_code VARCHAR(50) PRIMARY KEY,
    last_updated DATE NOT NULL,
    in_qty INT DEFAULT 0,
    out_qty INT DEFAULT 0,
    qty INT DEFAULT 0,
    cost DECIMAL(12,2) DEFAULT 0.00,
    total_cost DECIMAL(12,2) DEFAULT 0.00,
    FOREIGN KEY (item_code) REFERENCES catalog_items(item_code) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE inventory_adjustments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_code VARCHAR(50) NOT NULL,
    adjust_qty INT NOT NULL,
    reason TEXT NOT NULL,
    audit_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_code) REFERENCES inventory_stock(item_code) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Serialized Hardware Base Ledger (PCs, TVs, MP, SSD)
CREATE TABLE asset_skus (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sku VARCHAR(50) UNIQUE NOT NULL, -- MP-2605-0001
    item_code VARCHAR(50) NOT NULL,
    type ENUM('MP','TV','RM','SSD') NOT NULL,
    state ENUM('unassign','assigned','deployed','to be disposed','returned_supplier','disposed') NOT NULL DEFAULT 'unassign',
    is_faulty BOOLEAN DEFAULT FALSE,
    maxis_centre_id INT NULL,
    installed_at DATETIME NULL,
    FOREIGN KEY (item_code) REFERENCES catalog_items(item_code) ON DELETE RESTRICT,
    FOREIGN KEY (maxis_centre_id) REFERENCES outlets(maxis_centre_id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE asset_pc_specs (
    sku_id INT PRIMARY KEY,
    processor VARCHAR(255),
    ram ENUM('4GB', '8GB', '16GB', '32GB', '128GB', '256GB'),
    ram_ddr ENUM('DDR3', 'DDR4', 'DDR5', 'DDR6', 'DDR7'),
    storage ENUM('4GB', '8GB', '16GB', '32GB', '128GB', '256GB', '512GB', '1TB', '2TB+'),
    internet ENUM('LAN', 'Wi-Fi', 'Wifi Dongle', '4G SIM'),
    anydesk_id VARCHAR(50),
    anydesk_password VARCHAR(100),
    teamviewer_id VARCHAR(50),
    cix_pic VARCHAR(255),
    FOREIGN KEY (sku_id) REFERENCES asset_skus(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE asset_tv_specs (
    sku_id INT PRIMARY KEY,
    brand VARCHAR(255),
    size ENUM('14','32','39','40','42','45','50','55','60','65','70','75','88','98','50*4','50*9','98*2','98*4'),
    resolution VARCHAR(100),
    connection_port ENUM('HDMI', 'VGA-HDMI', 'DP-HDMI', 'Built-In', 'HDMI-LAN', 'DP-HDMI-VGA'),
    panel_hours INT DEFAULT 0,
    FOREIGN KEY (sku_id) REFERENCES asset_skus(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE display_licenses (
    display_id INT AUTO_INCREMENT PRIMARY KEY,
    sku_id INT NOT NULL,
    cs_license VARCHAR(255),
    current_label VARCHAR(255),
    screen_location VARCHAR(255),
    display_language ENUM('EN', 'BM', 'EN/BM'),
    installation_status ENUM('Installed', 'Not Installed - No Player', 'tbc'),
    FOREIGN KEY (sku_id) REFERENCES asset_skus(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- COMMERCIAL & OPERATIONAL WORKFLOWS
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS sr_photos, sr_hardware, service_reports, do_assigned_skus, do_items, delivery_orders, sales_orders, quotation_items, quotations, procurement_document_references;

CREATE TABLE procurement_document_references (
    doc_ref_id INT AUTO_INCREMENT PRIMARY KEY,
    project_ref VARCHAR(50) NOT NULL,
    quotation_no VARCHAR(50) NOT NULL,
    remedy_id VARCHAR(50) NULL,
    sales_order VARCHAR(50) NULL,
    delivery_order VARCHAR(50) NULL,
    sales_invoice VARCHAR(50) NULL,      -- AutoCount Final Sales Billing Code
    supplier_invoice VARCHAR(50) NULL,   -- AutoCount Supplier Billing Code
    service_report VARCHAR(50) NULL,
    goods_received_note VARCHAR(50) NULL,
    supplier_po VARCHAR(50) NULL,
    goods_return VARCHAR(50) NULL,
    ticket_cs VARCHAR(50) NULL
) ENGINE=InnoDB;

CREATE TABLE quotations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    quotation_no VARCHAR(50) UNIQUE NOT NULL,
    remedy_id VARCHAR(50) NULL,
    customer_id INT NOT NULL,
    job_type ENUM('Diagnostics', 'Replacement', 'Installation', 'Removal') NOT NULL,
    project_ref VARCHAR(50) NOT NULL,
    salesperson VARCHAR(100) NOT NULL,
    wo_number VARCHAR(50),
    remedy_number VARCHAR(50),
    dealer_code VARCHAR(50),
    subtotal DECIMAL(12,2) NOT NULL,
    tax_base DECIMAL(12,2) NOT NULL,
    tax_amount DECIMAL(12,2) NOT NULL,
    total DECIMAL(12,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'MYR',
    status ENUM('draft', 'sent', 'accepted', 'rejected') DEFAULT 'draft',
    validity_days INT DEFAULT 14,
    payment_term_days INT DEFAULT 90,
    accepted_signature_upload_id INT NULL,
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accepted_at DATETIME NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE quotation_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    quotation_id INT NOT NULL,
    line_no INT NOT NULL,
    item_code VARCHAR(50) NOT NULL,
    description TEXT,
    uom VARCHAR(20),
    qty DECIMAL(12,3) NOT NULL,
    unit_price DECIMAL(12,2) NOT NULL,
    tax_code VARCHAR(10),
    line_total DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (quotation_id) REFERENCES quotations(id) ON DELETE CASCADE,
    FOREIGN KEY (item_code) REFERENCES catalog_items(item_code) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE sales_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    so_no VARCHAR(50) UNIQUE NOT NULL,
    quotation_id INT NOT NULL,
    FOREIGN KEY (quotation_id) REFERENCES quotations(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE delivery_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    do_no VARCHAR(50) UNIQUE NOT NULL,
    so_id INT NULL,
    customer_id INT NOT NULL,
    maxis_centre_id INT NOT NULL,
    salesperson VARCHAR(100) NOT NULL,
    bill_to TEXT NOT NULL,
    ship_to TEXT NOT NULL,
    affected_screen VARCHAR(255),
    status ENUM('draft', 'assigned', 'in_transit', 'delivered', 'split') DEFAULT 'draft',
    parent_do_id INT NULL,
    signed_by VARCHAR(255) NULL,
    signature_upload_id INT NULL,
    signed_at DATETIME NULL,
    FOREIGN KEY (so_id) REFERENCES sales_orders(id) ON DELETE SET NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE RESTRICT,
    FOREIGN KEY (maxis_centre_id) REFERENCES outlets(maxis_centre_id) ON DELETE RESTRICT,
    FOREIGN KEY (parent_do_id) REFERENCES delivery_orders(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE do_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    do_id INT NOT NULL,
    line_no INT NOT NULL,
    item_code VARCHAR(50) NOT NULL,
    description TEXT,
    uom VARCHAR(20),
    qty DECIMAL(12,3) NOT NULL,
    fulfilled BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (do_id) REFERENCES delivery_orders(id) ON DELETE CASCADE,
    FOREIGN KEY (item_code) REFERENCES catalog_items(item_code) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE do_assigned_skus (
    do_id INT NOT NULL,
    sku_id INT NOT NULL,
    PRIMARY KEY (do_id, sku_id),
    FOREIGN KEY (do_id) REFERENCES delivery_orders(id) ON DELETE CASCADE,
    FOREIGN KEY (sku_id) REFERENCES asset_skus(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE service_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sr_no VARCHAR(50) UNIQUE NOT NULL,
    do_id INT NOT NULL,
    wo_number VARCHAR(50),
    remedy_number VARCHAR(50),
    client_company VARCHAR(255) NOT NULL,
    client_addr_json JSON NOT NULL,
    store_type VARCHAR(50),
    store_name VARCHAR(255),
    pic_name VARCHAR(255),
    pic_tel VARCHAR(50),
    diagnostic TEXT,
    action_taken TEXT,
    before_photos_json JSON NOT NULL,
    after_photos_json JSON NOT NULL,
    ack_signed_by VARCHAR(255) NOT NULL,
    ack_signature_upload_id INT NOT NULL,
    ack_signed_at DATETIME NOT NULL,
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (do_id) REFERENCES delivery_orders(id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE sr_hardware (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sr_id INT NOT NULL,
    direction ENUM('removed', 'installed') NOT NULL,
    sku_id INT NOT NULL,
    item_code VARCHAR(50) NOT NULL,
    reason TEXT,
    is_faulty BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (sr_id) REFERENCES service_reports(id) ON DELETE CASCADE,
    FOREIGN KEY (sku_id) REFERENCES asset_skus(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- SYSTEM ARCHITECTURE & FILE MANAGEMENT
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS audit_log, uploads;

CREATE TABLE uploads (
    id INT AUTO_INCREMENT PRIMARY KEY,
    path VARCHAR(500) NOT NULL,
    mime VARCHAR(100) NOT NULL,
    size BIGINT NOT NULL,
    sha256 VARCHAR(64) NOT NULL,
    uploaded_by INT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    entity VARCHAR(50) NOT NULL,
    entity_id INT NOT NULL,
    action VARCHAR(50) NOT NULL,
    actor_id INT NULL,
    before_json JSON,
    after_json JSON,
    at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (actor_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

SET FOREIGN_KEY_CHECKS = 1;