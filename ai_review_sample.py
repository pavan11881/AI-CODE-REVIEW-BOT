def calculate_average(total, count):
    if count == 0:
        raise ValueError("Cannot calculate average with zero items")
    return total / count


def get_item(items, index):
    return items[index]


total = 100
count = 10

print("Average:", calculate_average(total, count))

items = [10, 20, 30]
print("Item:", get_item(items, 5))