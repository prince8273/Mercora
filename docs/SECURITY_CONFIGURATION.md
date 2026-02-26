# Security Configuration Guide

## Overview
This document provides guidance on configuring security measures for the E-commerce Intelligence Agent system, including encryption, TLS, and secrets management.

## Table of Contents
1. [Encryption at Rest](#encryption-at-rest)
2. [Encryption in Transit (TLS)](#encryption-in-transit-tls)
3. [Secrets Management](#secrets-management)
4. [Role-Based Access Control](#role-based-access-control)
5. [Security Best Practices](#security-best-practices)

---

## Encryption at Rest

### PostgreSQL Encryption

#### Option 1: Transparent Data Encryption (TDE)
PostgreSQL supports encryption at rest through various methods:

**Using pgcrypto Extension:**
```sql
-- Enable pgcrypto extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Example: Encrypt sensitive columns
CREATE TABLE sensitive_data (
    id UUID PRIMARY KEY,
    encrypted_field BYTEA
);

-- Insert encrypted data
INSERT INTO sensitive_data (id, encrypted_field)
VALUES (
    gen_random_uuid(),
    pgp_sym_encrypt('sensitive data', 'encryption_key')
);

-- Query encrypted data
SELECT 
    id,
    pgp_sym_decrypt(encrypted_field, 'encryption_key') AS decrypted_field
FROM sensitive_data;
```

#### Option 2: Full Disk Encryption
For production deployments, use full disk encryption at the OS level:

**Linux (LUKS):**
```bash
# Encrypt the disk partition
cryptsetup luksFormat /dev/sdb1

# Open the encrypted partition
cryptsetup luksOpen /dev/sdb1 encrypted_disk

# Format and mount
mkfs.ext4 /dev/mapper/encrypted_disk
mount /dev/mapper/encrypted_disk /var/lib/postgresql
```

**Cloud Providers:**
- **AWS RDS:** Enable encryption at rest when creating the database
- **Google Cloud SQL:** Enable encryption by default
- **Azure Database:** Enable Transparent Data Encryption (TDE)

#### Option 3: Application-Level Encryption
Encrypt sensitive fields before storing in database:

```python
from cryptography.fernet import Fernet

# Generate encryption key (store securely!)
key = Fernet.generate_key()
cipher = Fernet(key)

# Encrypt data
encrypted_data = cipher.encrypt(b"sensitive information")

# Decrypt data
decrypted_data = cipher.decrypt(encrypted_data)
```

### Redis Encryption
For Redis cache encryption:

```bash
# Use Redis with TLS
redis-cli --tls \
    --cert /path/to/redis.crt \
    --key /path/to/redis.key \
    --cacert /path/to/ca.crt
```

---

## Encryption in Transit (TLS)

### TLS 1.3 Configuration

#### FastAPI/Uvicorn with TLS
```python
# main.py
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=443,
        ssl_keyfile="/path/to/private.key",
        ssl_certfile="/path/to/certificate.crt",
        ssl_version=3,  # TLS 1.3
        ssl_cert_reqs=2,  # Require client certificates (optional)
    )
```

#### Nginx Reverse Proxy (Recommended)
```nginx
server {
    listen 443 ssl http2;
    server_name api.example.com;

    # TLS 1.3 only
    ssl_protocols TLSv1.3;
    ssl_prefer_server_ciphers off;

    # Certificates
    ssl_certificate /etc/ssl/certs/certificate.crt;
    ssl_certificate_key /etc/ssl/private/private.key;

    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/ssl/certs/ca-bundle.crt;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.example.com;
    return 301 https://$server_name$request_uri;
}
```

#### PostgreSQL TLS Configuration
```bash
# postgresql.conf
ssl = on
ssl_cert_file = '/path/to/server.crt'
ssl_key_file = '/path/to/server.key'
ssl_ca_file = '/path/to/ca.crt'
ssl_min_protocol_version = 'TLSv1.3'
```

Connection string with TLS:
```python
DATABASE_URL = "postgresql+asyncpg://user:pass@host:5432/db?ssl=require&sslmode=verify-full"
```

---

## Secrets Management

### Option 1: Environment Variables (Development)
```bash
# .env file (NEVER commit to git!)
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@localhost/db
JWT_SECRET=your-jwt-secret-here
ENCRYPTION_KEY=your-encryption-key-here
```

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str
    database_url: str
    jwt_secret: str
    encryption_key: str
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

### Option 2: HashiCorp Vault (Production)
```python
import hvac

# Initialize Vault client
client = hvac.Client(url='https://vault.example.com:8200')
client.token = 'your-vault-token'

# Read secrets
secret = client.secrets.kv.v2.read_secret_version(
    path='ecommerce-intelligence/prod'
)

database_url = secret['data']['data']['database_url']
secret_key = secret['data']['data']['secret_key']
```

### Option 3: AWS Secrets Manager
```python
import boto3
import json

# Create a Secrets Manager client
client = boto3.client('secretsmanager', region_name='us-east-1')

# Retrieve secret
response = client.get_secret_value(SecretId='ecommerce-intelligence/prod')
secrets = json.loads(response['SecretString'])

database_url = secrets['database_url']
secret_key = secrets['secret_key']
```

### Option 4: Azure Key Vault
```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Initialize Key Vault client
credential = DefaultAzureCredential()
client = SecretClient(
    vault_url="https://your-vault.vault.azure.net/",
    credential=credential
)

# Retrieve secrets
database_url = client.get_secret("database-url").value
secret_key = client.get_secret("secret-key").value
```

### Secret Rotation
Implement automatic secret rotation:

```python
from datetime import datetime, timedelta

class SecretRotationService:
    """Service for rotating secrets periodically."""
    
    def __init__(self, rotation_interval_days: int = 90):
        self.rotation_interval = timedelta(days=rotation_interval_days)
        self.last_rotation = datetime.utcnow()
    
    def should_rotate(self) -> bool:
        """Check if secrets should be rotated."""
        return datetime.utcnow() - self.last_rotation > self.rotation_interval
    
    async def rotate_secrets(self):
        """Rotate all secrets."""
        if not self.should_rotate():
            return
        
        # Rotate JWT secret
        new_jwt_secret = generate_secure_secret()
        await update_secret('jwt_secret', new_jwt_secret)
        
        # Rotate encryption key
        new_encryption_key = generate_encryption_key()
        await update_secret('encryption_key', new_encryption_key)
        
        self.last_rotation = datetime.utcnow()
```

---

## Role-Based Access Control

### Role Hierarchy
```
Superuser (Full system access)
  └── Admin (Tenant administration)
      └── Analyst (Data analysis)
          └── User (Basic access)
              └── Viewer (Read-only)
```

### Permission Matrix

| Permission | Superuser | Admin | Analyst | User | Viewer |
|-----------|-----------|-------|---------|------|--------|
| Read Data | ✓ | ✓ | ✓ | ✓ | ✓ |
| Write Data | ✓ | ✓ | ✗ | ✗ | ✗ |
| Delete Data | ✓ | ✓ | ✗ | ✗ | ✗ |
| Execute Query | ✓ | ✓ | ✓ | ✓ | ✗ |
| Deep Mode | ✓ | ✓ | ✓ | ✗ | ✗ |
| View Reports | ✓ | ✓ | ✓ | ✓ | ✓ |
| Create Reports | ✓ | ✓ | ✓ | ✗ | ✗ |
| Export Reports | ✓ | ✓ | ✓ | ✗ | ✗ |
| Manage Users | ✓ | ✓ | ✗ | ✗ | ✗ |
| Manage Settings | ✓ | ✓ | ✗ | ✗ | ✗ |
| View Audit Logs | ✓ | ✓ | ✗ | ✗ | ✗ |
| System Admin | ✓ | ✗ | ✗ | ✗ | ✗ |

### Usage in API Endpoints
```python
from fastapi import APIRouter, Depends
from src.auth.rbac import require_permission, require_role, Permission, RoleType

router = APIRouter()

# Require specific permission
@router.post("/data")
async def create_data(
    data: dict,
    _: User = Depends(require_permission(Permission.WRITE_DATA))
):
    # Only users with WRITE_DATA permission can access
    return {"status": "created"}

# Require specific role
@router.get("/admin/users")
async def list_users(
    _: User = Depends(require_role(RoleType.ADMIN))
):
    # Only admins and superusers can access
    return {"users": []}

# Multiple permission checks
@router.delete("/data/{id}")
async def delete_data(
    id: str,
    current_user: User = Depends(require_permission(Permission.DELETE_DATA)),
    db: AsyncSession = Depends(get_db)
):
    # Check additional permissions programmatically
    await RBACService.require_permission(
        current_user,
        Permission.VIEW_AUDIT_LOGS,
        db
    )
    return {"status": "deleted"}
```

---

## Security Best Practices

### 1. Password Security
```python
# Use strong password hashing (bcrypt)
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Increase for more security
)

# Enforce password complexity
def validate_password(password: str) -> bool:
    """Validate password meets security requirements."""
    if len(password) < 12:
        return False
    if not any(c.isupper() for c in password):
        return False
    if not any(c.islower() for c in password):
        return False
    if not any(c.isdigit() for c in password):
        return False
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False
    return True
```

### 2. JWT Token Security
```python
# Use strong secrets
SECRET_KEY = secrets.token_urlsafe(32)  # 256-bit key

# Short expiration times
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Include security claims
def create_access_token(user_id: UUID, tenant_id: UUID):
    return jwt.encode({
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "exp": datetime.utcnow() + timedelta(minutes=15),
        "iat": datetime.utcnow(),
        "jti": str(uuid4()),  # Unique token ID for revocation
    }, SECRET_KEY, algorithm="HS256")
```

### 3. Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/login")
@limiter.limit("5/minute")  # 5 attempts per minute
async def login(request: Request):
    # Login logic
    pass
```

### 4. Input Validation
```python
from pydantic import BaseModel, validator, constr

class UserInput(BaseModel):
    email: constr(max_length=255)
    name: constr(max_length=100)
    
    @validator('email')
    def validate_email(cls, v):
        # Email validation
        if '@' not in v:
            raise ValueError('Invalid email')
        return v.lower()
```

### 5. SQL Injection Prevention
```python
# ALWAYS use parameterized queries
# GOOD:
result = await db.execute(
    select(User).where(User.email == email)
)

# BAD (vulnerable to SQL injection):
# result = await db.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

### 6. CORS Configuration
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600,
)
```

### 7. Security Headers
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware

# Trusted hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["api.example.com", "*.example.com"]
)

# Secure session cookies
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie="session",
    max_age=3600,
    same_site="strict",
    https_only=True
)
```

### 8. Audit Logging
```python
async def log_security_event(
    event_type: str,
    user_id: UUID,
    tenant_id: UUID,
    details: dict
):
    """Log security-relevant events."""
    logger.info(
        f"Security Event: {event_type}",
        extra={
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "event_type": event_type,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

---

## Compliance Checklist

- [ ] Encryption at rest enabled for database
- [ ] TLS 1.3 enforced for all network communication
- [ ] Secrets stored in secure vault (not in code/git)
- [ ] Strong password policy enforced
- [ ] JWT tokens with short expiration
- [ ] Role-based access control implemented
- [ ] Rate limiting on authentication endpoints
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (parameterized queries)
- [ ] CORS properly configured
- [ ] Security headers configured
- [ ] Audit logging for security events
- [ ] Regular security audits scheduled
- [ ] Dependency vulnerability scanning enabled
- [ ] Secrets rotation policy in place

---

## Security Incident Response

### 1. Detection
- Monitor audit logs for suspicious activity
- Set up alerts for failed authentication attempts
- Track unusual API usage patterns

### 2. Response
```python
async def handle_security_incident(incident_type: str, details: dict):
    """Handle security incident."""
    # Log incident
    logger.critical(f"Security Incident: {incident_type}", extra=details)
    
    # Notify security team
    await send_alert(
        channel="security",
        message=f"Security incident detected: {incident_type}",
        details=details
    )
    
    # Take automated action
    if incident_type == "brute_force":
        await block_ip(details["ip_address"])
    elif incident_type == "unauthorized_access":
        await revoke_tokens(details["user_id"])
```

### 3. Recovery
- Rotate compromised secrets
- Review and update access controls
- Patch vulnerabilities
- Document lessons learned

---

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CIS Controls](https://www.cisecurity.org/controls/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/security.html)
