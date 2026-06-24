# JWT Token Generation for BBBot Control Center

## Current State

**Main.py** has NO `/login` or `/token` endpoint. Bots can't self-generate JWT tokens.

**Endpoints that exist:**
- `GET /health`, `GET /api/health` — public, no auth
- `GET /status`, `GET /api/status` — public, no auth
- `POST /*/bootstrap`, `POST /*/analyze`, `POST /*/trade` — bot operations (may be protected)

---

## Solution: Add a Token Endpoint

Choose **ONE** of these options based on your security model:

### Option A: Service Account Token (Recommended for Bots)

**Best for**: Bots that need fixed, long-lived tokens.

Add this to `Main.py`:

```python
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from pydantic import BaseModel
import os
from jose import jwt

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"
BOT_USERNAME = os.getenv("BOT_USERNAME", "bentley_bots")
BOT_PASSWORD = os.getenv("BOT_PASSWORD", "change-me-in-production")

class TokenRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

def create_access_token(subject: str, expires_delta: timedelta = None):
    if expires_delta is None:
        expires_delta = timedelta(hours=24)  # Default: 24 hours
    
    expire = datetime.utcnow() + expires_delta
    to_encode = {"sub": subject, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, int(expire.timestamp())

@app.post("/token", response_model=TokenResponse)
async def login(request: TokenRequest):
    """
    Generate a JWT token for bot service accounts.
    
    Usage in Postman:
        POST http://localhost:5001/token
        Body: {"username": "bentley_bots", "password": "<your_password>"}
    
    Then use the returned access_token as Bearer in subsequent requests.
    """
    if request.username != BOT_USERNAME or request.password != BOT_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    token, exp_ts = create_access_token(request.username)
    expires_in_seconds = exp_ts - int(datetime.utcnow().timestamp())
    
    return TokenResponse(
        access_token=token,
        expires_in=expires_in_seconds
    )
```

**Setup:**

1. Add to `.env`:
   ```bash
   JWT_SECRET_KEY=your-super-secret-key-min-32-chars
   BOT_USERNAME=bentley_bots
   BOT_PASSWORD=your-secure-password
   ```

2. Restart Main.py:
   ```powershell
   # In terminal with activated venv
   python -m uvicorn Main:app --host 0.0.0.0 --port 5001 --reload
   ```

3. Test in Postman:
   ```bash
   POST http://localhost:5001/token
   Content-Type: application/json
   
   {
     "username": "bentley_bots",
     "password": "<your_password>"
   }
   ```

4. Copy the `access_token` and set it as `jwt_token` in Postman collection variables.

---

### Option B: Pre-generated Token (For Dev/Testing Only)

If you don't want a `/token` endpoint, generate tokens manually and store them in `.env`:

```python
from datetime import datetime, timedelta
from jose import jwt

# Run this once to generate a token
SECRET_KEY = "your-secret-key"
payload = {
    "sub": "bentley_bots",
    "exp": datetime.utcnow() + timedelta(hours=24)
}
token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
print(f"JWT_TOKEN={token}")
```

Add to `.env`:
```bash
JWT_TOKEN=<generated_token>
```

Then in Main.py, set collection variable directly:
```bash
jwt_token = os.getenv("JWT_TOKEN")
```

**⚠️ Drawback**: Token expires after 24 hours. You have to manually regenerate it.

---

### Option C: OAuth2 with Username/Password (For Multi-User)

If you have multiple bot accounts with different permissions:

```python
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Define user database (replace with real DB)
USERS_DB = {
    "bentley_bots": {"password": "secure_password", "role": "bot"},
    "admin_user": {"password": "admin_password", "role": "admin"}
}

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = USERS_DB.get(form_data.username)
    if not user or user["password"] != form_data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token, exp_ts = create_access_token(form_data.username)
    return {"access_token": token, "token_type": "bearer"}

async def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        if not subject:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return subject

# Protect routes
@app.get("/api/status")
async def status(current_user: str = Depends(verify_token)):
    return {"status": "ok", "user": current_user}
```

