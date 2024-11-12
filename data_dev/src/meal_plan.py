import csv
import os.path

from common import DATA_DIR

nutrients_in_food_file = os.path.join(DATA_DIR, 'nutrients_in_food.csv')


def get_nutrients_in_food():
    with open(nutrients_in_food_file, encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        nutrients_in_food = {row['Food']: row for row in reader}
    return nutrients_in_food


def get_nr_foods_per_category():
    """
    Return the number of foods in each category

    :return: Dictionary in the following format
    {
        'Baked Products': 3,
        'Beef Products': 12,
        ...
        'Sweets': 1,
        'Vegetables and Vegetable Products': 67
     }
    """

    nutrients_in_food = get_nutrients_in_food()
    categories = {row['FoodCategory'] for row in nutrients_in_food.values()}
    return {
        category: sum(1 for row in nutrients_in_food.values() if row['FoodCategory'] == category)
        for category in categories
    }


def nutrients_for_meal_plan(meal_plan):
    """
    Calculate the total nutrients in a meal plan

    :param meal_plan: Dictionary in this format:
    {
        'Hummus, commercial': 100,
        'Onion rings, breaded, par fried, frozen, prepared, heated in oven': 50,
    }
    Note: the names must be exactly the same as in nutrients_in_food.csv

    :return: Dictionary in this format:
    {
        'B2': 0.248,
        'B3': 0.173,
        'kCal': 373.0
    }
    """

    nutrients_in_food = get_nutrients_in_food()
    total_nutrients = {}
    for meal_component, meal_component_weight in meal_plan.items():
        nutrients = nutrients_in_food[meal_component]
        for nutrient, nutrient_value in nutrients.items():
            if nutrient == 'Food' or nutrient == 'FoodCategory':
                continue
            nutrient_value = float(nutrient_value or '0')
            total_nutrients[nutrient] = total_nutrients.get(nutrient, 0) + nutrient_value * meal_component_weight / 100
    return total_nutrients


def generate_meal_plan():
    constraints = {
        'Baked Products': 100,
        'Beef Products': 30,
        'Beverages': 0,
        'Cereal Grains and Pasta': 250,
        'Dairy and Egg Products': 40,
        'Fats and Oils': 20,
        'Finfish and Shellfish Products': 40,
        'Fruits and Fruit Juices': 200,
        'Legumes and Legume Products': 200,
        'Nut and Seed Products': 100,
        'Pork Products': 10,
        'Poultry Products': 30,
        'Restaurant Foods': 0,
        'Sausages and Luncheon Meats': 20,
        'Soups, Sauces, and Gravies': 20,
        'Spices and Herbs': 10,
        'Sweets': 10,
        'Vegetables and Vegetable Products': 300
    }

    nutrients_in_food = get_nutrients_in_food()
    nr_foods_per_category = get_nr_foods_per_category()

    meal_plan = {}
    for food, nutrients in nutrients_in_food.items():
        category = nutrients['FoodCategory']
        if constraints[category] > 0:
            meal_plan[food] = constraints[category] / nr_foods_per_category[category]
    return meal_plan


def compare_meal_plan_to_reference(meal_plan, reference=None):
    """

    :param meal_plan: Dictionary in this format:
    {
        'Hummus, commercial': 100,
        'Onion rings, breaded, par fried, frozen, prepared, heated in oven': 50,
    }
    :param reference: This should come from the micronutrient recommendations per gender / age / condition
    :return: Dictionary in this format:
    {
        'B2': 5.191686821056804,
        'B3': 5.561313606918105,
        'kCal': -0.4424807504346418
    }
    """

    if not reference:
        # Hardcode a single reference for now
        reference = {
            'B2': 0.3,
            'B3': 0.2,
            'kCal': 2000
        }

    total_nutrients = nutrients_for_meal_plan(meal_plan)
    relative_differences = {
        nutrient: (total_nutrients[nutrient] - reference[nutrient]) / reference[nutrient]
        for nutrient in reference
    }
    return relative_differences


if __name__ == '__main__':
    meal_plan_based_on_constraints = generate_meal_plan()

    print('Nutrients for this meal plan:')
    nutrients_for_this_meal_plan = nutrients_for_meal_plan(meal_plan_based_on_constraints)
    for key, value in nutrients_for_this_meal_plan.items():
        print(f'-> {key}: {value:.2f}')

    print('Relative differences to reference:')
    differences = compare_meal_plan_to_reference(meal_plan_based_on_constraints)
    for key, value in differences.items():
        sign = '+' if value > 0 else ''
        print(f'-> {key}: {sign}{value:.0%}')
