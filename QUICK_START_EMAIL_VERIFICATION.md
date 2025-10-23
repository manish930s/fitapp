# Quick Start: Email Verification for Fitsani

## ⚡ Quick Setup (5 minutes)

### Step 1: Run Database Migration

Open Supabase SQL Editor and run:

```sql
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS verification_token TEXT,
ADD COLUMN IF NOT EXISTS token_created_at TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_users_verification_token ON users(verification_token);
```

### Step 2: Get Gmail App Password

1. Go to: https://myaccount.google.com/apppasswords
2. Select "Mail" → Generate
3. Copy the 16-character password (remove spaces!)

### Step 3: Update .env File

Edit `/app/backend/.env`:

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=abcdefghijklmnop
MAIL_FROM=your-email@gmail.com
```

### Step 4: Restart Backend

```bash
cd /app/backend
sudo supervisorctl restart backend
```

### Step 5: Test It!

Register a new user → Check email → Click verification link → Login ✅

## 🎯 What's New?

- ✉️ Users receive a beautiful verification email with your Fitsani logo
- 🔒 Users must verify email before they can login
- ⏰ Verification links expire in 24 hours
- 🔄 Users can resend verification email if needed
- 🎨 Beautiful success/failure pages

## 📧 Email Template Preview

Your users will receive an email with:
- Fitsani logo (green on dark background)
- Personalized greeting
- Big green "Verify Email Address" button
- 24-hour expiry notice
- List of Fitsani features
- Manual verification link (if button doesn't work)

## 🚀 Ready to Go!

See `/app/EMAIL_VERIFICATION_SETUP.md` for:
- Complete documentation
- API endpoint details
- Frontend integration guide
- Troubleshooting tips
- Production recommendations
