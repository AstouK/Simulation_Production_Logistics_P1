import simpy
import numpy as np
import random

from .config import SIM_TIME, START_OF_DAY, laundry_types
from .helpers import format_time
from .laundry_process import LaundryLoad

# Pre-sort basket
def pre_sort_basket(env, client_id, basket_id, facility):
    """Pre-sort a basket before it is processed."""
    laundry_type = np.random.choice(laundry_types['Type'], p=laundry_types['Share'])
    load = LaundryLoad(env, client_id, basket_id, laundry_type)
    facility.enqueue(load)

# Clients
def client1_arrivals(env, facility):
    basket_id = 10000

    while env.now < SIM_TIME:
        current_day = int(env.now // (24 * 60))
        day_of_week = current_day % 7
        if day_of_week >= 5:  # weekend, skip to Monday
            next_monday = ((current_day // 7) + 1) * 7 * 24 * 60 + START_OF_DAY
            print(f"[{format_time(env.now)}] ❌ Client 1 skips weekend delivery")
            yield env.timeout(next_monday - env.now)
            continue
        # Wait until start of day (8:00 AM)
        today_start = (env.now // (24 * 60)) * 24 * 60 + START_OF_DAY
        if env.now < today_start:
            yield env.timeout(today_start - env.now)

        # First delivery at 08:00 (6–8 baskets)
        baskets = random.randint(6, 8)
        print(f"[{format_time(env.now)}] 📦 Client 1 delivers {baskets} baskets.")
        for _ in range(baskets):
            basket_id += 1
            print(f"[{format_time(env.now)}] 📦 Client 1 delivers Basket {basket_id} (First Morning Delivery)")
            pre_sort_basket(env, 1, basket_id, facility)

        # Second delivery: 1–3 baskets between 08:30 and 12:00
        delivery_time = today_start + 240  # at 12:00
        yield env.timeout(delivery_time - env.now)

        extra_baskets = random.randint(1, 3)
        print(f"[{format_time(env.now)}] 📦 Client 1 delivers {extra_baskets} baskets ")
        for _ in range(extra_baskets):
            basket_id += 1
            print(f"[{format_time(env.now)}] 📦 Client 1 delivers Basket {basket_id} (Second Morning Delivery)")
            pre_sort_basket(env, 1, basket_id, facility)

        # Then move to next day start
        next_day = (current_day + 1) * 24 * 60 + START_OF_DAY
        yield env.timeout(next_day - env.now)

def client2_arrivals(env, facility):
    basket_id = 20000
    while env.now < SIM_TIME:
        current_day = int(env.now // (24 * 60))
        day_of_week = current_day % 7
        if day_of_week >= 5:  # weekend, skip to Monday
            next_monday = ((current_day // 7) + 1) * 7 * 24 * 60 + START_OF_DAY
            print(f"[{format_time(env.now)}] ❌ Client 2 skips weekend delivery")
            yield env.timeout(next_monday - env.now)
            continue

        day_start = (env.now // (24 * 60)) * 24 * 60 + START_OF_DAY
        noon = day_start + 4 * 60  # 12:00 PM

        if env.now < day_start:
            yield env.timeout(day_start - env.now)

        # First delivery at 8:00 exactly (or shortly after)
        first_delivery_time = day_start + random.randint(0, 180)  # between 8:00 and 11:00
        yield env.timeout(first_delivery_time - env.now)
        first_baskets = random.randint(3, 5)
        print(f"[{format_time(env.now)}] 📦 Client 2 delivers {first_baskets} baskets (First Delivery)")
        for _ in range(first_baskets):
            basket_id += 1
            print(f"[{format_time(env.now)}] 📦 Client 2 delivers Basket {basket_id}")
            pre_sort_basket(env, 2, basket_id, facility)

        # Wait for exponentially distributed time gap (mean 60 min)
        gap = np.random.exponential(scale=60)
        # Cap the gap so second delivery doesn't exceed noon
        max_gap = noon - env.now
        gap = min(gap, max_gap) if max_gap > 0 else 0

        yield env.timeout(gap)

        # Second delivery happens after gap but before noon
        if env.now <= noon:
            second_baskets = random.randint(2, 4)
            print(f"[{format_time(env.now)}] 📦 Client 2 delivers {second_baskets} baskets (Second Delivery)")
            for _ in range(second_baskets):
                basket_id += 1
                print(f"[{format_time(env.now)}] 📦 Client 2 delivers Basket {basket_id}")
                pre_sort_basket(env, 2, basket_id, facility)
        else:
            print(f"[{format_time(env.now)}] ❌ Client 2 missed second delivery window today")

        # Then move to next day start
        next_day = (current_day + 1) * 24 * 60 + START_OF_DAY
        yield env.timeout(next_day - env.now)