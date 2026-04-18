"""
Full JS syntax validation of index.html:
- Extract all <script> blocks
- Check for common syntax errors
- Verify all functions are properly closed
"""
import pathlib, re, subprocess, json, os

h = pathlib.Path("static/index.html").read_text(encoding="utf-8")

# Extract JS from <script> tags
scripts = re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', h, re.DOTALL)
print(f"Found {len(scripts)} inline script blocks")

# Combine all scripts
combined = "\n".join(scripts)
print(f"Total inline JS: {len(combined)} chars")

# Write to temp file
temp_js = pathlib.Path("_temp_check.js")
temp_js.write_text(combined, encoding="utf-8")

# Use node.js to syntax check if available
result = subprocess.run(
    ["node", "--check", str(temp_js)],
    capture_output=True, text=True
)
if result.returncode == 0:
    print("NODE SYNTAX CHECK: PASS")
else:
    print("NODE SYNTAX ERROR:")
    print(result.stderr[:2000])

# Clean up
temp_js.unlink()

# Manual checks for common issues
checks = [
    # Bad regex patterns
    (r'/\.\*\[.*?(?<!\\)/\]/', "Unclosed/bad regex character class"),
    # Unterminated string (simplified)
]

issues = []
for pattern, desc in checks:
    matches = list(re.finditer(pattern, combined))
    if matches:
        for m in matches[:3]:
            line_no = combined[:m.start()].count('\n') + 1
            issues.append(f"Line ~{line_no}: {desc}: {repr(m.group()[:60])}")

# Also check bracket balance
open_braces = combined.count('{')
close_braces = combined.count('}')
open_parens = combined.count('(')
close_parens = combined.count(')')
print(f"\nBrace balance: {{ = {open_braces}, }} = {close_braces}, diff = {open_braces - close_braces}")
print(f"Paren balance: ( = {open_parens}, ) = {close_parens}, diff = {open_parens - close_parens}")

if issues:
    print("\nIssues found:")
    for i in issues:
        print(" -", i)
else:
    print("No known syntax issues found")
