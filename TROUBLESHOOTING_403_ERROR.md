# Troubleshooting: 403 Forbidden - Phone Number Not Allowed

## Error Message
```
❌ FAILED TO CREATE GROUP CHAT via iMessage API:
   Status: 403
   Response: forbidden: phone number not allowed for this team
```

## What This Means

The Series API requires all phone numbers to be **whitelisted/registered** for your team before they can be used in group chats. The 403 error indicates that one or more of the phone numbers in the group chat are not authorized.

## Participants in Group Chat

When creating a group chat, the system includes:
1. **Current sender** (user who said "yes") - e.g., `+19172156679`
2. **Matched user** (from database) - e.g., `+16469324962`
3. **AI Agent** - `+16463230991`

## How to Fix

### Option 1: Whitelist Phone Numbers in Series API

1. Log into your Series API dashboard/team settings
2. Navigate to "Phone Numbers" or "Team Members" section
3. Add/whitelist the following phone numbers:
   - `+16463230991` (Agent number - MUST be whitelisted)
   - `+19172156679` (Your user number)
   - `+16469324962` (Matched user number)
   - Any other phone numbers that users might have

### Option 2: Check Team Configuration

1. Verify your API key has permissions to create group chats
2. Check if there are any restrictions on group chat creation
3. Ensure the team has group chat functionality enabled

### Option 3: Test Individual Phone Numbers

You can test which phone number is causing the issue by:
1. Trying to create a 1-on-1 chat with each number
2. If a 1-on-1 chat works, that number is whitelisted
3. If it fails with 403, that number needs to be whitelisted

## Current Implementation

The code already:
- ✅ Normalizes all phone numbers to E.164 format
- ✅ Removes duplicates
- ✅ Includes all three participants (sender, matched user, agent)
- ✅ Uses correct API endpoint: `https://series-hackathon-service-202642739529.us-east1.run.app/api/chats`
- ✅ Logs detailed error information

## Next Steps

1. **Whitelist the agent number** (`+16463230991`) - This is critical as it's the sender
2. **Whitelist user phone numbers** - Any phone numbers that users might have
3. **Test with whitelisted numbers** - Once numbers are whitelisted, group chat creation should work

## Error Handling

The system now provides:
- Detailed logging of which phone numbers are being used
- Clear error messages identifying the issue
- User-friendly error message sent to the user

