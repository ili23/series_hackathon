# Language Matching Workflow

## Overview

This system implements an automated language matching workflow that:
1. Detects new languages from voice messages
2. Asks users if they want to add the language to their profile
3. Asks if they want to be matched with other speakers
4. Shows matching user profiles
5. Creates group chats when users agree

## Workflow Steps

### Step 1: New Language Detected
When a user sends a voice message in a language they haven't used before:

```
User: [Sends voice message in Spanish]
Agent: "I noticed this is a new language for you. Do you want me to add this language proficiency to our table for future matching?"
```

### Step 2: Add Language Response
If user says "Yes":
- Language is added to database
- System asks about matching

If user says "No":
- Conversation ends

### Step 3: Matching Preference
```
Agent: "Do you want to be matched with people who know this language?"
```

If user says "Yes":
- Matching preference is saved
- System searches for matching users

If user says "No":
- Conversation ends

### Step 4: Finding Matches
If matching users are found:
- System shows first matching user's profile
- Asks if they want to create a group chat

If no matching users:
```
Agent: "Unfortunately, there are no other users who know this language currently."
```

### Step 5: Group Chat Decision
```
Agent: "Would you like a group chat created with this user?"
```

If user says "Yes":
- Group chat is created via Series API
- Both users are added to the chat

If user says "No":
- System asks if they want another match

### Step 6: Another Match (Optional)
```
Agent: "Would you like me to match you with another user who knows this language?"
```

If user says "Yes":
- System shows another matching user
- Process repeats from Step 5

If user says "No":
- Conversation ends

## Database Tables

### Languages
Stores user language profiles:
- `phone_number`: User's phone number
- `language_name`: Language name
- `created_at`: Timestamp

### UserProfiles
Stores user information:
- `phone_number`: User's phone number (unique)
- `bio`: User bio text
- `display_name`: Display name
- `created_at`, `updated_at`: Timestamps

### ConversationStates
Tracks active conversations:
- `phone_number`: User's phone number
- `state`: Current conversation state
- `language_name`: Language being discussed
- `matched_user_phone`: Currently shown matched user
- `created_at`, `updated_at`: Timestamps

### MatchingPreferences
Stores matching preferences:
- `phone_number`: User's phone number
- `language_name`: Language
- `wants_matching`: 'yes' or 'no'
- `created_at`: Timestamp

## Conversation States

- `asking_add_language`: Waiting for user to confirm adding language
- `asking_matching`: Waiting for user to confirm matching preference
- `showing_profile`: Showing a matched user profile, waiting for group chat decision
- `asking_another_match`: Waiting for user to confirm if they want another match

## API Integration

The system uses the Series API to:
- Send messages to users (`POST /api/chats` or `POST /api/chats/{id}/chat_messages`)
- Create group chats (`POST /api/chats` with multiple phone numbers)

## Example Flow

### User 1 (First User)
1. Sends voice message in Spanish
2. System detects new language
3. User confirms adding language
4. User confirms wanting matching
5. No other users found → "Unfortunately, there are no other users..."

### User 2 (Second User)
1. Sends voice message in Spanish
2. System detects new language
3. User confirms adding language
4. User confirms wanting matching
5. System finds User 1
6. Shows User 1's profile
7. User confirms group chat
8. Group chat created with both users

## Testing

To test the workflow:
1. Send a voice message in a new language
2. Respond "Yes" to add language
3. Respond "Yes" to matching
4. Review matched user profile
5. Respond "Yes" to create group chat

## Notes

- The system automatically creates user profiles if they don't exist
- Matching is based on language name (case-sensitive)
- Users can request multiple matches for the same language
- Group chats are created with a display name: "{Language} Language Exchange"

