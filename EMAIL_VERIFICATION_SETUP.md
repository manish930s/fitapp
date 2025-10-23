# Email Verification Setup Guide for Fitsani

## Overview
This guide will help you set up email verification for user signups in your Fitsani fitness application. Email verification ensures that users have access to their email accounts and helps prevent spam registrations.

## Features Implemented
✅ Email verification on user registration
✅ Beautifully designed HTML email templates with Fitsani branding
✅ Embedded logo in verification emails
✅ 24-hour verification link expiry for security
✅ Resend verification email functionality
✅ Verification success/failure pages
✅ Login blocked until email is verified

## Prerequisites
- A Gmail account (or any SMTP email service)
- 2-factor authentication enabled on Gmail
- Access to Supabase dashboard

## Step 1: Database Migration

Run the following SQL in your Supabase SQL Editor (Dashboard → SQL Editor):

```sql
-- Add email verification columns to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS verification_token TEXT,
ADD COLUMN IF NOT EXISTS token_created_at TIMESTAMP;

-- Create index for verification token lookups
CREATE INDEX IF NOT EXISTS idx_users_verification_token ON users(verification_token);
```

## Step 2: Gmail SMTP Setup (Free Option)

### Enable Gmail App Passwords

1. **Enable 2-Factor Authentication**
   - Go to https://myaccount.google.com/
   - Click "Security" → "2-Step Verification"
   - Follow the setup process

2. **Generate App Password**
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" as the app
   - Select your device type
   - Click "Generate"
   - Copy the 16-character password (it will look like: `abcd efgh ijkl mnop`)

### Configure Environment Variables

Edit `/app/backend/.env` and update these values:

```env
# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com          # Your actual Gmail address
MAIL_PASSWORD=abcdefghijklmnop              # The 16-character app password (remove spaces)
MAIL_FROM=your-email@gmail.com              # Same as MAIL_USERNAME
```

**Important**: Remove all spaces from the app password!

## Step 3: Alternative Email Providers

### Option 1: Zoho Mail (Recommended for Production - Free Forever)

```env
MAIL_SERVER=smtppro.zoho.in
MAIL_PORT=465
MAIL_USERNAME=your-email@zoho.com
MAIL_PASSWORD=your-app-specific-password
MAIL_FROM=your-email@zoho.com
```

Zoho offers:
- Unlimited emails per day
- Professional email addresses
- Better deliverability than Gmail
- Explicit support for transactional emails

### Option 2: Outlook/Hotmail

```env
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USERNAME=your-email@outlook.com
MAIL_PASSWORD=your-password
MAIL_FROM=your-email@outlook.com
```

## Step 4: Restart the Backend

After configuring the email settings, restart your backend server:

```bash
cd /app/backend
sudo supervisorctl restart backend
```

## Testing the Email Verification Flow

### 1. Register a New User

```bash
curl -X POST http://localhost:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "SecurePass123!",
    "age": 25,
    "gender": "male",
    "height": 175,
    "weight": 70,
    "activity_level": "moderate"
  }'
```

Expected Response:
```json
{
  "message": "Registration successful! Please check your email to verify your account.",
  "email": "test@example.com",
  "requires_verification": true,
  "user_id": "uuid-here"
}
```

### 2. Check Email

The user should receive an email like this:

**Subject**: Verify Your Fitsani Email Address

**Content**: 
- Fitsani logo
- Personalized greeting
- "Verify Email Address" button
- 24-hour expiry notice
- List of features
- Manual verification link

### 3. Click Verification Link

When the user clicks the verification link, they'll see:
- Success page with animated checkmark
- Welcome message with feature list
- "Login to Your Account" button
- Auto-redirect after 5 seconds

### 4. Try to Login Before Verification

```bash
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'
```

Expected Response (Before Verification):
```json
{
  "detail": "Please verify your email before logging in. Check your inbox for the verification link."
}
```

### 5. Login After Verification

After email verification, login will work normally and return a JWT token.

### 6. Resend Verification Email

If user didn't receive the email:

```bash
curl -X POST http://localhost:8001/api/auth/resend-verification \
  -H "Content-Type: application/json" \
  -d '"test@example.com"'
```

## API Endpoints

### POST /api/auth/register
Register a new user and send verification email.

**Request Body**:
```json
{
  "name": "string",
  "email": "string",
  "password": "string",
  "age": number (optional),
  "gender": "string" (optional),
  "height": number (optional),
  "weight": number (optional),
  "activity_level": "string" (optional),
  "goal_weight": number (optional)
}
```

**Response**: 
```json
{
  "message": "Registration successful! Please check your email to verify your account.",
  "email": "string",
  "requires_verification": true,
  "user_id": "string"
}
```

### GET /api/auth/verify-email?token={token}
Verify user's email address. Returns HTML page.

**Query Parameters**:
- `token`: Verification token from email link

**Response**: HTML page (success/failure/expired)

### POST /api/auth/resend-verification
Resend verification email.

**Request Body**: 
```json
"user@example.com"
```

**Response**:
```json
{
  "message": "Verification email has been resent. Please check your inbox.",
  "email": "string"
}
```

