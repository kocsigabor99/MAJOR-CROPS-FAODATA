import pandas as pd
import streamlit as st

# Correct the file paths
file_path_requirements = r'C:\Users\kocsi\OneDrive\Asztali gép\ACT PROJ\1 FIND JOB 4 DAYS, (+IMPACT (EA UNI CHAPTER) + VOLUNTEER 1 DAY)\00 PLANT JOB\SUPPORT MATERIALS\ARTICLE 43 NUTRITION FOR EVERYONE\CSV\GROUPED MICRONUTRIENTS\GROUPSMicronutrient Needs by single year Pregnant and Breastfeeding included.csv'
file_path_foods = r'C:\Users\kocsi\OneDrive\Asztali gép\ACT PROJ\1 FIND JOB 4 DAYS, (+IMPACT (EA UNI CHAPTER) + VOLUNTEER 1 DAY)\00 PLANT JOB\SUPPORT MATERIALS\ARTICLE 43 NUTRITION FOR EVERYONE\CSV\food_nutrientNEW3.csv'

# Load the data
nutritional_requirements = pd.read_csv(file_path_requirements)
food_nutrients = pd.read_csv(file_path_foods)

# Function to get nutritional requirements based on user input
def get_nutritional_requirements(gender, age_group, condition):
    condition_filter = (nutritional_requirements['Gender'] == gender) & (nutritional_requirements['Age'] == age_group)
    if condition:
        condition_filter &= (nutritional_requirements['Breastfeeding/Pregnant'] == condition)
    return nutritional_requirements[condition_filter]

# Function to calculate the total nutrient content of a meal plan
def calculate_nutrient_totals(meal_plan, food_nutrients):
    totals = {}
    for food, grams in meal_plan.items():
        food_data = food_nutrients[food_nutrients['Food'] == food]
        for _, row in food_data.iterrows():
            nutrient = row['Nutrient']
            amount = row['amount'] * (grams / 100)
            if nutrient in totals:
                totals[nutrient] += amount
            else:
                totals[nutrient] = amount
    return totals

# Function to generate a meal plan based on stipulations and nutritional needs
def generate_meal_plan(num_people, food_nutrients):
    # Define stipulations
    stipulations = {
        "Grains": (250, 20),
        "Fruits": (200, 9),
        "Vegetables": (300, 11),
        "Beans": (200, 16),
        "Nuts": (100, 12)
    }

    meal_plan = {}

    for food_type, (min_amount, category_id) in stipulations.items():
        # Filter foods by category
        foods_in_category = food_nutrients[food_nutrients['Category'] == category_id]

        # Select foods to meet the minimum amount requirement
        selected_foods = foods_in_category.sample(frac=1).reset_index(drop=True)  # Shuffle foods
        total_amount = 0

        for _, food in selected_foods.iterrows():
            food_name = food['Food']
            remaining_amount = min_amount - total_amount

            if remaining_amount <= 0:
                break

            if food_name in meal_plan:
                meal_plan[food_name] += remaining_amount
            else:
                meal_plan[food_name] = remaining_amount

            total_amount += remaining_amount

    # Scale the meal plan for the number of people
    meal_plan = {food: grams * num_people for food, grams in meal_plan.items()}

    return meal_plan

# Streamlit UI
st.title("Meal Plan Generator")

# User inputs
num_people = st.number_input("Number of people", min_value=1, step=1)
gender = st.selectbox("Gender", ["Male", "Female"])
age_group = st.selectbox("Age Group", nutritional_requirements['Age'].unique())
condition = st.selectbox("Condition", ["None", "Pregnant", "Breastfeeding"])

# Get the nutritional requirements for the selected group
nutritional_needs = get_nutritional_requirements(gender, age_group, condition if condition != "None" else None)

# Display nutritional needs
st.write("Nutritional needs for one person:")
st.write(nutritional_needs)

# Generate meal plan
if st.button("Generate Meal Plan"):
    # Generate a meal plan that meets the stipulations
    meal_plan = generate_meal_plan(num_people, food_nutrients)
    
    # Calculate total nutrient content of the meal plan
    nutrient_totals = calculate_nutrient_totals(meal_plan, food_nutrients)
    
    st.write("Generated Meal Plan:")
    for food, amount in meal_plan.items():
        st.write(f"{food}: {amount}g")

    st.write("Nutrient Totals in Meal Plan:")
    st.write(nutrient_totals)

    # Check if the meal plan meets the nutritional needs
    st.write("Does the meal plan meet the nutritional needs?")
    for nutrient, required_amount in nutritional_needs.iloc[0].items():
        if nutrient in nutrient_totals:
            if nutrient_totals[nutrient] >= required_amount * num_people:
                st.write(f"{nutrient}: Yes")
            else:
                st.write(f"{nutrient}: No")
        else:
            st.write(f"{nutrient}: Not available in the selected foods")
