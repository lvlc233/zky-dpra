import ast
import os
import sys

def check_syntax(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        source = f.read()
                    ast.parse(source)
                except SyntaxError as e:
                    print(f"SyntaxError in {path}: {e}")
                except Exception as e:
                    print(f"Error checking {path}: {e}")

if __name__ == "__main__":
    target_dir = r"g:\work\project\bishe\Agent\DeepPaperResearcher\zky\zky-dpra\main\backend"
    print(f"Checking syntax in {target_dir}...")
    check_syntax(target_dir)
    print("Done.")
