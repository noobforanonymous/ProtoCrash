"""
Keyboard input handler for dashboard
"""

import sys
import threading
import time


class KeyboardHandler:
    """Non-blocking keyboard input handler"""

    def __init__(self):
        self.paused = False
        self.should_refresh = False
        self.running = True
        self._thread = None

    def start(self):
        """Start keyboard listener thread"""
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()

    def _listen(self):
        """Listen for keyboard input (cross-platform)"""
        try:
            # Try Unix/Linux termios
            import termios
            import tty
            import select

            old_settings = termios.tcgetattr(sys.stdin)
            try:
                tty.setcbreak(sys.stdin.fileno())
                while self.running:
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        key = sys.stdin.read(1).lower()
                        self._handle_key(key)
            finally:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

        except (ImportError, OSError):
            # Fallback for Windows or non-TTY environments
            try:
                import msvcrt
                while self.running:
                    if msvcrt.kbhit():
                        key = msvcrt.getch().decode('utf-8').lower()
                        self._handle_key(key)
                    time.sleep(0.1)
            except ImportError:
                # No keyboard support available
                pass

    def _handle_key(self, key):
        """Handle keypress"""
        if key == 'p':
            self.paused = not self.paused
        elif key == 'r':
            self.should_refresh = True
        elif key == 'q':
            self.running = False

    def stop(self):
        """Stop keyboard listener"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=1.0)
