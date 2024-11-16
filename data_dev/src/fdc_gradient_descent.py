import csv
import os.path

import numpy as np

from data_dev.src.common import DATA_DIR
from data_dev.src.gradient_descent import gradient_descent


class FdcGradientDescent:
    def __init__(self, food_nutrients_file: str):
        """
        :param food_nutrients_file: Full path to the file containing the nutrients in food
        """

        with open(food_nutrients_file, encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';')
            self.file_contents: list[list[str]] = [row for row in reader]

    def prepare_data(self):
        # Remove the header and the first two columns
        food_nutrients = self.file_contents[1:]
        food_nutrients = [row[2:] for row in food_nutrients]

        # Convert the values to floats. Fill in 0 if the value is missing
        food_nutrients = [[float(value) if value else 0
                           for value in row]
                          for row in food_nutrients]

        # Convert to numpy array
        food_nutrients = np.array(food_nutrients)

        # Get the optimal nutrients array
        optimal_nutrients = {
            'Protein': 50,  # g
            'Energy': 2000,  # kCal
            'Fiber, total dietary': 20,  # g
            'Calcium, Ca': 1,  # mg
            'Magnesium, Mg': 1,  # mg
            'Vitamin C, total ascorbic acid': 1,  # mg
            'Vitamin B-6': 1,  # mg
            'Vitamin B-12': 1  # ug
        }
        optimal_nutrients = np.array([optimal_nutrients[nutrient] for nutrient in self.file_contents[0][2:]])

        meal_plan = gradient_descent(
            A=food_nutrients,
            optimal_nutrients=optimal_nutrients,
            learning_rate=1E-5,
            max_iterations=10_000,
            tolerance=1E-5
        )

        print(meal_plan)


if __name__ == '__main__':
    path_to_input_file = os.path.join(DATA_DIR, 'fdc_data', 'food_nutrients_short.csv')
    fdc = FdcGradientDescent(path_to_input_file)
    fdc.prepare_data()
