import simpy
import numpy as np
import random
import pandas as pd

from .config import START_OF_DAY, laundry_types
from .helpers import format_time, parse_duration

# Ensure nothing happens outside of operating hours
def safe_timeout(env, duration):
    now = env.now
    closing = (now // (24 * 60)) * 24 * 60 + 17 * 60  # 17:00 daily closing

    current_day = int(now // (24 * 60))
    day_of_week = current_day % 7
    if day_of_week >= 5:
        # weekend start time
        weekend_start = (current_day // 7) * 7 * 24 * 60 + 5 * 24 * 60 + START_OF_DAY
        if now < weekend_start:
            closing = min(closing, weekend_start)  # close at weekend start

    next_open = None
    if day_of_week >= 5:
        # next Monday 08:00
        next_open = ((current_day // 7) + 1) * 7 * 24 * 60 + START_OF_DAY
    else:
        # next day 08:00
        next_open = ((current_day) + 1) * 24 * 60 + START_OF_DAY

    end_time = now + duration
    if end_time <= closing:
        yield env.timeout(duration)
    else:
        time_until_close = closing - now
        remaining = duration - time_until_close
        yield env.timeout(time_until_close)
        print(f"[{format_time(env.now)}] ⏸ Paused (end of day/week). Resuming next working day...")
        yield env.timeout(next_open - env.now)
        print(f"[{format_time(env.now)}] ▶️ Resuming operation...")
        yield env.timeout(remaining)
        
# Detergent management
class DetergentManager:
    def __init__(self, env):
        self.env = env
        self.stock = 1000
        self.restock_pending = False

    def use(self, amount):
        self.stock -= amount
        if self.stock < 180 and not self.restock_pending:
            self.restock_pending = True
            self.env.process(self.restock())

    def restock(self):
        print(f"[{format_time(self.env.now)}] 🚚 Ordering detergent pack...")
        yield from safe_timeout(self.env, 240)
        self.stock += 1000
        self.restock_pending = False
        print(f"[{format_time(self.env.now)}] 📦 New detergent pack arrived. Stock = {self.stock}g")

# Laundry load
class LaundryLoad:
    def __init__(self, env, client_id, basket_id, laundry_type):
        self.env = env
        self.client_id = client_id
        self.basket_id = basket_id
        self.laundry_type = laundry_type
        self.arrival_time = env.now

# Laundry Process/stages
class LaundryFacility:
    def __init__(self, env, employees):
        self.env = env
        self.employees = employees
        self.washers = simpy.Resource(env, capacity=4)
        self.dryers = simpy.Resource(env, capacity=2)
        self.special_dryer = simpy.Resource(env, capacity=1)
        self.detergent = DetergentManager(env)
        self.wash_queue = simpy.Store(env)
        self.dry_queue = simpy.Store(env)
        self.special_dryer_queue = simpy.Store(env)
        self.iron_queue = simpy.Store(env)
        env.process(self.wash_dispatcher())
        env.process(self.dry_dispatcher())
        env.process(self.special_dry_dispatcher())
        env.process(self.iron_dispatcher())

    def enqueue(self, load):
        self.wash_queue.put(load)

    def get_employee(self):
        for emp in self.employees:
            if emp.available and emp.resource.count == 0:
                return emp
        return None

    def wash_dispatcher(self):
        while True:
            load = yield self.wash_queue.get()
            self.env.process(self.washing(load))

    def dry_dispatcher(self):
        while True:
            load = yield self.dry_queue.get()
            self.env.process(self.drying(load))

    def special_dry_dispatcher(self):
        while True:
            load = yield self.special_dryer_queue.get()
            self.env.process(self.drying(load, special=True))

    def iron_dispatcher(self):
        while True:
            load = yield self.iron_queue.get()
            self.env.process(self.ironing(load))

    def washing(self, load):
        with self.washers.request() as req:
            yield req
            emp = None
            while emp is None:
                emp = self.get_employee()
                if emp is None:
                    yield from safe_timeout(self.env, 1)
            with emp.resource.request() as ereq:
                yield ereq
                emp.available = False
                print(f"[{format_time(self.env.now)}] {emp.name} loads Basket {load.basket_id} in washing machine and adds detergent")
                yield from safe_timeout(self.env, random.triangular(2, 5, 10))
                self.detergent.use(20)
                wash_duration = parse_duration(laundry_types.loc[laundry_types["Type"] == load.laundry_type, "Washing Time"].values[0])
                print(f"[{format_time(self.env.now)}] Washing starts for Basket {load.basket_id} (Duration: {wash_duration} min)")
                yield from safe_timeout(self.env, wash_duration)
                print(f"[{format_time(self.env.now)}] {emp.name} unloads Basket {load.basket_id}")
                emp.available = True
        if load.laundry_type.lower() == 'wool':
            self.special_dryer_queue.put(load)
        else:
            self.dry_queue.put(load)

    def drying(self, load, special=False):
        dryer = self.special_dryer if special else self.dryers
        with dryer.request() as req:
            yield req
            emp = None
            while emp is None:
                emp = self.get_employee()
                if emp is None:
                    yield from safe_timeout(self.env, 1)
            with emp.resource.request() as ereq:
                yield ereq
                emp.available = False
                machine = "SPECIAL" if special else "STANDARD"
                print(f"[{format_time(self.env.now)}] {emp.name} loads Basket {load.basket_id} in {machine} dryer")
                yield from safe_timeout(self.env, random.triangular(2, 5, 10))
                dry_duration = parse_duration(laundry_types.loc[laundry_types["Type"] == load.laundry_type, "Drying Time"].values[0])
                print(f"[{format_time(self.env.now)}] Drying starts for Basket {load.basket_id} (Duration: {dry_duration} min)")
                yield from safe_timeout(self.env, dry_duration)
                print(f"[{format_time(self.env.now)}] {emp.name} unloads Basket {load.basket_id}")
                emp.available = True
        self.iron_queue.put(load)

    def ironing(self, load):
        if load.laundry_type.lower() in ['boil-wash', 'colored wash']:
            emp = None
            while emp is None:
                emp = self.get_employee()
                if emp is None:
                    yield from safe_timeout(self.env, 1)
            with emp.resource.request() as req:
                yield req
                emp.available = False
                iron_duration = random.gammavariate(40, 0.4)
                print(f"[{format_time(self.env.now)}] Ironing starts for Basket {load.basket_id} (Duration: {iron_duration:.1f} min)")
                yield from safe_timeout(self.env, iron_duration)
                emp.available = True
