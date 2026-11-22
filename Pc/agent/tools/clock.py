# Clock tools - time, date, alarm, timer, reminder
import time
import threading
from datetime import datetime, timedelta


class ClockTools:
    """Time and scheduling tools for Haven."""

    def __init__(self):
        self.alarms = {}  # key: "HH:MM" -> list of messages
        self.timers = {}  # key: name -> {"end_time": float, "message": str, "done": bool}
        self.reminders = {}  # key: name -> {"time": float, "message": str, "done": bool}

    def get_current_time(self) -> str:
        """Return the current local time."""
        now = datetime.now()
        return f"The current time is {now.strftime('%I:%M %p')} ({now.strftime('%H:%M')} in 24-hour format)."

    def get_current_date(self) -> str:
        """Return the current local date."""
        now = datetime.now()
        return f"Today is {now.strftime('%A, %B %d, %Y')}."

    def get_datetime(self) -> str:
        """Return the current date and time."""
        now = datetime.now()
        return f"The current date and time is {now.strftime('%A, %B %d, %Y')} at {now.strftime('%I:%M %p')}."

    def set_alarm(self, time_str: str, message: str = "Alarm!") -> str:
        """Set an alarm for a specific time (HH:MM in 24-hour format)."""
        try:
            hour, minute = map(int, time_str.strip().split(":"))
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                return "Invalid time. Please use HH:MM format (e.g., 07:30 or 14:00)."

            key = f"{hour:02d}:{minute:02d}"
            if key not in self.alarms:
                self.alarms[key] = []
            self.alarms[key].append(message)

            # Calculate when the alarm will trigger
            now = datetime.now()
            alarm_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if alarm_time <= now:
                alarm_time += timedelta(days=1)
            wait = (alarm_time - now).total_seconds()

            # Start alarm thread
            threading.Thread(target=self._alarm_thread, args=(key, message, wait), daemon=True).start()

            return f"Alarm set for {alarm_time.strftime('%I:%M %p')}. I'll remind you with: \"{message}\""
        except ValueError:
            return "Invalid time format. Please use HH:MM (e.g., 07:30 for 7:30 AM, 14:00 for 2:00 PM)."

    def _alarm_thread(self, key: str, message: str, wait_seconds: float):
        """Wait and trigger alarm."""
        time.sleep(wait_seconds)
        # Check if alarm still exists
        if key in self.alarms and message in self.alarms[key]:
            print(f"[Haven] ⏰ ALARM: {message}")
            # Remove this alarm
            self.alarms[key].remove(message)
            if not self.alarms[key]:
                del self.alarms[key]

    def cancel_alarm(self, time_str: str) -> str:
        """Cancel an alarm at a specific time."""
        key = time_str.strip()
        if key in self.alarms:
            messages = self.alarms.pop(key)
            return f"Alarm at {key} cancelled ({len(messages)} reminder(s) removed)."
        return f"No alarm found at {key}."

    def list_alarms(self) -> str:
        """List all set alarms."""
        if not self.alarms:
            return "No alarms are currently set."
        parts = []
        for time_str, messages in self.alarms.items():
            for msg in messages:
                parts.append(f"  {time_str} — {msg}")
        return f"Your alarms:\n" + "\n".join(parts)

    def set_timer(self, minutes: float, message: str = "Timer done!") -> str:
        """Set a timer for N minutes."""
        try:
            minutes = float(minutes)
            if minutes <= 0:
                return "Timer must be a positive number of minutes."

            name = f"timer_{time.time()}"
            end_time = time.time() + (minutes * 60)
            self.timers[name] = {"end_time": end_time, "message": message, "done": False}

            threading.Thread(target=self._timer_thread, args=(name, minutes * 60, message), daemon=True).start()

            if minutes >= 60:
                hours = int(minutes // 60)
                mins = int(minutes % 60)
                duration = f"{hours} hour(s) and {mins} minute(s)"
            else:
                duration = f"{int(minutes)} minute(s)"

            return f"Timer set for {duration}. I'll remind you with: \"{message}\""
        except ValueError:
            return "Invalid timer duration. Please provide a number of minutes."

    def _timer_thread(self, name: str, seconds: float, message: str):
        """Wait and trigger timer."""
        time.sleep(seconds)
        if name in self.timers and not self.timers[name]["done"]:
            self.timers[name]["done"] = True
            print(f"[Haven] ⏱️  TIMER: {message}")

    def cancel_timer(self) -> str:
        """Cancel all active timers."""
        active = [k for k, v in self.timers.items() if not v["done"]]
        if not active:
            return "No active timers to cancel."
        for k in active:
            self.timers[k]["done"] = True
        return f"Cancelled {len(active)} timer(s)."

    def set_reminder(self, minutes: float, message: str) -> str:
        """Set a reminder for N minutes from now."""
        try:
            minutes = float(minutes)
            if minutes <= 0:
                return "Reminder time must be a positive number of minutes."

            name = f"reminder_{time.time()}"
            end_time = time.time() + (minutes * 60)
            self.reminders[name] = {"time": end_time, "message": message, "done": False}

            threading.Thread(target=self._reminder_thread, args=(name, minutes * 60, message), daemon=True).start()

            if minutes >= 60:
                hours = int(minutes // 60)
                mins = int(minutes % 60)
                duration = f"{hours} hour(s) and {mins} minute(s)"
            else:
                duration = f"{int(minutes)} minute(s)"

            return f"Reminder set for {duration} from now: \"{message}\""
        except ValueError:
            return "Invalid time. Please provide a number of minutes."

    def _reminder_thread(self, name: str, seconds: float, message: str):
        """Wait and trigger reminder."""
        time.sleep(seconds)
        if name in self.reminders and not self.reminders[name]["done"]:
            self.reminders[name]["done"] = True
            print(f"[Haven] 📝 REMINDER: {message}")

    def get_status(self) -> dict:
        """Return status of all clock tools."""
        active_timers = {k: v for k, v in self.timers.items() if not v["done"]}
        active_reminders = {k: v for k, v in self.reminders.items() if not v["done"]}
        return {
            "alarms": len(self.alarms),
            "active_timers": len(active_timers),
            "active_reminders": len(active_reminders),
        }
