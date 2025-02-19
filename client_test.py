import json

demo_dict = {
    '111222333': {'x': 1, 'y': 2},
    '444555666': {'x': 3, 'y': 4},
    '777888999': {'x': 5, 'y': 6}
}

demo_json = json.dumps(demo_dict)
print(demo_json)
print(type(demo_json))