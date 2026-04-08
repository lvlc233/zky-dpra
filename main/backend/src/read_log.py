
with open("summary_debug_log_v2.txt", "rb") as f:
    content = f.read()
    # Try different encodings
    for encoding in ["utf-16", "utf-16-le", "utf-8"]:
        try:
            print(f"--- Decoded with {encoding} ---")
            print(content.decode(encoding))
            break
        except Exception:
            continue
