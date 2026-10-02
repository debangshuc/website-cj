# Accessory Inventory Backend API

FastAPI backend for the Accessory Inventory management system.

## Architecture

The backend follows a 3-tier architecture with dependency injection:

```
FastAPI Routing Layer (app/api/)
        ↓
Service Layer (app/services/)
        ↓
Repository Protocol & In-Memory Store (app/repositories/)
```

- **Routes**: Thin request/response adapters that validate input parameters and return standard HTTP response codes.
- **Services**: Pure business logic (e.g. inventory calculation, soft deletion rules, stock validation, and sales recording).
- **Repositories**: Data access abstraction using `ProductRepositoryProtocol` and `SalesRepositoryProtocol`. The in-memory implementation provides full functionality without external database dependencies and will be seamlessly replaced by a PostgreSQL/Supabase repository in future tasks.

## Quick Start

### 1. Install Dependencies
```bash
cd backend
python -m pip install -r requirements.txt
```

### 2. Run the Development Server
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### 3. API Documentation & Endpoints
- **Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: `GET http://localhost:8000/health`
- **Root Metadata**: `GET http://localhost:8000/`

## API Endpoints Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health status |
| `GET` | `/api/products` | List active products (supports `search`, `category`, `stock_status`, `include_inactive`) |
| `GET` | `/api/products/{id}` | Retrieve product details by ID |
| `POST` | `/api/products` | Create a new product |
| `PATCH` | `/api/products/{id}` | Update product fields |
| `DELETE` | `/api/products/{id}` | Soft delete product (`is_active = false`) |
| `GET` | `/api/sales` | List sales transactions (supports `search`, `category`, `date_filter`, `sort_by`) |
| `GET` | `/api/sales/{id}` | Retrieve single sales transaction |
| `POST` | `/api/sales` | Record sale, calculate total, and decrement inventory |
| `GET` | `/api/dashboard/summary` | Aggregate live inventory and sales KPI metrics |

## Running the Automated Test Suite

Run the full pytest suite:

```bash
cd backend
python -m pytest tests/ -v
```
