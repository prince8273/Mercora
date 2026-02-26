# Signup & Tenant Creation Flow - Complete Analysis

**Date:** February 24, 2026  
**Status:** ✅ FULLY IMPLEMENTED

---

## 🎯 ANSWER: YES! TENANT ID IS AUTOMATICALLY CREATED DURING SIGNUP

When a user signs up, your backend **automatically creates a new tenant** and assigns a unique `tenant_id` (UUID). Here's exactly how it works:

---

## 📋 SIGNUP FLOW (Step-by-Step)

### Step 1: User Submits Registration Form

**Endpoint:** `POST /api/v1/auth/register`

**Request Body:**
```json
{
  "email": "john@newcompany.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "tenant_slug": "new-company"
}
```

**Required Fields:**
- ✅ `email` - User's email (must be unique)
- ✅ `password` - Minimum 8 characters
- ✅ `tenant_slug` - Company identifier (e.g., "acme-corp", "my-store")
- ⚠️ `full_name` - Optional

---

### Step 2: Backend Validates Data

**File:** `src/api/auth.py` → `register()` function

**Validation Checks:**

```python
# 1. Check if email already exists
existing_user = await get_user_by_email(db, user_data.email)
if existing_user:
    raise HTTPException(
        status_code=400,
        detail="Email already registered"
    )

# 2. Check if tenant slug already exists
existing_tenant = await get_tenant_by_slug(db, user_data.tenant_slug)
if existing_tenant:
    raise HTTPException(
        status_code=400,
        detail="Tenant slug already taken"
    )
```

**Possible Errors:**
- ❌ Email already registered → 400 Bad Request
- ❌ Tenant slug already taken → 400 Bad Request
- ❌ Password too short → 422 Validation Error

---

### Step 3: Create New Tenant (AUTOMATIC!)

**File:** `src/crud/tenant.py` → `create_tenant()` function

**What Happens:**

```python
# Create tenant with auto-generated UUID
tenant = await create_tenant(
    db,
    name=user_data.tenant_slug.replace("-", " ").title(),  # "new-company" → "New Company"
    slug=user_data.tenant_slug,                            # "new-company"
    contact_email=user_data.email,                         # "john@newcompany.com"
    plan="free"                                            # Default plan
)

# Tenant object created:
# {
#   id: UUID('xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'),  ← AUTO-GENERATED!
#   name: "New Company",
#   slug: "new-company",
#   contact_email: "john@newcompany.com",
#   plan: "free",
#   max_products: 100,
#   max_users: 5,
#   is_active: True,
#   created_at: "2026-02-24T10:30:00Z"
# }
```

**Plan Limits (Automatic):**

| Plan | Max Products | Max Users |
|------|--------------|-----------|
| free | 100 | 5 |
| basic | 1,000 | 10 |
| pro | 10,000 | 50 |
| enterprise | 100,000 | 500 |

---

### Step 4: Create First User (Admin)

**File:** `src/crud/user.py` → `create_user()` function

**What Happens:**

```python
# Create user linked to the new tenant
user = await create_user(
    db,
    email=user_data.email,                    # "john@newcompany.com"
    password=user_data.password,              # Hashed with bcrypt
    tenant_id=tenant.id,                      # ← LINKED TO TENANT!
    full_name=user_data.full_name,            # "John Doe"
    is_superuser=False                        # First user is admin, not superuser
)

# User object created:
# {
#   id: UUID('yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy'),
#   email: "john@newcompany.com",
#   hashed_password: "$2b$12$...",
#   full_name: "John Doe",
#   tenant_id: UUID('xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'),  ← TENANT LINK!
#   is_active: True,
#   is_superuser: False,
#   created_at: "2026-02-24T10:30:00Z"
# }
```

---

### Step 5: Commit to Database

```python
await db.commit()
```

**Database Changes:**

**tenants table:**
```sql
INSERT INTO tenants (id, name, slug, plan, max_products, max_users, is_active)
VALUES (
  'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',  -- Auto-generated UUID
  'New Company',
  'new-company',
  'free',
  100,
  5,
  true
);
```

**users table:**
```sql
INSERT INTO users (id, email, hashed_password, full_name, tenant_id, is_active)
VALUES (
  'yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy',  -- Auto-generated UUID
  'john@newcompany.com',
  '$2b$12$...',
  'John Doe',
  'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',  -- Links to tenant
  true
);
```

---

### Step 6: Return User Response

**Response (201 Created):**
```json
{
  "id": "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy",
  "email": "john@newcompany.com",
  "full_name": "John Doe",
  "tenant_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "is_active": true,
  "is_superuser": false
}
```

