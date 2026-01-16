# Security Audit Report
Generated: 2025-01-XX

## Critical Vulnerabilities

### 1. **HARDCODED SECRETS** ⚠️ CRITICAL

#### Issue 1.1: Hardcoded JWT Secret Key
- **File**: `backend/main.py`
- **Line**: 28
- **Code**: `SECRET_KEY = "a_very_secret_key_for_jwt_replace_this"`
- **Risk**: Anyone with access to the code can forge JWT tokens and impersonate users
- **Fix**: 
```python
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable must be set")
```

#### Issue 1.2: Hardcoded API Keys
- **File**: `backend/core/news_scraper.py`
- **Lines**: 7-9
- **Code**: 
  - `GNEWS_API_KEY = "9f7e717acb032ceaadb99476cdaff97a"`
  - `NEWSAPI_API_KEY = "727b143d1e6c4b2299c1988de58663fa"`
  - `NEWSDATA_API_KEY = "pub_07c21dcbcd814b6e958e6ed63972d53b"`
- **Risk**: API keys exposed in source code, can be stolen and used by attackers
- **Fix**: Move to environment variables:
```python
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
NEWSAPI_API_KEY = os.getenv("NEWSAPI_API_KEY")
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
```

### 2. **COMMAND INJECTION** ⚠️ HIGH

#### Issue 2.1: User Input in Subprocess Command
- **File**: `backend/main.py`
- **Lines**: 209-215
- **Code**: 
```python
command = [
    python_executable, 
    engine_script, 
    server_seed, 
    bet.client_seed,  # User-controlled input
    nonce
]
```
- **Risk**: Malicious `client_seed` could inject shell commands if not properly sanitized
- **Fix**: Validate and sanitize `client_seed`:
```python
import re

# Validate client_seed (only alphanumeric and hyphens)
if not re.match(r'^[a-zA-Z0-9\-_]+$', bet.client_seed):
    raise HTTPException(status_code=400, detail="Invalid client_seed format")

# Use list form (already done, but ensure no shell=True)
result = subprocess.run(
    command,
    capture_output=True,
    text=True,
    check=True,
    timeout=30,
    shell=False  # Explicitly set to False
)
```

### 3. **INSECURE API ENDPOINTS** ⚠️ HIGH

#### Issue 3.1: Overly Permissive CORS
- **File**: `backend/main.py`
- **Lines**: 40-46
- **Code**: 
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)
```
- **Risk**: Allows any origin, method, and header in production could lead to CSRF attacks
- **Fix**: Restrict CORS in production:
```python
import os

# Only allow all in development
if os.getenv("ENVIRONMENT") == "development":
    allow_origins = ["http://localhost:3000", "http://localhost:3001"]
    allow_methods = ["*"]
    allow_headers = ["*"]
else:
    # Production: strict CORS
    allow_origins = [os.getenv("FRONTEND_URL", "https://yourdomain.com")]
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization"]
```

#### Issue 3.2: No Rate Limiting
- **File**: `backend/main.py`
- **Risk**: Endpoints can be abused for DoS attacks or brute force
- **Fix**: Add rate limiting middleware:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/token")
@limiter.limit("5/minute")  # 5 login attempts per minute
async def login_for_access_token(...):
    ...
```

#### Issue 3.3: Weak JWT Configuration
- **File**: `backend/main.py`
- **Line**: 28-30
- **Risk**: No expiration validation, weak secret
- **Fix**: Already has expiration, but ensure secret is strong:
```python
# Generate strong secret: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # Must be at least 32 bytes
if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
```

### 4. **PATH TRAVERSAL** ⚠️ MEDIUM

#### Issue 4.1: File Path Construction
- **File**: `backend/main.py`
- **Line**: 129
- **Code**: `with open("simulation/world_state.json", "r") as f:`
- **Risk**: If user input affects path, could read arbitrary files
- **Fix**: Use absolute paths and validate:
```python
import os
from pathlib import Path

# Use absolute path
base_dir = Path(__file__).parent
state_file = base_dir / "simulation" / "world_state.json"

# Validate path is within allowed directory
if not str(state_file).startswith(str(base_dir)):
    raise HTTPException(status_code=403, detail="Invalid path")

with open(state_file, "r") as f:
    ...
```

### 5. **INFORMATION DISCLOSURE** ⚠️ MEDIUM

#### Issue 5.1: Error Messages Expose Internal Details
- **File**: `backend/main.py`
- **Lines**: 229, 232, 234
- **Code**: Error messages include stack traces and internal details
- **Risk**: Reveals system architecture and potential attack vectors
- **Fix**: Sanitize error messages in production:
```python
import logging

logger = logging.getLogger(__name__)

try:
    result = subprocess.run(...)
except subprocess.CalledProcessError as e:
    logger.error(f"Engine script failed: {e.stderr}", exc_info=True)
    raise HTTPException(
        status_code=500, 
        detail="Game engine error. Please try again."
    )
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise HTTPException(
        status_code=500,
        detail="An error occurred. Please contact support."
    )
```

### 6. **XSS (Cross-Site Scripting)** ⚠️ LOW

#### Issue 6.1: User Input Displayed Without Sanitization
- **File**: `frontend/app/betting/page.jsx`
- **Lines**: 74, 142-143
- **Code**: User input (`message`, `error`) displayed directly
- **Risk**: If backend returns malicious content, it could execute scripts
- **Fix**: React auto-escapes, but ensure backend sanitizes:
```python
from html import escape

message = escape(message)  # Sanitize before returning
```

### 7. **INSECURE FILE OPERATIONS** ⚠️ MEDIUM

#### Issue 7.1: No File Permission Checks
- **File**: `backend/core/blockchain_manager.py`
- **Line**: 22
- **Code**: `with open("abi.json", "r") as f:`
- **Risk**: Could read files outside intended directory
- **Fix**: Use absolute paths:
```python
import os
from pathlib import Path

abi_path = Path(__file__).parent.parent / "abi.json"
with open(abi_path, "r") as f:
    ...
```

### 8. **WEAK PASSWORD POLICY** ⚠️ MEDIUM

#### Issue 8.1: No Password Strength Validation
- **File**: `backend/main.py`
- **Lines**: 59-61
- **Risk**: Users can create accounts with weak passwords
- **Fix**: Add password validation:
```python
import re

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v
```

### 9. **INSECURE DEFAULT CONFIGURATION** ⚠️ MEDIUM

#### Issue 9.1: Database File Permissions
- **File**: `backend/core/database.py`
- **Line**: 4
- **Code**: `DATABASE_URL = "sqlite:///./database.db"`
- **Risk**: SQLite file may have insecure permissions
- **Fix**: Set proper file permissions:
```python
import os
from pathlib import Path

db_path = Path("database.db")
if db_path.exists():
    os.chmod(db_path, 0o600)  # Read/write for owner only
```

## Summary

**Critical Issues**: 2
**High Issues**: 2
**Medium Issues**: 5
**Low Issues**: 1

**Total Issues Found**: 10

## Recommended Action Plan

1. **Immediate (Critical)**:
   - Move all secrets to environment variables
   - Fix command injection vulnerability
   - Rotate all exposed API keys

2. **Short-term (High)**:
   - Implement rate limiting
   - Restrict CORS in production
   - Add input validation for subprocess commands

3. **Medium-term (Medium)**:
   - Add password strength requirements
   - Sanitize error messages
   - Use absolute paths for file operations

4. **Long-term (Low)**:
   - Implement comprehensive input sanitization
   - Add security headers
   - Set up security monitoring