### POST /api/auth/login
Login user (requires verified email).

**Request Body**:
```json
{
  "email": "string",
  "password": "string"
}
```

**Response** (if not verified):
```json
{
  "detail": "Please verify your email before logging in. Check your inbox for the verification link."
}
```

**Response** (if verified):
```json
{
  "message": "Login successful",
  "token": "jwt-token",
  "user": {
    "user_id": "string",
    "name": "string",
    "email": "string"
  }
}
```

## Frontend Integration

### 1. Update Signup Flow

After successful registration, show this message:

```javascript
// After calling /api/auth/register
if (response.requires_verification) {
  showMessage("✅ Registration successful! Please check your email to verify your account.");
  showMessage(`We've sent a verification link to ${response.email}`);
}
```

### 2. Handle Login Errors

```javascript
// Handle 403 error on login
try {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  
  if (response.status === 403) {
    const error = await response.json();
    showError(error.detail); // "Please verify your email..."
    showResendButton(email); // Show "Resend Verification Email" button
  }
} catch (error) {
  // Handle other errors
}
```

### 3. Resend Verification Button

```javascript
async function resendVerification(email) {
  const response = await fetch('/api/auth/resend-verification', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(email)
  });
  
  if (response.ok) {
    showSuccess("Verification email resent! Check your inbox.");
  }
}
```

## Security Features

✅ **Time-Limited Tokens**: Verification links expire after 24 hours
✅ **Single-Use Tokens**: Tokens are cleared after successful verification
✅ **Secure Token Generation**: Uses itsdangerous library with cryptographic signatures
✅ **No Password in Email**: Emails never contain passwords
✅ **Login Protection**: Users can't login without verification
✅ **HTTPS Recommended**: Use HTTPS in production for secure token transmission

## Troubleshooting

### Email Not Sending

**Problem**: User registers but doesn't receive email.

**Solutions**:

1. **Check SMTP Credentials**:
   ```bash
   cd /app/backend
   python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Username:', os.getenv('MAIL_USERNAME')); print('Password length:', len(os.getenv('MAIL_PASSWORD', '')))"
   ```

2. **Check Backend Logs**:
   ```bash
   tail -f /var/log/supervisor/backend.*.log | grep -i "email\|mail"
   ```

3. **Test SMTP Connection**:
   ```python
   import smtplib
   server = smtplib.SMTP('smtp.gmail.com', 587)
   server.starttls()
   server.login('your-email@gmail.com', 'your-app-password')
   print("✅ SMTP connection successful!")
   server.quit()
   ```

4. **Common Issues**:
   - App password has spaces (remove them)
   - 2FA not enabled on Gmail
   - Wrong SMTP server/port
   - Firewall blocking port 587

### Email Goes to Spam

**Solutions**:
1. Use a professional email domain (not Gmail)
2. Set up SPF and DKIM records for your domain
3. Use Zoho Mail instead of Gmail
4. Ask users to check spam folder

### Verification Link Expired

**Solution**: User can request a new link using the "Resend Verification Email" button.

### Database Migration Failed

**Solution**: Run the SQL manually in Supabase SQL Editor (see Step 1).

## Production Recommendations

1. **Use Professional Email Service**:
   - Zoho Mail (free, unlimited)
   - SendGrid (free tier: 100 emails/day)
   - Mailgun (free tier: 5,000 emails/month)

2. **Add Rate Limiting**:
   - Limit verification email resends (max 3 per hour)
   - Prevent email enumeration attacks

3. **Monitor Email Delivery**:
   - Track email send success/failure rates
   - Log failed email attempts
   - Set up alerts for delivery issues

4. **Use Environment-Specific URLs**:
   - Development: `http://localhost:3000`
   - Staging: `https://staging.fitsani.com`
   - Production: `https://fitsani.com`

5. **Add Email Templates**:
   - Welcome email after verification
   - Password reset email
   - Account activity notifications

## Files Created/Modified

### New Files:
- `/app/backend/email_service.py` - Email sending service
- `/app/backend/utils.py` - Token generation/verification utilities
- `/app/backend/templates/verification_email.html` - Email template
- `/app/backend/static/logo.png` - Fitsani logo
- `/app/backend/add_email_verification.sql` - Database migration
- `/app/EMAIL_VERIFICATION_SETUP.md` - This guide

### Modified Files:
- `/app/backend/server.py` - Added email verification endpoints
- `/app/backend/.env` - Added email configuration
- `/app/backend/requirements.txt` - Added email dependencies

## Next Steps

1. Run the database migration (Step 1)
2. Configure email SMTP settings (Step 2)
3. Restart backend server (Step 4)
4. Test the flow (Step 5)
5. Update frontend to handle verification flow

## Support

If you encounter any issues:
1. Check the logs: `tail -f /var/log/supervisor/backend.*.log`
2. Verify .env configuration
3. Test SMTP connection
4. Check Supabase database structure

---

**Created**: October 2024
**Version**: 1.0
**App**: Fitsani - AI-Powered Fitness Application
