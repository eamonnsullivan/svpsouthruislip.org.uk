"""Check recorded import safety and run installed cfn-lint offline."""

import argparse
import shutil
import subprocess
import sys

import yaml

from prepare_infrastructure_import import ROOT, STACKS, load_inventory


def check(root=ROOT, runner=subprocess.run, executable=None):
    """Validate all inputs before linting each template in its actual region."""
    _, _, stacks = load_inventory(root)
    executable = executable or shutil.which("cfn-lint")
    if not executable:
        raise ValueError("cfn-lint is not installed; use the project's pinned dependencies")
    failed = False
    for name in STACKS:
        stack = stacks[name]
        result = runner([executable, "--template", str(stack["template_path"]),
                         "--regions", stack["region"], "--non-zero-exit-code", "warning"],
                        check=False)
        failed = failed or result.returncode != 0
    if failed:
        raise ValueError("cfn-lint reported findings; review its output")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        check()
    except (ValueError, TypeError, KeyError, OSError, yaml.YAMLError) as error:
        parser.exit(1, f"Infrastructure check failed: {error}\n")
    print("Offline infrastructure validation and regional cfn-lint checks passed. No AWS verification performed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