**Frontend receives:**
- ✅ User ID
- ✅ Tenant ID (for reference)
- ✅ User details

---

## 🔐 LOGIN FLOW (After Signup)

### Step 1: User Logs In

**Endpoint:** `POST /api/v1/auth/login`

**Request:**
```json
{
  "email": "john@newcompany.com",
  "password": "SecurePass123!"
}
```

### Step 2: Backend Creates JWT Token

**File:** `src/api/auth.py` → `login()` function

```python
# Authenticate user
user = await authenticate_user(db, credentials.email, credentials.password)

# Create JWT token with tenant_id embedded
access_token = create_access_token(
    user_id=user.id,
    tenant_id=user.tenant_id,  # ← TENANT ID EMBEDDED IN TOKEN!
    role="admin",
    expires_delta=timedelta(minutes=30)
)
```

### Step 3: JWT Token Structure

**Token Payload:**
```json
{
  "sub": "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy",      // User ID
  "tenant_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", // Tenant ID
  "role": "admin",
  "exp": 1708876800,                                   // Expiration
  "iat": 1708875000                                    // Issued at
}
```

### Step 4: Response

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

## 🔄 COMPLETE SIGNUP → LOGIN → API CALL FLOW

### Example: New Company Signs Up and Fetches Products

**1. Signup:**
```bash
POST /api/v1/auth/register
{
  "email": "jane@acme-corp.com",
  "password": "AcmePass123!",
  "full_name": "Jane Smith",
  "tenant_slug": "acme-corp"
}

Response:
{
  "id": "user-uuid-1",
  "tenant_id": "tenant-uuid-acme",  ← NEW TENANT CREATED!
  "email": "jane@acme-corp.com",
  ...
}
```

**2. Login:**
```bash
POST /api/v1/auth/login
{
  "email": "jane@acme-corp.com",
  "password": "AcmePass123!"
}

Response:
{
  "access_token": "eyJ...",  ← Contains tenant_id: "tenant-uuid-acme"
  "token_type": "bearer"
}
```

**3. Fetch Products:**
```bash
GET /api/v1/products
Authorization: Bearer eyJ...

Middleware extracts: tenant_id = "tenant-uuid-acme"
Query executes: SELECT * FROM products WHERE tenant_id = 'tenant-uuid-acme'

Response:
{
  "products": []  ← Empty (new tenant has no products yet)
}
```

**4. Upload Products:**
```bash
POST /api/v1/csv/upload/products
Authorization: Bearer eyJ...
File: products.csv

Backend automatically sets: tenant_id = "tenant-uuid-acme" for all products
```

**5. Fetch Products Again:**
```bash
GET /api/v1/products
Authorization: Bearer eyJ...

Response:
{
  "products": [
    {
      "id": "product-1",
      "tenant_id": "tenant-uuid-acme",  ← Linked to tenant
      "sku": "SKU-001",
      "name": "Product 1",
      ...
    }
  ]
}
```

---

## 🏢 MULTI-TENANT SCENARIO

### Scenario: Two Companies Sign Up

**Company A (Acme Corp):**
```bash
POST /api/v1/auth/register
{
  "email": "admin@acme.com",
  "tenant_slug": "acme-corp"
}

→ Creates:
  - Tenant ID: aaaa-aaaa-aaaa-aaaa
  - User ID: user-1
```

**Company B (Beta Inc):**
```bash
POST /api/v1/auth/register
{
  "email": "admin@beta.com",
  "tenant_slug": "beta-inc"
}

→ Creates:
  - Tenant ID: bbbb-bbbb-bbbb-bbbb
  - User ID: user-2
```

**Result:**
- ✅ Two separate tenants created
- ✅ Each has unique tenant_id
- ✅ Each has their own admin user
- ✅ Data is completely isolated

**When they fetch products:**

```bash
# Acme Corp
GET /api/v1/products
Authorization: Bearer <acme-token>
→ Returns products WHERE tenant_id = 'aaaa-aaaa-aaaa-aaaa'

# Beta Inc
GET /api/v1/products
Authorization: Bearer <beta-token>
→ Returns products WHERE tenant_id = 'bbbb-bbbb-bbbb-bbbb'
```

---

## 📊 DATABASE STRUCTURE AFTER SIGNUP

### tenants table:
```
id                                   | name        | slug       | plan | max_products | max_users | is_active
-------------------------------------|-------------|------------|------|--------------|-----------|----------
aaaa-aaaa-aaaa-aaaa                 | Acme Corp   | acme-corp  | free | 100          | 5         | true
bbbb-bbbb-bbbb-bbbb                 | Beta Inc    | beta-inc   | free | 100          | 5         | true
```

