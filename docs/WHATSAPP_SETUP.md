# WhatsApp Business API Setup Guide

## Overview
SMARTII can send WhatsApp messages in two ways:

1. **Desktop Mode (No Setup)** - Opens WhatsApp Desktop with pre-filled message
2. **API Mode (Requires Setup)** - Sends messages programmatically via Meta API

---

## Method 1: Desktop Mode (Quick Start)

**Already working!** Just say:
- "Send WhatsApp to +911234567890 saying hello"
- "Open WhatsApp chat with +911234567890"

### How it works:
- Opens WhatsApp Desktop or web.whatsapp.com
- Pre-fills the message
- User clicks send

### Limitations:
- Requires user to click send
- WhatsApp Desktop must be installed
- Not fully automated

---

## Method 2: API Mode (Full Automation)

Send messages completely automatically - no clicks required!

### Step-by-Step Setup

#### 1. Create Meta Business Account
1. Go to https://business.facebook.com
2. Click "Create Account"
3. Fill in business details
4. Verify email

#### 2. Create Developer App
1. Go to https://developers.facebook.com/apps
2. Click "Create App"
3. Select "Business" as app type
4. Name: "SMARTII WhatsApp Bot"
5. Contact email: your email
6. Click "Create App"

#### 3. Add WhatsApp Product
1. In your new app, find "Add Products"
2. Find "WhatsApp" and click "Set Up"
3. You'll see the WhatsApp setup dashboard

#### 4. Get Credentials

**Phone Number ID:**
1. In WhatsApp dashboard, go to "API Setup"
2. Copy the "Phone number ID" (looks like: `123456789012345`)

**Access Token:**
1. In same "API Setup" page
2. Click "Generate Token" under "Temporary access token"
3. Copy the token (starts with `EAAG...`)
4. **IMPORTANT:** This token expires in 24 hours
5. For permanent token, follow "Get Permanent Token" section below

#### 5. Configure SMARTII Backend

**On Windows (PowerShell):**
```powershell
# Set environment variables
$env:WHATSAPP_API_KEY = "EAAG...your_access_token"
$env:WHATSAPP_PHONE_ID = "123456789012345"

# Restart backend
cd C:\Users\lenovo\Desktop\smartii\backend
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

**Make Variables Permanent (Windows):**
```powershell
# Add to user environment variables (persists across reboots)
[System.Environment]::SetEnvironmentVariable("WHATSAPP_API_KEY", "EAAG...your_token", "User")
[System.Environment]::SetEnvironmentVariable("WHATSAPP_PHONE_ID", "123456789012345", "User")
```

#### 6. Test It!

Say to SMARTII:
- "Send WhatsApp to +911234567890 saying test message"

You should see: "WhatsApp message sent to +911234567890!" ✅

---

## Get Permanent Access Token

Temporary tokens expire in 24 hours. Get a permanent one:

### Method 1: System User (Recommended)

1. Go to Meta Business Suite: https://business.facebook.com
2. Click "Settings" → "Business Settings"
3. Under "Users" → click "System Users"
4. Click "Add" to create new system user
5. Name: "SMARTII WhatsApp Bot"
6. Role: Admin
7. Click "Add Assets" → select your WhatsApp app
8. Check "Manage WhatsApp Business Account" permission
9. Click "Generate New Token"
10. Select your app
11. Check required permissions:
    - `whatsapp_business_messaging`
    - `whatsapp_business_management`
12. Copy the token (never expires!)

### Method 2: Access Token Tool

1. Go to https://developers.facebook.com/tools/accesstoken/
2. Find your app in the list
3. Click "Generate Access Token"
4. Select required permissions
5. Copy token

---

## Verify Setup

### Test via API directly:

```powershell
# PowerShell test
$headers = @{
    "Authorization" = "Bearer YOUR_ACCESS_TOKEN"
    "Content-Type" = "application/json"
}

$body = @{
    messaging_product = "whatsapp"
    to = "911234567890"
    type = "text"
    text = @{
        body = "Test from SMARTII!"
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://graph.facebook.com/v18.0/YOUR_PHONE_ID/messages" -Method Post -Headers $headers -Body $body
```

### Expected Response:
```json
{
  "messaging_product": "whatsapp",
  "contacts": [{"input": "911234567890", "wa_id": "911234567890"}],
  "messages": [{"id": "wamid.XXX..."}]
}
```

---

## Pricing

**Free Tier:**
- First 1,000 conversations per month: **FREE**
- Conversation = 24-hour window with a user

**Paid (after 1,000):**
- Varies by country
- India: ~₹0.40 per conversation
- USA: ~$0.005 per conversation

**Business-initiated messages:**
- Require approved message templates
- User-initiated messages (replies) are free within 24h window

---

## Adding Test Numbers

During development, you can only send to verified test numbers:

1. In WhatsApp API Setup page
2. Find "To" field
3. Click "Manage phone number list"
4. Add phone numbers with country code
5. Each number gets a 6-digit verification code via WhatsApp
6. Enter code to verify

**For production:** Submit app for business verification (takes 3-5 days)

---

## Current Status in SMARTII

✅ Desktop mode - fully working
✅ API integration - code complete
⏳ API credentials - you need to set up
⏳ Production verification - optional

### What's Already Implemented:

**backend/integrations/whatsapp_api.py:**
- `send_message()` - send text messages
- `send_media()` - send images/videos
- Automatic fallback to desktop mode if API not configured

**backend/tools.py:**
- `whatsapp_send()` - tries API first, falls back to desktop

**Voice Commands:**
- "Send WhatsApp to +911234567890 saying hello"
- "Message +911234567890 on WhatsApp"

---

## Troubleshooting

### "WhatsApp API not configured"
- Check environment variables are set:
  ```powershell
  echo $env:WHATSAPP_API_KEY
  echo $env:WHATSAPP_PHONE_ID
  ```
- Restart backend after setting variables

### "Access token expired"
- Temporary tokens expire in 24h
- Get permanent token using System User method

### "Recipient phone number not registered"
- Add number to test numbers in API Setup
- Verify with 6-digit code

### "Invalid phone number format"
- Use format: `911234567890` (country code + number, no spaces/+)
- Remove leading zeros after country code

### "Message not delivered"
- Check recipient has WhatsApp installed
- Verify phone number is active
- Check message templates (if business-initiated)

---

## Security Notes

⚠️ **Keep tokens secure:**
- Never commit tokens to GitHub
- Use environment variables only
- Rotate tokens if exposed

⚠️ **Rate limits:**
- 80 messages per second
- 1,000 messages per day (free tier)

⚠️ **Compliance:**
- Only message users who opted in
- Follow WhatsApp Commerce Policy
- Don't spam or send unsolicited messages

---

## Next Steps

1. ✅ Test desktop mode (already working)
2. 🔧 Set up Meta Business Account
3. 🔧 Get API credentials
4. 🔧 Configure environment variables
5. ✅ Test API mode with verified numbers
6. 📱 (Optional) Build Android app for full integration

---

## Resources

- **WhatsApp Cloud API Docs:** https://developers.facebook.com/docs/whatsapp/cloud-api
- **Getting Started:** https://developers.facebook.com/docs/whatsapp/cloud-api/get-started
- **Meta Business Suite:** https://business.facebook.com
- **Developer Console:** https://developers.facebook.com/apps
- **Pricing:** https://developers.facebook.com/docs/whatsapp/pricing

---

## Support

If you encounter issues:
1. Check troubleshooting section above
2. Verify credentials in Meta developer console
3. Test with curl/PowerShell directly
4. Check backend logs: `backend/app.log`

Desktop mode is always available as fallback! 🎯
