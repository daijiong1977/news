#!/usr/bin/env python3
"""
Compare DeepSeek Chat Mode vs Research Mode analysis quality.
Processes the same article with both modes and generates comparison report.
"""

import subprocess
import json
import time
from pathlib import Path
from datetime import datetime

def run_chat_mode():
    """Process one article with chat mode."""
    print("\n" + "="*70)
    print("🤖 MODE 1: CHAT MODE (Current)")
    print("="*70)
    
    start = time.time()
    result = subprocess.run(
        ["python3", "deepseek_processor.py", "--batch-size", "1", "--max-batches", "1"],
        capture_output=True,
        text=True
    )
    chat_time = time.time() - start
    
    print(result.stdout)
    if result.returncode != 0:
        print("❌ Error:", result.stderr)
        return None, chat_time
    
    # Try to load the response
    response_file = Path("deepseek_batch_1.json")
    if response_file.exists():
        with open(response_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if content.startswith("```"):
                content = content.lstrip("`").lstrip("json").lstrip(" \n")
            if content.endswith("```"):
                content = content.rstrip("`").rstrip(" \n")
            try:
                data = json.loads(content)
                return data, chat_time
            except:
                return None, chat_time
    
    return None, chat_time


def run_research_mode():
    """Process one article with research mode."""
    print("\n" + "="*70)
    print("🔬 MODE 2: RESEARCH MODE (New)")
    print("="*70)
    
    start = time.time()
    result = subprocess.run(
        ["python3", "deepseek_research_processor.py", "--batch-size", "1", "--max-batches", "1"],
        capture_output=True,
        text=True
    )
    research_time = time.time() - start
    
    print(result.stdout)
    if result.returncode != 0:
        print("❌ Error:", result.stderr)
        return None, research_time
    
    # Try to load the response
    response_file = Path("deepseek_research_batch_1.json")
    if response_file.exists():
        with open(response_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if content.startswith("```"):
                content = content.lstrip("`").lstrip("json").lstrip(" \n")
            if content.endswith("```"):
                content = content.rstrip("`").rstrip(" \n")
            try:
                data = json.loads(content)
                return data, research_time
            except:
                return None, research_time
    
    return None, research_time


def generate_comparison_report(chat_data, research_data, chat_time, research_time):
    """Generate detailed comparison report."""
    
    report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║          DEEPSEEK API MODE COMPARISON REPORT                              ║
║          Chat Mode vs Research Mode                                        ║
║          {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                                      ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 PERFORMANCE METRICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Chat Mode (Current):
  Response Time: {chat_time:.1f} seconds
  Status: {'✅ SUCCESS' if chat_data else '❌ FAILED'}
  
Research Mode (New):
  Response Time: {research_time:.1f} seconds
  Status: {'✅ SUCCESS' if research_data else '❌ FAILED'}

⏱️  SPEED COMPARISON:
  Research mode is {abs(research_time - chat_time):.1f}s {'faster' if research_time < chat_time else 'slower'}
  Ratio: Research is {(research_time/chat_time):.2f}x {'faster' if research_time < chat_time else 'slower'}

"""
    
    if chat_data:
        report += f"""
📋 CHAT MODE ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Summary Length:
  English: {len(chat_data.get('summary_en', ''))} characters
  Chinese: {len(chat_data.get('summary_zh', ''))} characters

Keywords: {len(chat_data.get('key_words', []))}
Questions: {len(chat_data.get('multiple_choice_questions', []))}

Question Types Distribution:
  """
        types = {}
        for q in chat_data.get('multiple_choice_questions', []):
            q_type = q.get('word_type', 'unknown')
            types[q_type] = types.get(q_type, 0) + 1
        
        for q_type, count in types.items():
            report += f"\n  • {q_type}: {count}"
    
    if research_data:
        report += f"""

🔬 RESEARCH MODE ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Summary Length:
  English: {len(research_data.get('research_summary_en', ''))} characters
  Chinese: {len(research_data.get('research_summary_zh', ''))} characters

Research Keywords: {len(research_data.get('research_keywords', []))}
Deep Questions: {len(research_data.get('deep_questions', []))}

Question Difficulty Distribution:
  """
        difficulties = {}
        for q in research_data.get('deep_questions', []):
            difficulty = q.get('difficulty', 'unknown')
            difficulties[difficulty] = difficulties.get(difficulty, 0) + 1
        
        for diff, count in difficulties.items():
            report += f"\n  • {diff}: {count}"
        
        report += f"""

Cognitive Levels Used:
  """
        levels = {}
        for q in research_data.get('deep_questions', []):
            level = q.get('cognitive_level', 'unknown')
            levels[level] = levels.get(level, 0) + 1
        
        for level, count in levels.items():
            report += f"\n  • {level}: {count}"
    
    report += f"""

📝 COMPARISON SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Strengths of Chat Mode:
  ✓ Faster response time ({chat_time:.1f}s)
  ✓ Good balance of question types
  ✓ Clear, accessible explanations
  ✓ Works well for general learning

Strengths of Research Mode:
  ✓ More detailed academic analysis
  ✓ Includes cognitive difficulty levels
  ✓ Research-focused perspectives
  ✓ Identifies research gaps
  ✓ Better for advanced learners

🎯 RECOMMENDATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
    
    if research_time <= chat_time * 1.5:  # If research is less than 1.5x slower
        report += """
✅ USE RESEARCH MODE if:
  • You want deeper academic analysis
  • You need research gaps identified
  • You want multi-level questions
  • Speed difference is acceptable

✅ USE CHAT MODE if:
  • You need fast processing (quick turnaround)
  • You prefer straightforward content
  • You're processing many articles
  • Speed is critical
"""
    else:
        report += """
⚠️  RESEARCH MODE IS SLOWER
  Current timing suggests chat mode is preferable for batch processing.
  Use research mode only for special in-depth analysis needs.
"""
    
    report += f"""

Files Generated:
  • deepseek_batch_1.json (Chat Mode Response)
  • deepseek_research_batch_1.json (Research Mode Response)
  • comparison_report.txt (This report)

"""
    
    return report


def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                    STARTING API MODE COMPARISON TEST                      ║
║                                                                            ║
║     Processing the same article with both Chat and Research modes         ║
║     to determine which is better for your learning platform               ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")
    
    # Run both modes
    chat_data, chat_time = run_chat_mode()
    time.sleep(3)  # Wait between API calls
    research_data, research_time = run_research_mode()
    
    # Generate report
    report = generate_comparison_report(chat_data, research_data, chat_time, research_time)
    
    print(report)
    
    # Save report
    with open('comparison_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("✓ Comparison report saved to: comparison_report.txt")
    
    # Summary
    print("\n" + "="*70)
    print("📊 QUICK SUMMARY")
    print("="*70)
    if chat_data:
        print(f"✅ Chat Mode: {len(chat_data.get('multiple_choice_questions', []))} questions in {chat_time:.1f}s")
    else:
        print(f"❌ Chat Mode: Failed after {chat_time:.1f}s")
    
    if research_data:
        print(f"✅ Research Mode: {len(research_data.get('deep_questions', []))} questions in {research_time:.1f}s")
    else:
        print(f"❌ Research Mode: Failed after {research_time:.1f}s")


if __name__ == "__main__":
    main()
