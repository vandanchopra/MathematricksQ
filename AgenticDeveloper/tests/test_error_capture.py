import os

def check_errors_in_console_output(console_output: str) -> tuple[list, list]:
    """Check for error messages and warnings in the console output and extract multi-line blocks."""
    errors = []
    warnings = []
    lines = console_output.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        is_warning = "warning" in line.lower()
        is_error = (
            ("error" in line.lower() and "tracking error" not in line.lower())
            or ("syntaxerror" in line.lower())
            or ("traceback" in line.lower())
            or ("exception" in line.lower())
            or ("failed" in line.lower() and "failed data requests" not in line.lower())
            or ("could not" in line.lower())
            or ("unable to" in line.lower())
            or "compiler error" in line.lower()
        )
        
        if is_warning or is_error:
            message_block = [line.rstrip()]
            i += 1
            # Capture any related context (indented lines, stack traces, etc.)
            while i < len(lines) and (
                lines[i].startswith(" ")
                or lines[i].startswith("\t")
                or lines[i].startswith("***")
                or lines[i].strip() == ""
                or "at line" in lines[i].lower()
                or "at" in lines[i].lower()
                or "in" in lines[i].lower()
            ):
                message_block.append(lines[i].rstrip())
                i += 1
            if is_warning:
                warnings.append("\n".join(message_block))
            else:
                errors.append("\n".join(message_block))
        else:
            i += 1
            
    return errors, warnings

def test_error_capture():
    """Test error and warning capture from output file."""
    output_file = "Strategies/AgenticDev/LazyYellowCat/backtests/2025-04-25_12-10-47/output.txt"
    
    # Read the output file
    with open(output_file, 'r') as f:
        content = f.read()
    
    # Extract errors and warnings
    errors, warnings = check_errors_in_console_output(content)
    
    # Display results
    print("\n=== WARNINGS ===")
    print(f"Found {len(warnings)} warnings:")
    for i, warning in enumerate(warnings, 1):
        print(f"\nWarning {i}:")
        print(warning)
        print("-" * 80)
    
    print("\n=== ERRORS ===")
    print(f"Found {len(errors)} errors:")
    for i, error in enumerate(errors, 1):
        print(f"\nError {i}:")
        print(error)
        print("-" * 80)

if __name__ == "__main__":
    test_error_capture()