---

## Integration with Bot Workflows

Once you have a `/token` endpoint, bots can request tokens at startup:

**Python (in your bot's init):**
```python
import requests

def get_bot_token():
    response = requests.post(
        "http://localhost:5001/token",
        json={
            "username": os.getenv("BOT_USERNAME", "bentley_bots"),
            "password": os.getenv("BOT_PASSWORD")
        }
    )
    response.raise_for_status()
    return response.json()["access_token"]

# Then use in requests
token = get_bot_token()
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("http://localhost:5001/api/status", headers=headers)
```

**PowerShell (in start scripts):**
```powershell
$response = Invoke-RestMethod -Uri "http://localhost:5001/token" `
  -Method POST `
  -ContentType "application/json" `
  -Body (@{
    username = $env:BOT_USERNAME
    password = $env:BOT_PASSWORD
  } | ConvertTo-Json)

$token = $response.access_token
[Environment]::SetEnvironmentVariable("JWT_TOKEN", $token, "Process")
```

---

## Validation Workflow

After adding `/token` endpoint:

1. **Get Token**
   ```bash
   POST http://localhost:5001/token
   Body: {"username": "bentley_bots", "password": "..."}
   Response: {"access_token": "eyJ...", "expires_in": 86400}
   ```

2. **Use Token in Postman (Folder 5)**
   ```bash
   Set jwt_token = response.access_token
   Run "Decode JWT + Assert Not Expired" ✅
   ```

3. **Use Token in Bot Code**
   ```python
   headers = {"Authorization": f"Bearer {token}"}
   # All bot requests include this header
   ```

---

## Security Best Practices

1. **Use strong secrets**: `JWT_SECRET_KEY` should be >32 characters
2. **Rotate tokens**: Set `expires_delta = timedelta(hours=1)` for bots, refresh on each start
3. **Environment variables only**: Never commit passwords or secrets
4. **HTTPS in production**: JWTs are not encrypted, only signed. Use HTTPS to prevent interception
5. **Rate limiting**: Add `slowapi` or similar to prevent token-generation DOS:
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   
   @app.post("/token")
   @limiter.limit("5/minute")
   async def login(request: TokenRequest):
       # ...
   ```

---

## Choosing Your Option

| Option | Best For | Effort | Security |
|--------|----------|--------|----------|
| **A** (Service Account) | Bots with fixed creds | Medium | High (configurable expiry) |
| **B** (Pre-generated) | Quick testing | Low | Low (static token) |
| **C** (OAuth2 Multi-user) | Multiple bots + users | High | Highest (role-based) |

**Recommendation for BBBot**: Use **Option A** for dev, Option C for prod.

---

## FAQ

**Q: Can I use the same token for all bots?**  
A: Yes. In Option A, all bots use `BOT_USERNAME`/`BOT_PASSWORD`. They all get the same token subject.

**Q: How long should tokens live?**  
A: For bots: 1–24 hours. For API clients: 15–60 minutes. Balance security (shorter = less exposure) vs. operational burden (refresh overhead).

**Q: What if a bot's token expires mid-operation?**  
A: Bots should:
   1. Catch 401 responses
   2. Request a new token
   3. Retry the original request
   ```python
   response = requests.get(url, headers={"Authorization": f"Bearer {token}"})
   if response.status_code == 401:
       token = get_bot_token()  # Refresh
       response = requests.get(url, headers={"Authorization": f"Bearer {token}"})
   ```

**Q: Can I bypass JWT for localhost?**  
A: Yes, but not recommended. Instead:
   - Use `@app.get("/api/status")` without auth for health checks
   - Require auth only for sensitive operations
   - Implement "if local, skip auth" logic (careful in prod!)

---

Next Steps:
1. Pick **Option A** above
2. Add the code to `Main.py`
3. Set `.env` variables
4. Restart Main.py
5. Test in Postman folder 5 ✅