### users table:
```
id          | email            | tenant_id           | full_name   | is_active | is_superuser
------------|------------------|---------------------|-------------|-----------|-------------
user-1      | admin@acme.com   | aaaa-aaaa-aaaa-aaaa | Admin User  | true      | false
user-2      | admin@beta.com   | bbbb-bbbb-bbbb-bbbb | Admin User  | true      | false
```

### products table (after data upload):
```
id          | tenant_id           | sku     | name       | price
------------|---------------------|---------|------------|-------
prod-1      | aaaa-aaaa-aaaa-aaaa | SKU-001 | Product A1 | 99.99
prod-2      | aaaa-aaaa-aaaa-aaaa | SKU-002 | Product A2 | 149.99
prod-3      | bbbb-bbbb-bbbb-bbbb | SKU-001 | Product B1 | 79.99
prod-4      | bbbb-bbbb-bbbb-bbbb | SKU-002 | Product B2 | 199.99
```

**Notice:**
- ✅ Each product has `tenant_id`
- ✅ Acme Corp has 2 products (tenant_id: aaaa...)
- ✅ Beta Inc has 2 products (tenant_id: bbbb...)
- ✅ Same SKU can exist in different tenants

---

## 🎯 KEY POINTS

### ✅ Automatic Tenant Creation
1. **User signs up** → Backend creates tenant automatically
2. **Tenant gets unique UUID** → Generated by database
3. **User is linked to tenant** → `user.tenant_id = tenant.id`
4. **JWT contains tenant_id** → Embedded in token payload
5. **All API calls filtered** → Middleware extracts tenant_id

### ✅ No Manual Tenant Management Needed
- User doesn't need to "create a tenant" separately
- Tenant is created as part of signup
- First user becomes admin of the tenant
- Additional users can be invited later (same tenant_id)

### ✅ Tenant Slug
- **Purpose:** Human-readable identifier (e.g., "acme-corp")
- **Used for:** Subdomain routing (future), branding
- **Must be unique:** No two tenants can have same slug
- **Format:** Lowercase, hyphens allowed, 3-100 characters

### ✅ Default Plan
- New tenants start on **"free" plan**
- Limits: 100 products, 5 users
- Can be upgraded later (basic, pro, enterprise)

---

## 🔍 VERIFICATION

### Check if Tenant Was Created:

**Query Database:**
```sql
-- Find tenant by slug
SELECT * FROM tenants WHERE slug = 'acme-corp';

-- Find user's tenant
SELECT u.email, u.full_name, t.name, t.slug
FROM users u
JOIN tenants t ON u.tenant_id = t.id
WHERE u.email = 'admin@acme.com';
```

**API Endpoint:**
```bash
GET /api/v1/auth/me
Authorization: Bearer <token>

Response:
{
  "id": "user-uuid",
  "email": "admin@acme.com",
  "tenant_id": "tenant-uuid",  ← TENANT ID HERE!
  "is_active": true
}
```

---

## 🚀 FRONTEND INTEGRATION

### Signup Form:

```jsx
// SignupPage.jsx
const handleSignup = async (formData) => {
  const response = await fetch('/api/v1/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: formData.email,
      password: formData.password,
      full_name: formData.fullName,
      tenant_slug: formData.companySlug  // e.g., "my-company"
    })
  });
  
  const data = await response.json();
  
  if (response.ok) {
    // Tenant created! User can now login
    console.log('Tenant ID:', data.tenant_id);
    navigate('/login');
  }
};
```

### Login & Store Token:

```jsx
// LoginPage.jsx
const handleLogin = async (credentials) => {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials)
  });
  
  const data = await response.json();
  
  if (response.ok) {
    // Store token (contains tenant_id)
    localStorage.setItem('token', data.access_token);
    
    // All subsequent API calls will use this token
    // Middleware will extract tenant_id automatically
    navigate('/dashboard');
  }
};
```

---

## ✅ CONCLUSION

### YES! Tenant ID is AUTOMATICALLY created during signup:

1. ✅ User submits signup form with `tenant_slug`
2. ✅ Backend creates new tenant with auto-generated UUID
3. ✅ Backend creates user linked to that tenant
4. ✅ User logs in and receives JWT with `tenant_id`
5. ✅ All API calls automatically filtered by `tenant_id`

**You don't need to do anything extra!** The tenant creation is built into the signup flow. Each new signup creates a new tenant, and the user becomes the admin of that tenant.

**For SaaS:**
- Each customer signs up → Gets their own tenant
- Each tenant has unique UUID
- Data is automatically isolated
- No manual tenant management needed

Your backend is **production-ready for multi-tenant SaaS** with automatic tenant provisioning! 🎉
