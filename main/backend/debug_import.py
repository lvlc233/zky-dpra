
import sys
import os
import traceback

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.append(src_dir)

try:
    from worker.tasks import WorkerSettings
    print("Import successful")
    print(f"Functions: {WorkerSettings.functions}")
    print(f"Redis Settings: {WorkerSettings.redis_settings}")
except Exception:
    traceback.print_exc()
