# User Registration Feature Added! 🎉

## What's New

Your Chemical Equipment Visualizer now supports **user registration** directly from the React frontend!

## Features

✅ **Register New Users** - Create accounts without Django admin
✅ **Email Field** - Optional email during registration
✅ **Password Validation** - Minimum 6 characters required
✅ **Username Validation** - Checks for duplicate usernames
✅ **Toggle UI** - Easy switch between login and registration
✅ **Success Messages** - Clear feedback for users

## How It Works

### Backend (Django)
- **New Endpoint**: `POST /api/register/`
- **Validation**: Username uniqueness, password length
- **Security**: Uses Django's built-in `create_user()` method

### Frontend (React)
- **Toggle Button**: Switch between "Sign in" and "Create Account"
- **Form Fields**: Username, Email (optional), Password
- **Auto-redirect**: After successful registration, switches to login

## Usage

### For Users:
1. Open the React app: http://localhost:5173
2. Click "Don't have an account? Register"
3. Fill in:
   - Username (required)
   - Email (optional)
   - Password (min 6 characters)
4. Click "Create Account"
5. After success, click "Already have an account? Sign in"
6. Login with your new credentials

### API Testing:
```bash
# Register a new user
curl -X POST http://127.0.0.1:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "newuser", "password": "password123", "email": "user@example.com"}'

# Response:
{
  "message": "User registered successfully",
  "username": "newuser"
}
```

## Validation Rules

| Field | Rule |
|-------|------|
| Username | Required, must be unique |
| Password | Required, minimum 6 characters |
| Email | Optional |

## Error Messages

- "Username and password are required"
- "Password must be at least 6 characters long"
- "Username already exists"
- "Registration failed: [error details]"

## Files Modified

### Backend:
- `data_api/views.py` - Added `RegisterView` class
- `data_api/urls.py` - Added `/api/register/` endpoint

### Frontend:
- `chemical-viz-frontend/src/App.jsx` - Added registration form and logic
- `chemical-viz-frontend/src/App.css` - Added toggle button styles

## Security Notes

✅ Passwords are hashed using Django's built-in authentication
✅ No authentication required for registration endpoint
✅ Username uniqueness enforced at database level
✅ Input validation on both frontend and backend

## Testing

1. **Start Django server**:
   ```bash
   python manage.py runserver
   ```

2. **Start React app**:
   ```bash
   cd chemical-viz-frontend
   npm run dev
   ```

3. **Test Registration**:
   - Navigate to http://localhost:5173
   - Click "Don't have an account? Register"
   - Create a new account
   - Login with new credentials

## Next Steps

You can now:
- ✅ Register users without Django admin access
- ✅ Allow self-service account creation
- ✅ Deploy with public registration enabled

---

**Ready to use! No additional setup required.** 🚀
