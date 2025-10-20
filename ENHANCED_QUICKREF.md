# ⚡ ENHANCED SYSTEM QUICK REFERENCE

## 🚀 Start Services (30 seconds)

```bash
# Terminal 1: HTTP Server (if not running)
cd /Users/jidai/news && python3 -m http.server 8000 &

# Terminal 2: Flask Backend
cd /Users/jidai/news && python3 subscription_service_enhanced.py
```

## 🧪 3-Command Test (1 minute)

```bash
# Test 1: Is service running?
curl http://localhost:5001/health

# Test 2: Get categories
curl http://localhost:5001/categories | python3 -m json.tool | head -20

# Test 3: Create subscription
curl -X POST http://localhost:5001/subscribe-enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "age_group": "middle",
    "interests": [1, 2],
    "frequency": "daily"
  }'
```

## 📱 Browser Test (1 minute)

1. Visit: **http://localhost:8000/main_articles_interface_v2.html**
2. Scroll to subscription form
3. Fill with:
   - Email: `browser@test.com`
   - Name: `Browser Test`
   - Age: Pick one
   - Interests: Check ≥1
   - Frequency: Pick one
4. Click **Subscribe**
5. Look for success message

## 📊 Check Database (1 minute)

```bash
# Show all subscriptions
sqlite3 /Users/jidai/news/subscriptions.db \
  "SELECT email, name, age_group, difficulty_level, frequency FROM subscriptions_enhanced;"

# Show categories
sqlite3 /Users/jidai/news/subscriptions.db \
  "SELECT id, name, emoji FROM categories;"

# Count entries
sqlite3 /Users/jidai/news/subscriptions.db \
  "SELECT COUNT(*) as total FROM subscriptions_enhanced;"
```

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Connection refused port 5001 | Start: `python3 subscription_service_enhanced.py` |
| Connection refused port 8000 | Start: `python3 -m http.server 8000` |
| 404 on /categories | Service not running, check Terminal 2 |
| Form won't load | Refresh browser, clear cache (Cmd+Shift+R) |
| "Categories not loading" alert | Check DevTools → Network → /categories request |

## 📋 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Check if running |
| GET | `/categories` | Get all categories |
| POST | `/subscribe-enhanced` | Create subscription |
| POST | `/generate-deepseek-summaries` | Make batch prompt |
| POST | `/store-summaries` | Save summaries to DB |

## 🎯 Age → Difficulty Mapping

| Age Group | Difficulty | Words | Questions |
|-----------|------------|-------|-----------|
| Elementary | easy | 100-200 | Simple |
| Middle | medium | 300-500 | Standard |
| High | hard | 500-700 | Analysis |

## 📝 Form Fields (Required)

1. **Email** - User email (required)
2. **Name** - Full name (required)
3. **Age Group** - Dropdown (required)
   - Elementary (Grades 3-5)
   - Middle School (Grades 6-8)
   - High School (Grades 9-12)
4. **Interests** - Checkboxes (≥1 required)
   - 🌍 World
   - 🔬 Science
   - 💻 Technology
   - 🏊 Sports
   - 🎨 Life
   - 💰 Economy
5. **Frequency** - Radio buttons (required)
   - Daily
   - Weekly

## ✅ Success Indicators

- ✅ `/health` returns `{"status": "ok"}`
- ✅ `/categories` returns array of 6 objects
- ✅ `/subscribe-enhanced` returns success message
- ✅ Database row appears in `subscriptions_enhanced`
- ✅ `difficulty_level` matches age group:
  - elementary → easy
  - middle → medium
  - high → hard
- ✅ Form submits without error
- ✅ Interests stored as JSON array

## 🗂 Files Involved

| File | Purpose | Location |
|------|---------|----------|
| `main_articles_interface_v2.html` | Main page with form | Root |
| `subscription_service_enhanced.py` | Flask backend | Root |
| `subscriptions.db` | SQLite database | Root |
| `articles_data_with_summaries.json` | Test data | Root |

## 🔍 Expected Output Examples

### Health Check
```json
{"status": "ok"}
```

### Categories Response
```json
[
  {"id": 1, "name": "World", "emoji": "🌍", ...},
  {"id": 2, "name": "Science", "emoji": "🔬", ...},
  ...
]
```

### Subscription Success
```json
{
  "message": "Subscription created successfully",
  "difficulty_level": "medium"
}
```

### Database Entry
```
test@example.com | Test User | middle | medium | [1,2] | daily | active
```

## 🚨 Quick Kill Switch

```bash
# Stop all services
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9
lsof -i :5001 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

## 📚 Full Documentation

- **ENHANCED_SYSTEM.md** - Complete system guide
- **ENHANCED_TESTING_GUIDE.md** - Detailed test procedures
- **ENHANCED_STATUS.md** - Full implementation status

---

**Status**: ✅ Ready for Testing  
**Last Updated**: Current Session  
**Next Step**: Run the 3-Command Test above
