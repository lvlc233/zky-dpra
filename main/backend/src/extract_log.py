
with open("summary_debug_log_v2.txt", "rb") as f:
    content = f.read()
    try:
        text = content.decode("utf-16")
        lines = text.splitlines()
        # Print only relevant lines to avoid truncation
        for line in lines:
            if "Effective config" in line or "SummaryAgent" in line or "error" in line.lower() or "Exception" in line:
                print(line)
    except Exception as e:
        print(f"Error: {e}")
