-- ERP NovaMarket (PostgreSQL). Sistema legado: algumas convenções são inconsistentes.
-- Aplicado de forma idempotente por `novamarket data load-erp`.

CREATE SCHEMA IF NOT EXISTS erp;
CREATE SCHEMA IF NOT EXISTS inventory;

CREATE TABLE IF NOT EXISTS erp.suppliers (
    supplier_id    integer PRIMARY KEY,
    supplier_name  text NOT NULL,
    tax_id         text,
    country        char(2) NOT NULL,
    active         boolean NOT NULL DEFAULT true,
    created_at     timestamp NOT NULL
);

CREATE TABLE IF NOT EXISTS erp.stores (
    store_id    integer PRIMARY KEY,
    store_code  text NOT NULL UNIQUE,
    store_name  text NOT NULL,
    store_type  text NOT NULL CHECK (store_type IN ('STORE', 'DC', 'VIRTUAL')),
    country     char(2) NOT NULL,
    city        text,
    opened_at   date,
    active      boolean NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS erp.products (
    product_id    integer PRIMARY KEY,
    sku           text NOT NULL UNIQUE,
    product_name  text NOT NULL,
    category      text,
    subcategory   text,
    brand         text,
    supplier_id   integer REFERENCES erp.suppliers (supplier_id),
    cost_price    numeric(12, 2) NOT NULL CHECK (cost_price >= 0),
    list_price    numeric(12, 2) NOT NULL CHECK (list_price >= 0),
    status        text NOT NULL,
    dt_cadastro   date
);

CREATE TABLE IF NOT EXISTS inventory.stock (
    store_id           integer NOT NULL REFERENCES erp.stores (store_id),
    product_id         integer NOT NULL REFERENCES erp.products (product_id),
    quantity_on_hand   integer NOT NULL,
    quantity_reserved  integer NOT NULL DEFAULT 0,
    updated_at         timestamp,
    PRIMARY KEY (store_id, product_id)
);

CREATE INDEX IF NOT EXISTS ix_products_supplier ON erp.products (supplier_id);
CREATE INDEX IF NOT EXISTS ix_stock_product ON inventory.stock (product_id);
