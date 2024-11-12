import csv
import json
import os.path
from pprint import pprint
from common import DATA_DIR

nutrients_json_file = os.path.join(DATA_DIR, 'nutrients_in_food.json')
first_foods_file = os.path.join(DATA_DIR, 'first_foods.json')
nutrients_units_file = os.path.join(DATA_DIR, 'nutrients_units.json')
nutrients_csv_file = os.path.join(DATA_DIR, 'nutrients_in_food.csv')

# List comprehension
def list_comprehension():
    calories = [{'food': 'tomatoes', 'energy': 100},
                {'food': 'apples', 'energy': 200}]
    
    names_1 = []
    for food in calories:
        new_name = food['food']
        names_1.append(new_name)
    
    names_2 = []
    for food in calories:
        names_2.append(food['food'])

    names_3 = [
        food['food']
        for food in calories
    ]

def dict_comprehension():
    calories = [{'food': 'tomatoes', 'energy': 100},
                {'food': 'apples', 'energy': 200}]
    
    # Desired output:
    # {'tomatoes': 100, 'apples': 200}
    
    names_1 = {}
    for food in calories:
        new_name = food['food']
        new_value = food['energy']
        names_1[new_name] = new_value
    
    names_2 = {}
    for food in calories:
        names_2[food['food']] = food['energy']

    names_3 = {
        food['food']: food['energy']
        for food in calories
    }

def explore():
    with open(nutrients_json_file, encoding='utf-8') as f:
        nutrients = json.load(f)['FoundationFoods']
    first_foods = nutrients[:4]
    with open(first_foods_file, 'w') as f:
        json.dump(first_foods, f, indent=4)
    


    nutrient_units = {
        food_nutrient['nutrient']['name'] : food_nutrient['nutrient']['unitName']
        for food_nutrient in first_foods[0]['foodNutrients']
    }
    with open(nutrients_units_file, 'w', encoding='utf-8') as f:
        json.dump(nutrient_units, f, indent=4)


def convert_json_to_csv():
    nutrients_to_keep = {
        1165: 'B2', # Thiamin
        1166: 'B3', # Riboflavin
        2048: 'kCal', # Energy (Atwater Specific Factors)
        1008: 'kCal', # Energy
    }

    with open(nutrients_json_file) as f:
        nutrients = json.load(f)['FoundationFoods']
    
    header = ['Food', 'FoodCategory'] + list(nutrients_to_keep.values())
    result = []
    for food in nutrients:
        line = {
            'Food': food['description'],
            'FoodCategory': food['foodCategory']['description']
        }
        for food_nutrient in food['foodNutrients']:
            nutrient_id_in_json = food_nutrient['nutrient']['id']
            if nutrient_id_in_json not in nutrients_to_keep:
                # Continue with the next iteration of the for-loop
                # So we don't execute the following lines for this nutrient to store it 
                continue
            nutrient_name_in_csv = nutrients_to_keep[nutrient_id_in_json]
            line[nutrient_name_in_csv] = food_nutrient['amount']
        result.append(line)
    
    with open(nutrients_csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=header, delimiter=';')
        writer.writeheader()
        for row in result:
            writer.writerow(row)
            

if __name__ == '__main__':
    explore()
    convert_json_to_csv()
