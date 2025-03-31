import os
import datetime
import traceback

LOG_FILE = "debug.log"

def log_message(msg, error=False):
    """Log a message to the debug file with timestamp"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_type = "ERROR" if error else "INFO"
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [{log_type}] {msg}\n")

def log_error(msg, exc=None):
    """Log an error message and optional exception traceback"""
    log_message(msg, error=True)
    if exc:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(traceback.format_exc())
            f.write("\n")

def log_file_status(filepath):
    """Log the status of a file (exists, size, etc.)"""
    try:
        msg = f"File check: {filepath} - "
        if not os.path.exists(filepath):
            msg += "DOES NOT EXIST"
        else:
            size = os.path.getsize(filepath)
            msg += f"EXISTS, size={size} bytes"
            try:
                with open(filepath, "rb") as f:
                    f.seek(0)
                    msg += ", READABLE"
            except Exception as e:
                msg += f", NOT READABLE ({str(e)})"
        log_message(msg)
        return msg
    except Exception as e:
        log_error(f"Error checking file {filepath}: {str(e)}", e)
        return f"Error checking file: {str(e)}"