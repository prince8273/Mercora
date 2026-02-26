# Bugfix Requirements Document

## Introduction

This document addresses two critical bugs preventing the dashboard from loading after user login. The first bug is a database schema mismatch where the Product model defines a `cost` column that doesn't exist in the database table, causing SQLAlchemy queries to fail. The second bug is a URL configuration issue where API requests are duplicated with double `/api/v1` prefixes due to misconfigured Vite proxy and Axios baseURL settings. Both bugs must be fixed to restore dashboard functionality.

## Bug Analysis

### Current Behavior (Defect)

**Bug 1: Missing Database Column**

1.1 WHEN the dashboard API queries Product data THEN the system crashes with `sqlite3.OperationalError: no such column: products.cost`

1.2 WHEN SQLAlchemy attempts to SELECT from the products table THEN the query fails because the cost column is missing from the database schema

1.3 WHEN the dashboard loads after login THEN the system displays "Failed to load dashboard data" error due to the database query failure

**Bug 2: Double API Prefix**

1.4 WHEN the frontend makes API requests with Axios THEN the URLs contain duplicate prefixes `/api/v1/api/v1/...` instead of `/api/v1/...`

1.5 WHEN Vite proxy forwards requests THEN the system logs show errors like `[vite] http proxy error: /api/v1/api/v1/amazon/upload`

1.6 WHEN API requests are made with the double prefix THEN the requests fail because the backend routes don't match the malformed URLs

### Expected Behavior (Correct)

**Bug 1: Missing Database Column**

2.1 WHEN the dashboard API queries Product data THEN the system SHALL successfully execute the query without database column errors

2.2 WHEN SQLAlchemy attempts to SELECT from the products table THEN the query SHALL succeed with the cost column present in the database schema

2.3 WHEN the dashboard loads after login THEN the system SHALL display dashboard data successfully without errors

**Bug 2: Double API Prefix**

2.4 WHEN the frontend makes API requests with Axios THEN the URLs SHALL contain a single correct prefix `/api/v1/...`

2.5 WHEN Vite proxy forwards requests THEN the system SHALL route requests correctly without duplicate prefixes

2.6 WHEN API requests are made THEN the requests SHALL succeed by matching the correct backend route paths

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the dashboard queries other Product model fields (excluding cost) THEN the system SHALL CONTINUE TO retrieve and display that data correctly

3.2 WHEN users access other API endpoints not related to the dashboard THEN the system SHALL CONTINUE TO process those requests successfully

3.3 WHEN existing Alembic migrations are run THEN the system SHALL CONTINUE TO apply them correctly without conflicts

3.4 WHEN the frontend makes requests to non-API routes THEN the Vite proxy SHALL CONTINUE TO handle them as before

3.5 WHEN the Product model is used in other parts of the application THEN the system SHALL CONTINUE TO function correctly with the cost column available

3.6 WHEN API requests are made from components other than those using Axios baseURL THEN the system SHALL CONTINUE TO route them correctly
