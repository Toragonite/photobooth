# UC-101: Admin Login

## Summary

Administrator authenticates to access the admin dashboard using a PIN code. This provides basic access control to prevent unauthorized users from accessing system management features.

---

## Actors

| Actor | Type | Description |
|-------|------|-------------|
| **Admin** | Primary | Person managing the photo booth |
| **System** | Secondary | Validates credentials, issues tokens |

---

## Preconditions

| ID | Condition |
|----|-----------|
| PRE-1 | Admin is on the Admin Login page (/admin) |
| PRE-2 | Admin knows the correct PIN |
| PRE-3 | System is operational |

---

## Trigger

Admin navigates to /admin or clicks Admin button on Home page.

---

## Main Flow

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Step                                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ Admin navigates to /admin                                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ System checks for existing valid token in localStorage         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ No valid token found, display PIN entry screen:                │
│     │ - Title: "Admin Login" / "관리자 로그인"                        │
│     │ - PIN input field (4-digit, masked)                            │
│     │ - Numeric keypad (for touch input)                             │
│     │ - [Login] button                                               │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4   │ Admin enters 4-digit PIN using keypad or keyboard              │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5   │ Admin taps [Login] button                                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6   │ Frontend sends POST /api/admin/auth:                           │
│     │ - Body: { pin: "1998" }                                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7   │ Backend validates PIN:                                         │
│     │ - Compare with stored PIN in settings                          │
│     │ - Check rate limiting (not exceeded)                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8   │ PIN is correct:                                                │
│     │ - Generate JWT token (30 minute expiry)                        │
│     │ - Reset failed attempt counter                                 │
│     │ - Log successful login                                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 9   │ Backend returns:                                               │
│     │ - { success: true, token: "eyJ...", expires_at: "..." }       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 10  │ Frontend stores token in localStorage                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ 11  │ Frontend navigates to /admin/dashboard                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 12  │ Dashboard loads, admin can access all features                 │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Alternative Flows

### AF-1: Valid Token Exists

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 2a  │ System finds token in localStorage                            │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2b  │ System checks token expiration                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2c  │ Token valid: Skip login, navigate directly to /admin/dashboard│
├─────┼────────────────────────────────────────────────────────────────┤
│ 2d  │ Token expired: Clear token, show login screen (step 3)        │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-2: PIN Auto-Submit on 4 Digits

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 4a  │ Admin enters 4th digit of PIN                                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4b  │ System automatically submits (no need to tap Login)           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4c  │ Continue from step 6                                          │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-3: Back to User Mode

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 3a  │ Admin taps [Back] or [Cancel] on login screen                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3b  │ Navigate back to Home page (/)                                │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Exception Flows

### EX-1: Invalid PIN

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Backend compares PIN: does not match                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Backend increments failed_attempts counter                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Backend returns:                                              │
│     │ - { success: false, error: "Invalid PIN" }                    │
│     │ - remaining_attempts: 5 - failed_attempts                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ Frontend displays error:                                      │
│     │ - "Invalid PIN" with shake animation                          │
│     │ - "X attempts remaining" warning                              │
├─────┼────────────────────────────────────────────────────────────────┤
│ E5  │ Frontend clears PIN input                                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ E6  │ Admin can retry                                               │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-2: Too Many Failed Attempts (Lockout)

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ failed_attempts >= 5                                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Backend calculates lockout time:                              │
│     │ - lockout_until = now + 5 minutes                             │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Backend returns:                                              │
│     │ - { success: false, error: "Too many attempts" }              │
│     │ - lockout_until: ISO timestamp                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ Frontend displays lockout screen:                             │
│     │ - "Too many failed attempts"                                  │
│     │ - "Try again in 5 minutes"                                    │
│     │ - Countdown timer                                             │
├─────┼────────────────────────────────────────────────────────────────┤
│ E5  │ PIN input disabled until lockout expires                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ E6  │ After lockout: failed_attempts reset, allow retry             │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-3: Network Error

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ POST /api/admin/auth fails (network error)                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Frontend displays:                                            │
│     │ - "Connection error. Please try again."                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ [Retry] button available                                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ Does NOT count as failed attempt                              │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Postconditions

