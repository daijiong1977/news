#!/usr/bin/env python3
"""
Step 3: Insert article content into template placeholders
This script reads template_variables.json and inserts content into email_template_conditional.html
"""

import json
import re

# Read template variables
with open('/Users/jidai/news/template_variables.json', 'r', encoding='utf-8') as f:
    variables = json.load(f)['variables']

# Read template
with open('/Users/jidai/news/email_template_conditional.html', 'r', encoding='utf-8') as f:
    template = f.read()

# Replace placeholders with actual content
for var_name, var_content in variables.items():
    placeholder = '{{ ' + var_name + ' }}'
    template = template.replace(placeholder, var_content)

# Save the final template with content inserted
output_path = '/Users/jidai/news/email_template_with_content.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(template)

print("\n" + "=" * 80)
print("✅ STEP 3 COMPLETE: Article content inserted into template")
print("=" * 80)
print(f"\nOutput file: {output_path}")
print(f"Template size: {len(template):,} bytes")
print("\nVariables inserted:")
for var_name in variables.keys():
    print(f"  ✅ {var_name}")

print("\n" + "=" * 80)
print("NEXT: Copy template to Buttondown via API")
print("=" * 80 + "\n")
