# JWT Secret Key Setup

## Current Status

The backend is using a default JWT secret key for development. This is fine for local development but **must be changed for production**.

## Setup

### Option 1: Add to `.env` file (Recommended)

1. Create or edit `backend/.env`:
```bash
cd backend
nano .env  # or use your preferred editor
```

2. Add this line (generate a new key):
```bash
JWT_SECRET_KEY=your_secure_random_key_here_min_32_chars
```

3. Generate a secure key:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Option 2: Set environment variable

```bash
export JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
```

## Production

In production, the backend will **raise an error** if `JWT_SECRET_KEY` is not set. This prevents accidentally using the default key.

## Development

In development, you'll see a one-time warning. This is normal and safe for local testing.

## Security Note

- Never commit `.env` files to git
- Use different keys for development and production
- Rotate keys if compromised
- Minimum 32 characters recommended
