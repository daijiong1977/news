#!/usr/bin/env python3
"""
Extract Article Content from HTML Files

Converts the 4 article HTML files into template variables:
- article_body_easy
- article_body_mid
- article_body_hard
- article_body_CN

These variables can be used in the Jinja2 conditional template.
"""

import re
import json
from pathlib import Path
from typing import Dict

def extract_article_section(html_content: str) -> str:
    """
    Extract the article section from HTML.
    
    Looks for the featured article structure and extracts just the article div.
    """
    
    # Find the first article div
    pattern = r'<div class="article">.*?</div>\s*</div>\s*</div>'
    match = re.search(pattern, html_content, re.DOTALL)
    
    if match:
        return match.group(0)
    
    return ""

def extract_article_content(html_file: str) -> str:
    """
    Extract article content from an HTML file.
    
    Returns the article div HTML that can be used as a template variable.
    """
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract the article div
        article_div = extract_article_section(content)
        
        if article_div:
            print(f"✅ Extracted from {html_file}")
            return article_div
        else:
            print(f"⚠️  Could not extract article from {html_file}")
            return ""
    
    except Exception as e:
        print(f"❌ Error reading {html_file}: {e}")
        return ""

def generate_template_variables() -> Dict[str, str]:
    """Generate template variables from 4 HTML files."""
    
    print("\n" + "=" * 70)
    print("EXTRACTING ARTICLE CONTENT FOR TEMPLATE VARIABLES")
    print("=" * 70 + "\n")
    
    files = {
        'easy': 'email_enhanced_easy.html',
        'mid': 'email_enhanced_mid.html',
        'hard': 'email_enhanced_hard.html',
        'CN': 'email_enhanced_CN.html'
    }
    
    variables = {}
    
    for level, filename in files.items():
        if not Path(filename).exists():
            print(f"❌ File not found: {filename}")
            continue
        
        content = extract_article_content(filename)
        if content:
            var_name = f'article_body_{level}'
            variables[var_name] = content
            print(f"   Stored in: {var_name}")
    
    return variables

def create_template_python_file(variables: Dict[str, str]):
    """Create a Python file with template variables."""
    
    print("\n" + "=" * 70)
    print("CREATING TEMPLATE VARIABLES FILE")
    print("=" * 70 + "\n")
    
    # Create Python file with variables
    python_code = '''#!/usr/bin/env python3
"""
Email Template Variables

These variables are used in email_template_conditional.html
with Jinja2 conditional logic to show level-specific content.

Usage in Buttondown:
1. Copy email_template_conditional.html to Buttondown
2. Use these variables in the template:
   - {{ article_body_easy }}
   - {{ article_body_mid }}
   - {{ article_body_hard }}
   - {{ article_body_CN }}
"""

# Article content for each difficulty level
# These are HTML strings that replace {{ article_body_* }} in the template

'''
    
    for var_name, content in variables.items():
        # Properly escape the HTML for Python
        escaped_content = content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        python_code += f'\n{var_name} = """{content}"""\n'
    
    with open('template_variables.py', 'w', encoding='utf-8') as f:
        f.write(python_code)
    
    print(f"✅ Created: template_variables.py")
    print(f"   Contains: {len(variables)} template variables")

