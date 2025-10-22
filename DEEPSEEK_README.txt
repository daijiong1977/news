╔════════════════════════════════════════════════════════════════════════════╗
║           DeepSeek Article Processing System - README                      ║
║                                                                            ║
║  Complete AI-powered analysis for news articles using DeepSeek API        ║
╚════════════════════════════════════════════════════════════════════════════╝

📋 WHAT THIS SYSTEM DOES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For each article, generates 6 comprehensive analyses:

  1. English Summary (300-500 words)
  2. Chinese Summary (300-500 words)  
  3. Key Words Analysis (10 terms with explanations)
  4. Background Reading (200-300 words of context)
  5. Study Questions (5 multiple choice questions)
  6. Discussion (Both perspectives + synthesis)


🚀 QUICK START (3 COMMANDS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Install dependency:
   $ pip install requests

2. Initialize database:
   $ python3 deepseek_processor.py --init

3. Process articles:
   $ python3 deepseek_processor.py --batch-size 5

Done! Results will be stored in the database.


📊 HOW IT WORKS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INPUT:  Your articles (full content from content files)
        ↓
PROCESS: Batch up to 5 articles → Send to DeepSeek API
        ↓
OUTPUT: JSON with 6 analytical components
        ↓
STORE:  (DEPRECATED) Previously saved to `deepseek_feedback` table. Runtime now writes to normalized tables (`article_summaries`, `keywords`, `questions`, `choices`, `background_read`, `article_analysis`). Use migration helpers if you have legacy `deepseek_feedback` data.
        ↓
QUERY:  Retrieve results anytime


📁 FILES PROVIDED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Main:
  • deepseek_processor.py         (330 lines, production-ready)

Documentation:
  • DEEPSEEK_QUICKSTART.md        (5-minute setup guide)
  • DEEPSEEK_SETUP.md             (Detailed guide + troubleshooting)
  • DEEPSEEK_PROMPT_TEMPLATE.md   (Exact prompt sent to DeepSeek)
  • DEEPSEEK_COMPLETE.md          (Full reference manual)
  • IMPLEMENTATION_SUMMARY.md     (Overview of system)
  • DEEPSEEK_README.txt           (This file)


💾 DATABASE TABLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Modified:
  • articles.deepseek_processed    (new column: 0=not done, 1=done)

New:
  • deepseek_feedback              (table: stores all 6 analyses)
    - article_id
    - summary_en, summary_zh
    - key_words
    - background_reading
    - multiple_choice_questions
    - discussion_both_sides
    - created_at, updated_at


🔄 USAGE EXAMPLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Process articles:
  $ python3 deepseek_processor.py --batch-size 5

Process only 2 batches (10 articles):
  $ python3 deepseek_processor.py --batch-size 5 --max-batches 2

Get analysis for article 16:
  $ python3 deepseek_processor.py --query 16

Check progress:
  $ sqlite3 articles.db "SELECT COUNT(*) FROM articles WHERE deepseek_processed=1;"


✨ KEY FEATURES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Batch processing (5 articles per API call)
✓ Automatic tracking (knows which articles are done)
✓ Bilingual (English + Chinese)
✓ Educational (questions, background, keywords)
✓ Balanced analysis (multiple perspectives)
✓ Quality control (response files saved)
✓ Flexible querying (individual or batch results)
✓ Rate limiting (3 second delays between batches)
✓ Error handling (graceful recovery)
✓ Well documented (4 complete guides)


🔐 YOUR API KEY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

API Key: sk-0ad0e8ca48544dd79ef790d17672eed2

Location in code: deepseek_processor.py (line 12)

Security: Keep this file private. Don't commit to public repos.


📈 COST & TIMING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Per batch (5 articles):
  • API processing: 2-5 seconds
  • Input size: ~45-50 KB
  • Output tokens: ~8000
  • Estimated cost: $0.01-0.02

Total for 20 articles (4 batches):
  • Time: ~30-40 seconds total
  • Cost: ~$0.04-0.08


📖 DOCUMENTATION GUIDE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Start here:
  → DEEPSEEK_QUICKSTART.md        (5 minute guide)

Need details:
  → DEEPSEEK_SETUP.md             (Setup + troubleshooting)

Understand the prompt:
  → DEEPSEEK_PROMPT_TEMPLATE.md   (Exact prompt structure)

Full reference:
  → DEEPSEEK_COMPLETE.md          (Complete guide)

System overview:
  → IMPLEMENTATION_SUMMARY.md     (System design)


⚡ COMMON COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Initialize (run once)
python3 deepseek_processor.py --init

# Process all remaining articles
python3 deepseek_processor.py

# Process specific number of batches
python3 deepseek_processor.py --batch-size 5 --max-batches 3

# Get results for one article
python3 deepseek_processor.py --query 16

# Export to JSON
python3 deepseek_processor.py --query 16 > article_16.json

# Check database progress
sqlite3 articles.db "SELECT COUNT(*) FROM articles WHERE deepseek_processed=1;"


🎯 NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Read DEEPSEEK_QUICKSTART.md for 5-minute setup
2. Run the three commands above
3. Check deepseek_batch_1.json for sample output
4. Query article 16 to see full analysis
5. Integrate results into your application


💡 TIPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Start with small batch size (5) to test
• Check deepseek_batch_N.json files for quality
• Process in batches of 5-10 for best results
• Use --max-batches to control processing
• Monitor deepseek_processed column to track progress
• Save queries to JSON for easy integration
• Chinese summaries are great for international readers


❓ TROUBLESHOOTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

See DEEPSEEK_SETUP.md for detailed troubleshooting guide.

Common issues:
  • "requests not found" → pip install requests
  • "No articles found" → Run --init first
  • "API error" → Check API key and internet connection
  • "JSON parse error" → Check deepseek_batch_N.json for response format


📞 SUPPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

All documentation is included in this directory.
Check the markdown files for detailed help.


✅ READY TO START!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Everything is set up and ready to use.
Just run the 3 commands above to get started!

Questions? Check the documentation files included in this directory.

