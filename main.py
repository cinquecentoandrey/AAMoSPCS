import simpy
import random

PART_A_ARRIVAL_MEAN = 5
PART_A_ARRIVAL_DEV = 2
PART_A_BATCH = 500

PART_B_ARRIVAL_MEAN = 20
PART_B_ARRIVAL_DEV = 5
PART_B_BATCH = 2000

CAR_ARRIVAL_MEAN = 10
CAR_ARRIVAL_DEV = 5

LOADING_TIME_MEAN = 10
LOADING_TIME_DEV = 2

CAR_CAPACITY = 1000
MAX_CARS_AT_WAREHOUSE = 3
TARGET_CARS = 50

cars_left_without_load = 0
cars_served = 0
part_a_on_warehouse = []
part_b_on_warehouse = []


def supplier(env, warehouse, part_type, mean, dev, batch_size):
    while True:
        supply_time = env.timeout(max(0, int(random.gauss(mean, dev))))
        yield supply_time
        warehouse[part_type] += batch_size
        if part_type == 'A':
            part_a_on_warehouse.append(warehouse['A'])
        else:
            part_b_on_warehouse.append(warehouse['B'])


def car(env, warehouse, dock, car_id, end_event):
    global cars_left_without_load, cars_served

    while True:
        arrival_time = max(0, int(random.gauss(CAR_ARRIVAL_MEAN, CAR_ARRIVAL_DEV)))
        yield env.timeout(arrival_time)

        print(f"Машина {car_id} прибыла на склад в момент времени {env.now}.")
        with dock.request() as request:
            if len(dock.queue) >= MAX_CARS_AT_WAREHOUSE - 1:
                print(f"Машина {car_id} уезжает без груза: нет места.")
                cars_left_without_load += 1
                continue
            yield request

            if warehouse['A'] >= CAR_CAPACITY and warehouse['B'] >= CAR_CAPACITY:
                warehouse['A'] -= CAR_CAPACITY
                warehouse['B'] -= CAR_CAPACITY
                print(f"Машина {car_id} загружается в момент времени {env.now}.")
                fill_time = env.timeout(max(0, int(random.gauss(LOADING_TIME_MEAN, LOADING_TIME_DEV))))
                yield fill_time
                print(f"Машина {car_id} завершила загрузку в момент времени {env.now}.")
                cars_served += 1
                if cars_served >= TARGET_CARS:
                    end_event.succeed()
                    return
            else:
                print(f"Машина {car_id} уезжает без груза: недостаточно товаров.")
                cars_left_without_load += 1


if __name__ == "__main__":
    random.seed(42)
    env = simpy.Environment()

    warehouse = {'A': 0, 'B': 0}

    dock = simpy.Resource(env, capacity=1)

    end_event = env.event()

    env.process(supplier(env, warehouse, 'A', PART_A_ARRIVAL_MEAN, PART_A_ARRIVAL_DEV, PART_A_BATCH))
    env.process(supplier(env, warehouse, 'B', PART_B_ARRIVAL_MEAN, PART_B_ARRIVAL_DEV, PART_B_BATCH))

    for car_id in range(TARGET_CARS):
        env.process(car(env, warehouse, dock, car_id, end_event))

    env.run(until=end_event)

    avg_part_a = sum(part_a_on_warehouse) / len(part_a_on_warehouse) if part_a_on_warehouse else 0
    avg_part_b = sum(part_b_on_warehouse) / len(part_b_on_warehouse) if part_b_on_warehouse else 0
    max_part_a = max(part_a_on_warehouse, default=0)
    max_part_b = max(part_b_on_warehouse, default=0)

    print("Результаты моделирования:")
    print(f"Число автомобилей, уехавших без груза: {cars_left_without_load}")
    print(f"Число обслуженных автомобилей: {cars_served}")
    print(f"Среднее количество изделий типа A на складе: {avg_part_a:.2f}")
    print(f"Среднее количество изделий типа B на складе: {avg_part_b:.2f}")
    print(f"Максимальное количество изделий типа A на складе: {max_part_a}")
    print(f"Максимальное количество изделий типа B на складе: {max_part_b}")
