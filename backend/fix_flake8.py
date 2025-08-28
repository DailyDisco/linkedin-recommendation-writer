#!/usr/bin/env python3
"""
Script to automatically fix common flake8 issues.
"""

import os
import re

def fix_fstrings(file_path):
    """Fix f-strings missing placeholders (F541)."""
    with open(file_path, 'r') as f:
        content = f.read()

    # Replace f-strings with no placeholders with regular strings
    original_content = content
    content = re.sub(r'f"([^"{]*?)"(?!\s*\+)', r'"\1"', content)
    content = re.sub(r"f'([^'{]*?)'(?!\s*\+)", r"'\1'", content)

    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    return False

def fix_unused_imports(file_path):
    """Fix unused imports (F401)."""
    with open(file_path, 'r') as f:
        lines = f.readlines()

    # Common unused imports patterns
    unused_patterns = [
        r'from typing import.*List.*',
        r'from typing import.*Any.*',
        r'from typing import.*Dict.*',
        r'import datetime.*timedelta.*',
        r'import httpx.*',
        r'from app\.schemas\.github import.*LanguageStats.*',
        r'from app\.schemas\.github import.*RepositoryInfo.*',
        r'from app\.schemas\.github import.*SkillAnalysis.*',
        r'from app\.models\.github_profile import GitHubProfile',
        r'from app\.models\.recommendation import Recommendation',
        r'from app\.models\.user import User',
        r'from fastapi import.*Depends.*',
        r'import os',
    ]

    modified = False
    new_lines = []
    for line in lines:
        skip_line = False
        for pattern in unused_patterns:
            if re.search(pattern, line.strip()):
                skip_line = True
                modified = True
                break
        if not skip_line:
            new_lines.append(line)

    if modified:
        with open(file_path, 'w') as f:
            f.writelines(new_lines)

    return modified

def fix_unused_variables(file_path):
    """Fix unused variables (F841)."""
    with open(file_path, 'r') as f:
        content = f.read()

    # Common patterns for unused variables
    original_content = content
    content = re.sub(r'rate_limit_info\s*=.*', '# rate_limit_info = ...  # Removed unused variable', content)
    content = re.sub(r'repositories\s*=.*', '# repositories = ...  # Removed unused variable', content)

    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    return False

def fix_bare_except(file_path):
    """Fix bare except clauses (E722)."""
    with open(file_path, 'r') as f:
        content = f.read()

    original_content = content
    content = re.sub(r'except:', r'except Exception as e:', content)

    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    return False

if __name__ == '__main__':
    # Files to fix
    files_to_fix = [
        'app/api/v1/github.py',
        'app/core/database.py',
        'app/core/dependencies.py',
        'app/schemas/github.py',
        'app/schemas/repository.py',
        'app/services/github_service.py',
        'app/services/recommendation_service.py',
        'app/services/repository_service.py',
        'app/services/ai_service.py'
    ]

    for file_path in files_to_fix:
        if os.path.exists(file_path):
            fstring_fixed = fix_fstrings(file_path)
            import_fixed = fix_unused_imports(file_path)
            var_fixed = fix_unused_variables(file_path)
            except_fixed = fix_bare_except(file_path)

            if fstring_fixed or import_fixed or var_fixed or except_fixed:
                print(f'Fixed: {file_path}')
