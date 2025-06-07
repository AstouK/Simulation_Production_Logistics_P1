import simpy

from .config import SIM_TIME, START_OF_DAY, WORKDAY_MINUTES
from .helpers import format_time
from .laundry_process import safe_timeout

# Employees
class Employee:
    def __init__(self, env, name, break_start):
        self.env = env
        self.name = name
        self.break_start = break_start
        self.resource = simpy.Resource(env, capacity=1)
        self.available = True
        self.action = env.process(self.manage_presence())

    def manage_presence(self):
        while self.env.now < SIM_TIME:
            today = int(self.env.now // (24 * 60))
            start = today * 24 * 60 + START_OF_DAY

            if self.env.now < start:
                yield from safe_timeout(self.env, start - self.env.now)

            self.available = True
            break_time = today * 24 * 60 + self.break_start

            if self.env.now < break_time:
                yield from safe_timeout(self.env, break_time - self.env.now)

            self.available = False
            print(f"[{format_time(self.env.now)}] {self.name} is on break.")
            yield from safe_timeout(self.env, 30)
            print(f"[{format_time(self.env.now)}] {self.name} returns from break.")
            self.available = True

            end = start + WORKDAY_MINUTES
            if self.env.now < end:
                yield from safe_timeout(self.env, end - self.env.now)