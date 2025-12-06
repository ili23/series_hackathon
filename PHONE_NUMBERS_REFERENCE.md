# Phone Numbers Reference

This document lists all phone numbers used in the codebase that need to be **whitelisted/authorized** in the Series API team settings.

## Agent Phone Number (REQUIRED)

- **`+16463230991`** - System agent/bot number
  - **Location**: `backend/config.py` (SENDER_NUMBER)
  - **Usage**: Sends all automated messages and creates group chats
  - **Status**: ⚠️ **MUST BE WHITELISTED** - This is critical for the system to work

## Test/Seed Data Phone Numbers

These are used in seed data and may need to be whitelisted if you're testing with these numbers:

- **`+16469324962`** - Test user "Iram Liu"
  - **Location**: `backend/db/seed_data.py`
  - **Usage**: Sample user in database for testing
  
- **`+19172156679`** - Test user "Crystal Liang"
  - **Location**: `backend/db/seed_data.py`
  - **Usage**: Sample user in database for testing

## Dynamic User Phone Numbers

Any phone number that sends a voice message or receives a match will need to be whitelisted. The system will:
1. Normalize phone numbers to E.164 format (e.g., `9172156679` → `+19172156679`)
2. Include them in group chats when matches are made

## How to Whitelist Phone Numbers

1. Log into your Series API dashboard
2. Navigate to **Team Settings** → **Phone Numbers** or **Team Members**
3. Add each phone number that will be used in group chats
4. Ensure the agent number (`+16463230991`) is always whitelisted

## Troubleshooting 403 Errors

If you see a `403 Forbidden: phone number not allowed for this team` error:

1. Check the logs for the exact phone numbers being used
2. Verify each number is whitelisted in Series API
3. The logs will show which numbers were attempted:
   ```
   📋 PHONE NUMBERS ATTEMPTED IN GROUP CHAT:
      1. +19172156679 (Current sender)
      2. +16469324962 (Matched user)
      3. +16463230991 (AGENT - REQUIRED)
   ```

## Phone Number Format

All phone numbers are normalized to **E.164 format**:
- Must start with `+`
- Country code + number (e.g., `+1` for US/Canada)
- Example: `+19172156679` (not `9172156679` or `(917) 215-6679`)

