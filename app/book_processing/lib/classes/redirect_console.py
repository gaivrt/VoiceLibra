import sys
import io
from threading import Lock

class RedirectConsole:
    """控制台输出重定向类"""
    def __init__(self):
        self.buffer = io.StringIO()
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.lock = Lock()
        
    def __enter__(self):
        """进入重定向上下文"""
        sys.stdout = self.buffer
        sys.stderr = self.buffer
        return self
        
    def __exit__(self, exc_type, exc_value, traceback):
        """退出重定向上下文"""
        sys.stdout = self.stdout
        sys.stderr = self.stderr
        
    def get_output(self):
        """获取缓冲区内容"""
        with self.lock:
            output = self.buffer.getvalue()
            self.buffer.truncate(0)
            self.buffer.seek(0)
        return output