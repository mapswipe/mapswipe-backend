# /// script
# dependencies = [
#   "requests<3",
#   "pyright==1.1.398",
# ]
# ///

# ruff: noqa: T201

import json
import os
import re
import subprocess
import sys
from collections import defaultdict

# NOTE:
# - Example usage: `uv run bulk_ignore_pyright_warnings.py .`
# - We need to use the same version of python as specified on precommit
# - We look for pyproject.toml on the current working directory

SEVERITY = "warning"


def run_pyright(path: str) -> dict:  # type: ignore[reportMissingTypeArgument]
    """Run pyright and return JSON output."""
    command = ["pyright", path, "--project", "./pyproject.toml", "--outputjson"]
    print(" ".join(command))
    result = subprocess.run(  # noqa: S603
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 1):
        # 0: no issues, 1: warnings/errors
        print(f"Error: return code should either be 0 or 1 but got f{result.returncode}", result.stderr)
        sys.exit(1)
    return json.loads(result.stdout)


def apply_specific_ignores(pyright_output: dict):  # type: ignore[reportMissingTypeArgument]
    """Apply specific pyright ignore comments to lines with warnings."""
    # {file: {line_num: {rule_codes}}}
    file_warnings: defaultdict[str, defaultdict[int, set[str]]] = defaultdict(lambda: defaultdict(set))

    for diag in pyright_output.get("generalDiagnostics", []):
        if "file" not in diag or "range" not in diag or "rule" not in diag or "severity" not in diag:
            print("Error: diagnostics should define file, range and rule", diag)
            continue
        if diag["severity"] != SEVERITY:
            continue

        file_path = diag["file"]
        line = diag["range"]["start"]["line"]
        rule = diag["rule"].strip()
        file_warnings[file_path][line].add(rule)

    total_files_modified = 0
    total_lines_modified = 0

    for file_path, line_issues in file_warnings.items():
        if not os.path.exists(file_path):  # noqa: PTH110
            print(f"Error: could not open file for reading {file_path}")
            continue

        with open(file_path, encoding="utf-8") as f:  # noqa: PTH123
            lines = f.readlines()

        file_modified = False
        for line_num, rules in sorted(line_issues.items()):
            if line_num >= len(lines):
                print(f"Warning: diagnostic line number {line_num} is greater than total lines {len(lines)}")
                continue

            if len(rules) <= 0:
                continue

            # Remove new line
            current_line = lines[line_num].rstrip("\n")

            comment_regex = re.compile(r"#\s*type:\s*ignore(?:\[(.*?)\])?")
            match = comment_regex.match(current_line)

            # list of new ignores
            all_rules = set[str](rules)

            if match:
                existing_ignore_comment = match.group(0)
                existing_rules_str = match.group(1)

                # get existing ignores
                if existing_rules_str:
                    existing_rules = existing_rules_str.split(",")
                    all_rules.update(*existing_rules)

                # replace existing comment in line
                modified_comment_part = "# type: ignore[" + ", ".join(all_rules) + "]"
                lines[line_num] = current_line.replace(
                    existing_ignore_comment,
                    modified_comment_part,
                )
            else:
                # append to line
                new_comment_part = "  # type: ignore[" + ", ".join(all_rules) + "]"
                lines[line_num] = current_line + new_comment_part + "\n"

            total_lines_modified += 1
            file_modified = True

        if file_modified:
            with open(file_path, "w", encoding="utf-8") as f:  # noqa: PTH123
                f.writelines(lines)
            total_files_modified += 1
            print(f"Updated file {file_path}")

    print(f"Updated {total_lines_modified} lines in {total_files_modified} files")


if __name__ == "__main__":
    target_path = sys.argv[1] if len(sys.argv) > 1 else "."
    print("Running pyright")
    output = run_pyright(target_path)
    apply_specific_ignores(output)