### Success

| ID | Condition |
|----|-----------|
| POST-1 | JWT token stored in localStorage |
| POST-2 | Admin on Dashboard page |
| POST-3 | Session active for 30 minutes |
| POST-4 | Login event logged |

### Failure

| ID | Condition |
|----|-----------|
| POST-F1 | No token stored |
| POST-F2 | Admin remains on Login page |
| POST-F3 | Failed attempt logged |

---

## Business Rules

| ID | Rule |
|----|------|
| AUTH-BR-1 | PIN must be exactly 4 digits |
| AUTH-BR-2 | Token expires after 30 minutes |
| AUTH-BR-3 | Lockout after 5 failed attempts |
| AUTH-BR-4 | Lockout duration: 5 minutes |
| AUTH-BR-5 | Lockout counter resets after successful login |
| AUTH-BR-6 | PIN is configurable via settings |
| AUTH-BR-7 | Default PIN: 1998 |

---

## Security Considerations

| Risk | Mitigation |
|------|------------|
| Brute force | Rate limiting, lockout after 5 attempts |
| Token theft | Short expiry (30 min), localStorage (not cookie) |
| Shoulder surfing | Masked PIN input, numeric keypad |
| Network sniffing | HTTPS required |
| PIN exposure | Not logged, not in error messages |

---

## Data Requirements

### Auth Request

```typescript
interface AdminAuthRequest {
  pin: string;  // 4 digits, e.g., "1998"
}
```

### Auth Response

```typescript
interface AdminAuthResponse {
  success: boolean;
  token?: string;              // JWT if success
  expires_at?: string;         // ISO timestamp if success
  error?: string;              // Error message if failure
  remaining_attempts?: number; // Attempts left before lockout
  lockout_until?: string;      // ISO timestamp if locked out
}
```

### JWT Payload

```typescript
interface AdminTokenPayload {
  sub: "admin";                // Subject
  iat: number;                 // Issued at (Unix timestamp)
  exp: number;                 // Expiry (Unix timestamp)
  jti: string;                 // Token ID (for revocation if needed)
}
```

---

## UI/UX Requirements

### Login Screen

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  [←]                                                            │
│                                                                 │
│                         🔒                                      │
│                                                                 │
│                    Admin Login                                  │
│                    관리자 로그인                                  │
│                                                                 │
│                                                                 │
│               ┌─────────────────────────┐                       │
│               │     ● ● ● ○            │  ← PIN dots           │
│               └─────────────────────────┘    (masked)           │
│                                                                 │
│           ┌───────┬───────┬───────┐                             │
│           │   1   │   2   │   3   │                             │
│           ├───────┼───────┼───────┤                             │
│           │   4   │   5   │   6   │  ← Numeric keypad          │
│           ├───────┼───────┼───────┤                             │
│           │   7   │   8   │   9   │                             │
│           ├───────┼───────┼───────┤                             │
│           │   ⌫   │   0   │   ✓   │  ← Clear, Zero, Submit     │
│           └───────┴───────┴───────┘                             │
│                                                                 │
│                                                                 │
│               [Cancel] / [취소]                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Error State

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  [←]                                                            │
│                                                                 │
│                         🔒                                      │
│                                                                 │
│                    Admin Login                                  │
│                    관리자 로그인                                  │
│                                                                 │
│            ┌─────────────────────────────────┐                  │
│            │  ❌ Invalid PIN / 잘못된 PIN    │ ← Error banner   │
│            │     3 attempts remaining        │   (shake anim)   │
│            └─────────────────────────────────┘                  │
│                                                                 │
│               ┌─────────────────────────┐                       │
│               │     ○ ○ ○ ○            │  ← Cleared            │
│               └─────────────────────────┘                       │
│                                                                 │
│                    (keypad)                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Lockout State

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  [←]                                                            │
│                                                                 │
│                         🔒                                      │
│                                                                 │
│                Too Many Attempts                                │
│                시도 횟수 초과                                     │
│                                                                 │
│                                                                 │
│              ┌─────────────────────────┐                        │
│              │                         │                        │
│              │        4:32             │  ← Countdown timer     │
│              │                         │                        │
│              └─────────────────────────┘                        │
│                                                                 │
│               Please wait before trying again                   │
│               잠시 후 다시 시도해주세요                           │
│                                                                 │
│                                                                 │
│               [Cancel] / [취소]                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technical Notes