def create_template_json_file(variables: Dict[str, str]):
    """Create a JSON file with template variables for Buttondown."""
    
    print("\n" + "=" * 70)
    print("CREATING TEMPLATE VARIABLES JSON")
    print("=" * 70 + "\n")
    
    json_data = {
        'template_version': '1.0',
        'description': 'Email template variables for multi-level emails',
        'usage': {
            'easy': 'For easy/beginner subscribers',
            'mid': 'For middle/intermediate subscribers',
            'hard': 'For hard/expert subscribers',
            'CN': 'For Chinese language subscribers'
        },
        'variables': variables
    }
    
    with open('template_variables.json', 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Created: template_variables.json")
    print(f"   Format: JSON (can import to Buttondown)")

def create_buttondown_instructions():
    """Create instructions for using with Buttondown."""
    
    instructions = """# Using Conditional Email Template with Buttondown

## Overview
This approach uses a SINGLE HTML template with Jinja2 conditional logic.
Each subscriber receives the SAME email HTML, but Buttondown renders
different content based on their tags.

## Setup Steps

### 1. Verify Subscriber Tags
Make sure each subscriber has the correct tag:
```
easy@daijiong.com     → Tag: level_easy
mid@daijiong.com      → Tag: level_mid
diff@daijiong.com     → Tag: level_hard
cn@daijiong.com       → Tag: level_CN
```

Run to verify:
```bash
python3 verify_subscriber_tags.py
```

### 2. Copy Template to Buttondown
1. Go to Buttondown Dashboard
2. Create new Email Draft
3. Copy entire content of `email_template_conditional.html`
4. Paste into Buttondown editor
5. Click "Save as Draft"

### 3. Add Template Variables
In Buttondown email editor:

Find this section:
```
{% if "level_easy" in subscriber.tags %}
    {{ article_body_easy }}
```

Replace with the article HTML from template_variables.json or template_variables.py

### 4. Test Template
Buttondown has a template preview feature:
1. In email editor, click "Preview"
2. Select each test subscriber
3. Verify correct content shows for each level

### 5. Send
- Select "Send to specific subscribers" or schedule
- Buttondown will automatically:
  - Check subscriber tags
  - Render appropriate {% if %} block
  - Show correct article_body_* variable
  - Send personalized HTML to each subscriber

## How It Works

```
Buttondown Email Template (Single File)
├─ {% if "level_easy" in subscriber.tags %}
│  └─ Shows: article_body_easy (beginner content)
├─ {% elif "level_mid" in subscriber.tags %}
│  └─ Shows: article_body_mid (intermediate content)
├─ {% elif "level_hard" in subscriber.tags %}
│  └─ Shows: article_body_hard (expert content)
├─ {% elif "level_CN" in subscriber.tags %}
│  └─ Shows: article_body_CN (Chinese content)
└─ {% else %}
   └─ Shows: Warning message

When sending:
1. Buttondown checks each subscriber's tags
2. Evaluates the Jinja2 conditions
3. Renders the matching {{ article_body_* }} block
4. Sends personalized HTML to subscriber
```

## Subscriber Receives

```
easy@daijiong.com:
  ├─ Header: 🟢 Easy Level (green)
  ├─ Content: article_body_easy (beginner version)
  └─ Footer: Standard

mid@daijiong.com:
  ├─ Header: 🔵 Middle Level (blue)
  ├─ Content: article_body_mid (intermediate version)
  └─ Footer: Standard

diff@daijiong.com:
  ├─ Header: 🟠 Hard Level (orange)
  ├─ Content: article_body_hard (expert version)
  └─ Footer: Standard

cn@daijiong.com:
  ├─ Header: 🔴 中文版本 (red, Chinese)
  ├─ Content: article_body_CN (Chinese version)
  └─ Footer: Standard
```

## Files Used

| File | Purpose |
|------|---------|
| `email_template_conditional.html` | Main template with Jinja2 logic |
| `template_variables.json` | Article content as JSON |
| `template_variables.py` | Article content as Python variables |
| `verify_subscriber_tags.py` | Verify tags are set correctly |

## Testing

### Before Sending
1. Verify tags: `python3 verify_subscriber_tags.py`
2. Preview in Buttondown with each test subscriber
3. Confirm correct content shows for each level

### After Sending
1. Check test email accounts
2. Verify each gets correct difficulty level
3. Verify images load
4. Verify formatting looks good

## Advantages of This Approach

✅ Single template to manage
✅ Automatic level detection based on tags
✅ Easy to update (change once, applies to all)
✅ Scales to thousands of subscribers
✅ No manual campaign per level needed
✅ Built-in preview/testing in Buttondown

## Next Steps

1. Run: `python3 verify_subscriber_tags.py`
2. Copy `email_template_conditional.html` to Buttondown
3. Replace `{{ article_body_* }}` placeholders with actual HTML
4. Test in Buttondown preview
5. Send to test subscribers
6. Verify correct levels received

"""
    
    with open('CONDITIONAL_TEMPLATE_GUIDE.md', 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    print(f"✅ Created: CONDITIONAL_TEMPLATE_GUIDE.md")

def main():
    """Main execution."""
    
    print("=" * 70)
    print("TEMPLATE VARIABLE EXTRACTION")
    print("=" * 70)
    
    # Extract variables
    variables = generate_template_variables()
    
    if not variables:
        print("\n❌ No variables extracted. Check that HTML files exist.")
        return
    
    # Create output files
    create_template_python_file(variables)
    create_template_json_file(variables)
    create_buttondown_instructions()
    
    print("\n" + "=" * 70)
    print("✅ EXTRACTION COMPLETE")
    print("=" * 70)
    print("\nFiles created:")
    print("  ✓ email_template_conditional.html - Main template with Jinja2 logic")
    print("  ✓ template_variables.py - Variables as Python code")
    print("  ✓ template_variables.json - Variables as JSON")
    print("  ✓ CONDITIONAL_TEMPLATE_GUIDE.md - Usage instructions")
    print("\nNext steps:")
    print("  1. Run: python3 verify_subscriber_tags.py")
    print("  2. Copy email_template_conditional.html to Buttondown")
    print("  3. Replace {{ article_body_* }} with content from template_variables.json")
    print("  4. Test in Buttondown preview")
    print("  5. Send to test subscribers")

if __name__ == "__main__":
    main()
