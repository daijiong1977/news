# Device ID Implementation Summary

**Date:** October 26, 2025  
**Purpose:** Add device_id for offline resilience and anonymous user tracking

---

## Changes Made

### 1. Database Schema

**File:** `dbinit/migration_add_device_id.sql` (NEW)
- Added `device_id TEXT UNIQUE` column to `user_subscriptions` table
- Created index `idx_user_subscriptions_device_id` for fast lookups

**File:** `dbinit/init_schema.md` (UPDATED)
- Updated `user_subscriptions` table documentation
- Added explanation of device_id purpose and benefits

### 2. Backend API

**File:** `serverapi/user_api.py` (UPDATED)

**New Endpoint:**
```python
GET /api/device/generate
```
- Generates unique 20-character device_id
- Format: `news-{uuid}` (e.g., `news-a1b2c3d4e5f6g7h8i9j0`)
- Works for anonymous users (no auth required)
- Returns: `{"success": true, "device_id": "news-..."}`

**Updated Endpoint:**
```python
POST /api/user/register
```
- Now stores device_id in database
- device_id sent to emailapi.6ray.com/client/bootstrap
- Fixed emailapi integration (was sending wrong fields)

**Changes:**
1. Generate device_id using `news-{uuid.uuid4().hex[:20]}`
2. Send `email` and `device_id` to emailapi (not `display_name`)
3. Store device_id in user_subscriptions table
4. Better error logging for emailapi calls

### 3. Frontend

**File:** `user_manager/user_manager.js` (UPDATED)

**New Features:**
1. Auto-generate device_id on first page load
2. Store in localStorage as `news_device_id`
3. Call `/api/device/generate` if not exists
4. Fallback to local generation if API unavailable

**New Method:**
```javascript
async ensureDeviceId() {
    // Get from localStorage or generate via API
    // Fallback: news-local-{timestamp}-{random}
}
```

**Flow:**
```
Page Load
  ↓
Check localStorage for device_id
  ↓
Not found? → Call /api/device/generate
  ↓
Store in localStorage
  ↓
Use for all tracking (anonymous + registered)
```

### 4. Documentation

**File:** `serverapi/README.md` (UPDATED)
- Added `/api/device/generate` to endpoint list
- Added usage documentation and examples
- Explained anonymous user tracking benefits

---

## Benefits

### 1. Offline Resilience
- If emailapi.6ray.com is down, we can still:
  - Generate tokens using device_id
  - Track user activity
  - Regenerate credentials

### 2. Anonymous Tracking
- Works without user registration
- Persistent identity across sessions
- Privacy-friendly (no email required)

### 3. Multi-Device Support (Future)
- One user → multiple device_ids
- Track activity per device
- Sync across devices

### 4. Stable Identity
- device_id doesn't change even if email changes
- Independent of emailapi availability
- Permanent user identifier

---

## EmailAPI Integration Fixed

### Old (WRONG):
```python
{
    'device_id': f"news-user-{email}",  # Not unique enough
    'display_name': name                 # Wrong field!
}
```

### New (CORRECT):
```python
{
    'email': email,                      # Required by emailapi
    'device_id': f"news-{uuid[:20]}"    # 16+ chars, unique
}
```

### EmailAPI Response:
```json
{
    "device_id": "news-a1b2c3d4e5f6g7h8",
    "api_key": "91107e29a4c289a4.4c895d93ba8e8687...",
    "username": "ios-newsa1b2c3"
}
```

---

## Migration Steps

### Local Database:
```bash
cd /Users/jidai/news
sqlite3 articles.db < dbinit/migration_add_device_id.sql
```

### Production Database:
```bash
ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227
cd /var/www/news
sqlite3 articles.db < dbinit/migration_add_device_id.sql
```

---

## Testing

### Test Device ID Generation:
```bash
curl https://news.6ray.com/api/device/generate
```

Expected:
```json
{
  "success": true,
  "device_id": "news-a1b2c3d4e5f6g7h8i9j0"
}
```

### Test Registration with device_id:
```bash
curl -X POST https://news.6ray.com/api/user/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "reading_style": "enjoy"
  }'
```

Backend will:
1. Generate device_id internally
2. Call emailapi with email + device_id
3. Get bootstrap token (api_key)
4. Store device_id + token in database
5. Send verification email

---

## Next Steps

1. ✅ Created migration SQL
2. ✅ Updated init_schema.md
3. ✅ Added API endpoint
4. ✅ Fixed emailapi integration
5. ✅ Updated frontend
6. ✅ Updated documentation
7. ⏳ Run migration on local DB
8. ⏳ Test locally
9. ⏳ Commit and push
10. ⏳ Deploy to production
11. ⏳ Run migration on production DB
12. ⏳ Test on production

---

## Files Modified

- `dbinit/migration_add_device_id.sql` - NEW
- `dbinit/init_schema.md` - UPDATED
- `serverapi/user_api.py` - UPDATED
- `user_manager/user_manager.js` - UPDATED
- `serverapi/README.md` - UPDATED

---

*Generated: October 26, 2025*