### Frontend Auth Context

```typescript
// contexts/AuthContext.tsx

interface AuthState {
  isAuthenticated: boolean;
  token: string | null;
  expiresAt: Date | null;
}

interface AuthContextValue extends AuthState {
  login: (pin: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => boolean;
}

const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AuthState>(() => {
    // Initialize from localStorage
    const token = localStorage.getItem('admin_token');
    const expiresAt = localStorage.getItem('admin_token_expires');

    if (token && expiresAt) {
      const expiry = new Date(expiresAt);
      if (expiry > new Date()) {
        return { isAuthenticated: true, token, expiresAt: expiry };
      }
      // Expired, clean up
      localStorage.removeItem('admin_token');
      localStorage.removeItem('admin_token_expires');
    }

    return { isAuthenticated: false, token: null, expiresAt: null };
  });

  const login = async (pin: string) => {
    const response = await api.adminAuth(pin);

    if (!response.success) {
      throw new AuthError(response.error, response.remaining_attempts, response.lockout_until);
    }

    // Store token
    localStorage.setItem('admin_token', response.token);
    localStorage.setItem('admin_token_expires', response.expires_at);

    setState({
      isAuthenticated: true,
      token: response.token,
      expiresAt: new Date(response.expires_at),
    });
  };

  const logout = () => {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_token_expires');
    setState({ isAuthenticated: false, token: null, expiresAt: null });
  };

  const checkAuth = () => {
    if (!state.token || !state.expiresAt) return false;
    if (state.expiresAt <= new Date()) {
      logout();
      return false;
    }
    return true;
  };

  return (
    <AuthContext.Provider value={{ ...state, login, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
};
```

### Backend Auth Endpoint

```python
# adapters/api/routes/admin_routes.py

@router.post("/auth")
async def admin_auth(request: AdminAuthRequest) -> AdminAuthResponse:
    settings_repo = get_settings_repository()

    # Check lockout
    lockout_until = settings_repo.get("admin_lockout_until")
    if lockout_until and datetime.fromisoformat(lockout_until) > datetime.now():
        return AdminAuthResponse(
            success=False,
            error="Too many attempts",
            lockout_until=lockout_until,
        )

    # Validate PIN
    correct_pin = settings_repo.get("admin_pin", "1998")

    if request.pin != correct_pin:
        # Increment failed attempts
        failed = settings_repo.get_int("admin_failed_attempts", 0) + 1
        settings_repo.set("admin_failed_attempts", failed)

        if failed >= 5:
            # Set lockout
            lockout_until = (datetime.now() + timedelta(minutes=5)).isoformat()
            settings_repo.set("admin_lockout_until", lockout_until)
            return AdminAuthResponse(
                success=False,
                error="Too many attempts",
                lockout_until=lockout_until,
            )

        return AdminAuthResponse(
            success=False,
            error="Invalid PIN",
            remaining_attempts=5 - failed,
        )

    # Success - reset counters and generate token
    settings_repo.set("admin_failed_attempts", 0)
    settings_repo.set("admin_lockout_until", None)

    # Generate JWT
    expires_at = datetime.now() + timedelta(minutes=30)
    token = jwt.encode(
        {
            "sub": "admin",
            "exp": expires_at.timestamp(),
            "jti": str(uuid.uuid4()),
        },
        SECRET_KEY,
        algorithm="HS256",
    )

    logger.info("Admin login successful")

    return AdminAuthResponse(
        success=True,
        token=token,
        expires_at=expires_at.isoformat(),
    )
```

---

## Related Use Cases

- **UC-102**: View System Status (requires auth)
- **UC-104**: Update Settings (can change PIN)
- **UC-109**: Reboot System (requires auth)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
