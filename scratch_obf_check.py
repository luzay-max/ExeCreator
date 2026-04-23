
def test_junk(source):
    lines = source.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        result.append(line)
        stripped = line.strip()
        if stripped.startswith('def ') and stripped.endswith(':'):
            indent = len(line) - len(line.lstrip())
            body_indent = indent + 4

            j = i + 1
            while j < len(lines) and (lines[j].strip() == '' or
                                       lines[j].strip().startswith('"""') or
                                       lines[j].strip().startswith("'''")):
                result.append(lines[j])
                j += 1
                if j <= len(lines) and (lines[j - 1].strip().startswith('"""') or
                                       lines[j - 1].strip().startswith("'''")):
                    quote = '"""' if lines[j - 1].strip().startswith('"""') else "'''"
                    if lines[j - 1].strip().count(quote) < 2 and len(lines[j - 1].strip()) >= 3:
                        while j < len(lines) and quote not in lines[j]:
                            result.append(lines[j])
                            j += 1
                        if j < len(lines):
                            result.append(lines[j])
                            j += 1
            i = j
            result.append(" " * body_indent + "if False: pass")
            continue
        i += 1
    return '\n'.join(result)

print(test_junk("""def foo():
    \"\"\"single line doc\"\"\"
    x = 1

def bar():
    \"\"\"
    multi line doc
    \"\"\"
    y = 2
"""))
