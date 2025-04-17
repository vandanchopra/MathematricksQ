import os
import argparse
import re

def _get_new_version(parent_filepath: str = None) -> tuple[str, str]:
    """
    Get parent's version and add _1, _2, etc. based on existing files.
    Args:
        parent_filepath: Path to parent strategy file (e.g., strategy_v1_0_1.py). If None, returns v1
    Returns:
        Tuple of (version number, full filepath) for the new file
    """
    # If no parent filepath provided, return v1 in current directory
    if parent_filepath is None:
        return "1", os.path.join(os.getcwd(), "strategy_v1.py")
        
    # Get directory and parent's version
    parent_dir = os.path.dirname(parent_filepath)
    parent_file = os.path.basename(parent_filepath)
    
    # Extract parent's version (e.g., from strategy_v1_0_1.py get 1_0_1)
    match = re.search(r'strategy_v(.+?)\.py', parent_file)
    if not match:
        new_version = "1"
        return os.path.join(parent_dir, f"strategy_v{new_version}.py")
    
    parent_version = match.group(1)  # e.g., "1_0_1"
    
    # Find all files with same base version but different trailing number
    existing_versions = []
    base_version = parent_version  # e.g., "1_0_1"
    base_prefix = f"strategy_v{base_version}_"  # e.g., "strategy_v1_0_1_"
    
    for fname in os.listdir(parent_dir):
        if fname.startswith(base_prefix) and fname.endswith(".py"):
            try:
                # Extract trailing number (e.g., from strategy_v1_0_1_2.py get 2)
                trailing = re.search(rf'{base_prefix}(\d+)\.py', fname)
                if trailing:
                    existing_versions.append(int(trailing.group(1)))
            except:
                continue
    
    # If no versions with trailing number exist, start with 1
    if not existing_versions:
        new_version = f"{base_version}_1"
    else:
        # Otherwise, use next available number
        next_num = max(existing_versions) + 1
        new_version = f"{base_version}_{next_num}"
    
    new_filepath = os.path.join(parent_dir, f"strategy_v{new_version}.py")
    return new_filepath

def main():
    parser = argparse.ArgumentParser(description='Get next version number and filepath for strategy files')
    parser.add_argument('filepath', nargs='?', default=None, 
                       help='Path to the strategy file (e.g., path/to/strategy_v1.py). If not provided, returns v1')
    args = parser.parse_args()
    
    try:
        filepath = _get_new_version(args.filepath)
        print(f"New filepath: {filepath}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
