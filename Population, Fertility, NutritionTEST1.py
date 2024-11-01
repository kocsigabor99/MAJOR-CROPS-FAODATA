import pandas as pd

# Define the URLs
url_female = "https://raw.githubusercontent.com/kocsigabor99/MAJOR-CROPS-FAODATA/main/UN_PPP2022_Forecast_PopulationBySingleAge_Female.csv"
url_male = "https://raw.githubusercontent.com/kocsigabor99/MAJOR-CROPS-FAODATA/main/UN_PPP2022_Forecast_PopulationBySingleAge_Male.csv"

# Read the CSV files into DataFrames
df_female = pd.read_csv(url_female)
df_male = pd.read_csv(url_male)

# Add a column to identify gender
df_female['Gender'] = 'Female'
df_male['Gender'] = 'Male'

# Merge the DataFrames
df_merged = pd.concat([df_female, df_male], ignore_index=True)

# Display the merged DataFrame
df_merged.head()

# Load the birth rate data
birth_rate_url = 'https://raw.githubusercontent.com/kocsigabor99/MAJOR-CROPS-FAODATA/refs/heads/main/UN_PPP2024_Output_Birth%20rate_Single_Year_per_1000_women.csv'

# Load the birth rate data with low_memory=False to avoid DtypeWarning
birth_rate_df = pd.read_csv(birth_rate_url, low_memory=False)

# Convert all columns except 'Year' and 'Region, subregion, country or area' to numeric, handling errors
for col in birth_rate_df.columns[2:]:
    birth_rate_df[col] = pd.to_numeric(birth_rate_df[col], errors='coerce')

# Drop rows with missing or non-numeric values in the birth rate columns
birth_rate_df = birth_rate_df.dropna(subset=birth_rate_df.columns[2:])

# Merge birth rate data with population data based on 'Year' and 'Region, subregion, country or area'
merged_df = pd.merge(df_female, birth_rate_df, on=['Year', 'Region, subregion, country or area'], suffixes=('', '_y'), how='inner')

# Calculate the number of births for each age group
for age in range(10, 55):  # Assuming age ranges from 10 to 54
    age_str = str(age)
    birth_rate_col = f'{age_str}_y'
    if age_str in merged_df.columns and birth_rate_col in merged_df.columns:
        merged_df[f'Births_{age}'] = merged_df[age_str] * merged_df[birth_rate_col]

# Sum up the number of births across all age groups to get total births
birth_columns = [f'Births_{age}' for age in range(10, 55) if f'Births_{age}' in merged_df.columns]
merged_df['Total_Births'] = merged_df[birth_columns].sum(axis=1)

# Calculate the number of pregnant women per single age group
pregnant_cols = {
    f'Pregnant_{age}': merged_df[f'Births_{age}'] 
    for age in range(10, 55) 
    if f'Births_{age}' in merged_df.columns
}

# Extrapolate for pregnant teens aged 9 based on births in age 10
if 'Births_10' in merged_df.columns:
    pregnant_cols['Pregnant_9'] = merged_df['Births_10']

# Calculate the number of breastfeeding women per single age group
breastfeeding_cols = {
    f'Breastfeeding_{age}': merged_df[f'Births_{age-2}'] + merged_df[f'Births_{age-1}']
    for age in range(12, 57)
    if f'Births_{age-2}' in merged_df.columns and f'Births_{age-1}' in merged_df.columns
}

# Special cases for ages 10 and 11
if 'Births_10' in merged_df.columns:
    breastfeeding_cols['Breastfeeding_10'] = merged_df['Births_10']
if 'Births_10' in merged_df.columns and 'Births_11' in merged_df.columns:
    breastfeeding_cols['Breastfeeding_11'] = merged_df['Births_10'] + merged_df['Births_11']

# Calculate 'Breastfeeding_56' as the difference between 'Breastfeeding_55' and 'Births_53'
if 'Breastfeeding_55' in breastfeeding_cols and 'Births_53' in merged_df.columns:
    breastfeeding_cols['Breastfeeding_56'] = breastfeeding_cols['Breastfeeding_55'] - merged_df['Births_53']

# Create a new DataFrame with these columns
new_cols = {**pregnant_cols, **breastfeeding_cols}
new_df = pd.DataFrame(new_cols)

# Concatenate the new DataFrame with the original DataFrame
merged_df = pd.concat([merged_df, new_df], axis=1)

# Optionally, save the updated DataFrame to a new CSV file
merged_df.to_csv('updated_birth_data.csv', index=False)

# Getting pregnant during breastfeeding years is not accounted for 
# 2. Subtract the numbers in the 'Pregnant_10' to 'Pregnant_54' columns from the corresponding female single age groups
pregnant_columns = {f'Pregnant_{age}': age for age in range(9, 53)}
for col, age in pregnant_columns.items():
    merged_df[str(age)] -= merged_df[col] / 1000

# 3. Subtract the numbers in the 'Breastfeeding_10' to 'Breastfeeding_' columns from the corresponding female single age groups
breastfeeding_columns = {f'Breastfeeding_{age}': age for age in range(10, 57)}
for col, age in breastfeeding_columns.items():
    merged_df[str(age)] -= merged_df[col] / 1000

# Optionally, save the updated DataFrame to a new CSV file
merged_df.to_csv('updated_nutritional_data.csv', index=False)

rounded_df = merged_df.round(10)

# Create a copy of the DataFrame to apply scaling
scaled_df = rounded_df.copy()

# Define columns to scale (pregnant and breastfeeding columns)
columns_to_scale = [f'Pregnant_{age}' for age in range(9, 53)] + [f'Breastfeeding_{age}' for age in range(11, 56)]

# Scale the specified columns by dividing by 1000
scaled_df[columns_to_scale] /= 1000

# Columns to drop and save
columns_to_save = ['15_y', '16_y', '17_y', '18_y', '19_y', '20_y', '21_y', '22_y', '23_y', '24_y',
                   '25_y', '26_y', '27_y', '28_y', '29_y', '30_y', '31_y', '32_y', '33_y', '34_y',
                   '35_y', '36_y', '37_y', '38_y', '39_y', '40_y', '41_y', '42_y', '43_y', '44_y',
                   '45_y', '46_y', '47_y', '48_y', '49_y',
                   'Births_15', 'Births_16', 'Births_17', 'Births_18', 'Births_19', 'Births_20',
                   'Births_21', 'Births_22', 'Births_23', 'Births_24', 'Births_25', 'Births_26',
                   'Births_27', 'Births_28', 'Births_29', 'Births_30', 'Births_31', 'Births_32',
                   'Births_33', 'Births_34', 'Births_35', 'Births_36', 'Births_37', 'Births_38',
                   'Births_39', 'Births_40', 'Births_41', 'Births_42', 'Births_43', 'Births_44',
                   'Births_45', 'Births_46', 'Births_47', 'Births_48', 'Births_49']

# Create a new DataFrame to save the dropped columns
saved_data = scaled_df[columns_to_save].copy()

# Drop the columns from scaled_df
scaled_df.drop(columns_to_save, axis=1, inplace=True)

# Adjust the merge keys as per your actual column names
merge_keys = ['Region, subregion, country or area', 'Year',]

# Perform inner merge on the common keys
merged_data = pd.merge(scaled_df, df_male, on=merge_keys, suffixes=('_female', '_male'))

# Assuming merged_data is your DataFrame with the specified columns
merged_data = merged_data.drop(columns=['Gender_female', 'Gender_male'])

# Define the age group mappings
age_groups = {
    'Male': {
        '0': ['0_male'],
        '1-3': [f'{i}_male' for i in range(1, 4)],
        '4-8': [f'{i}_male' for i in range(4, 9)],
        '9-13': [f'{i}_male' for i in range(9, 14)],
        '14-18': [f'{i}_male' for i in range(14, 19)],
        '19-50': [f'{i}_male' for i in range(19, 51)],
        '51-70': [f'{i}_male' for i in range(51, 71)],
        '71-100+': [f'{i}_male' for i in range(71, 100)] + ['100+_male']
    },
    'Female': {
        '0': ['0_female'],
        '1-3': [f'{i}_female' for i in range(1, 4)],
        '4-8': [f'{i}_female' for i in range(4, 9)],
        '9-13': [f'{i}_female' for i in range(9, 14)],
        '14-18': [f'{i}_female' for i in range(14, 19)],
        '19-50': [f'{i}_female' for i in range(19, 51)],
        '51-70': [f'{i}_female' for i in range(51, 71)],
        '71-100+': [f'{i}_female' for i in range(71, 100)] + ['100+_female']
    },
    'Pregnant': {
        '9-19': [f'Pregnant_{i}' for i in range(9, 20)],
        '20-53': [f'Pregnant_{i}' for i in range(20, 54)]
    },
    'Breastfeeding': {
        '9-19': [f'Breastfeeding_{i}' for i in range(11, 20)],
        '20-56': [f'Breastfeeding_{i}' for i in range(20, 57)]
    }
}

# Create a list of columns to keep based on the age group mappings
columns_to_keep = ['Region, subregion, country or area', 'Year', 'Total_Births']

# Loop through the age group mappings to calculate and drop as needed
for category, groups in age_groups.items():
    for age_range, columns in groups.items():
        # Filter only the columns that exist in merged_data
        existing_columns = [col for col in columns if col in merged_data.columns]
        
        if existing_columns:
            # Aggregate columns for the current age group
            merged_data[f'{age_range}_{category}'] = merged_data[existing_columns].sum(axis=1)
            # Append to columns_to_keep for the final filtered DataFrame
            columns_to_keep.append(f'{age_range}_{category}')
            # Drop these columns after aggregation
            merged_data.drop(existing_columns, axis=1, inplace=True)

# Filter the DataFrame to keep only the desired columns
merged_data_filtered = merged_data[columns_to_keep]

# Load your data
url_nutritional = 'https://raw.githubusercontent.com/kocsigabor99/MAJOR-CROPS-FAODATA/refs/heads/main/GROUPS%7E1.CSV'
nutritional_df = pd.read_csv(url_nutritional)

# Initialize a dictionary to collect results
result_dict = {
    'Region, subregion, country or area': merged_data_filtered['Region, subregion, country or area'],
    'Year': merged_data_filtered['Year']
}

# Function to add nutrient data to the result_dict
def add_nutrient_data(age_group, gender, condition=None):
    # Filter for age groups using string comparison
    nutrient_requirements = nutritional_df[
        (nutritional_df['Age'] == age_group) & 
        (nutritional_df['Gender'] == gender)
    ]
    
    if condition:
        nutrient_requirements = nutrient_requirements[
            (nutrient_requirements['Breastfeeding/Pregnant'] == condition)
        ]
    else:
        nutrient_requirements = nutrient_requirements[
            (nutritional_df['Breastfeeding/Pregnant'].isnull()) | 
            (nutritional_df['Breastfeeding/Pregnant'] == 'No')
        ]

    print(f"Age Group: {age_group}, Gender: {gender}, Condition: {condition}")
    print(f"Filtered Nutrient Requirements:\n{nutrient_requirements}\n")

    if not nutrient_requirements.empty:
        daily_requirements = nutrient_requirements.iloc[0]  # Assuming only one row matches the filter

        for nutrient in daily_requirements.index[3:]:  # Skip the first three columns (Age, Gender, Breastfeeding/Pregnant)
            if condition:
                column_name = f'{age_group}_{condition}'
            else:
                column_name = f'{age_group}_{gender.capitalize()}'
            
            # Check if column_name exists in merged_data_filtered
            if column_name in merged_data_filtered.columns:
                result_dict[f'{column_name}_{nutrient}'] = merged_data_filtered[column_name] * daily_requirements[nutrient]

# Extract age groups from merged_data column headers
age_groups_female = sorted(set([col.split('_')[0] for col in merged_data_filtered.columns if col.endswith('_Female')]))
age_groups_male = sorted(set([col.split('_')[0] for col in merged_data_filtered.columns if col.endswith('_Male')]))

# Extract special age groups for pregnant and breastfeeding women
special_age_groups = ['9-19', '20-56']
conditions = ['Pregnant', 'Breastfeeding']

# Step 1: Calculate nutrient requirements for all age groups and genders
for age_group in age_groups_female:
    print(f"Processing Female Age Group: {age_group}")
    add_nutrient_data(age_group, 'Female')

for age_group in age_groups_male:
    print(f"Processing Male Age Group: {age_group}")
    add_nutrient_data(age_group, 'Male')

# Step 2: Calculate nutrient requirements for special conditions (Pregnant and Breastfeeding)
for age_group in special_age_groups:
    for condition in conditions:
        print(f"Processing Female Age Group: {age_group} for {condition}")
        add_nutrient_data(age_group, 'Female', condition)

# Create the result_df DataFrame from result_dict
result_df = pd.DataFrame(result_dict)

# Step 1: Explicitly cast 'Region, subregion, country or area' as a string to ensure it stays as text
result_df['Region, subregion, country or area'] = result_df['Region, subregion, country or area'].astype(str)
region_column = result_df['Region, subregion, country or area']
year_column = result_df['Year']

# Step 2: Convert only nutrient columns to numeric, preserving non-numeric columns as NaN
result_df_numeric = result_df.drop(columns=['Region, subregion, country or area', 'Year']).apply(pd.to_numeric, errors='coerce').fillna(0)

# Step 3: Initialize a dictionary to store cumulative nutrient sums
vitamin_mineral_sums = {}

# Loop over columns in the numeric DataFrame for nutrient summation
for column in result_df_numeric.columns:
    # Extract nutrient name by splitting at underscores
    nutrient = '_'.join(column.split('_')[2:])
    
    # Sum values for each nutrient
    if nutrient not in vitamin_mineral_sums:
        vitamin_mineral_sums[nutrient] = result_df_numeric[column]
    else:
        vitamin_mineral_sums[nutrient] += result_df_numeric[column]

# Step 4: Convert the nutrient sums dictionary to a DataFrame
result_sum_df = pd.DataFrame(vitamin_mineral_sums, index=result_df.index)

# Step 5: Insert 'Region, subregion, country or area' and 'Year' as the first two columns
result_sum_df.insert(0, 'Region, subregion, country or area', region_column)
result_sum_df.insert(1, 'Year', year_column)

# Specify the columns to exclude from multiplication
exclude_columns = ['Region, subregion, country or area', 'Year']

# Multiply all other columns by 1000
result_sum_df.loc[:, ~result_sum_df.columns.isin(exclude_columns)] *= 1000

# Define the mapping for column renaming
column_mapping = {
    'Vitamin A': 'Vitamin A (RAE, mcg)',
    'Vitamin B1': 'Thiamine (vitamin B1) (mg)',
    'Vitamin B2': 'Riboflavin (vitamin B2) (mg)',
    'Vitamin B3': 'Niacin equivalents or [niacin, preformed] (vitamin B3) (mg)',
    'Vitamin B6': 'Vitamin B6 (mg)',
    'Vitamin B9': 'Folate, total or [folate, sum of vitamers] (vitamin B9) (mcg)',
    'Vitamin B12': 'Vitamin B12 (mcg)',
    'Vitamin C': 'Vitamin C (mg)',
    'Vitamin E': 'Vitamin E (expressed in alpha-tocopherol equivalents) or [alpha-tocopherol] (mg)',
    'Calcium': 'Calcium (mg)',
    'Copper': 'Copper (mg)',
    'Iron heme': 'Iron (mg)',
    'Magnesium': 'Magnesium (mg)',
    'Phosporus': 'Phosphorus (mg)',
    'Potassium': 'Potassium (mg)',
    'Zinc': 'Zinc (mg)'
}

# Select columns to keep based on the mapping, add region and year columns
columns_to_keep = ['Region, subregion, country or area', 'Year'] + list(column_mapping.keys())

# Filter the DataFrame to keep only necessary columns
result_sum_adj_df = result_sum_df[columns_to_keep]

# Rename columns based on the mapping
result_sum_adj_df = result_sum_adj_df.rename(columns=column_mapping)

import streamlit as st
import pandas as pd
import numpy as np

# Load the CSV files
nutrient_needs_df = pd.read_csv('result_sum_adj_df.csv')
food_data_df = pd.read_csv('WAFCT2019+PULSES.csv')
population_df = pd.read_csv('UN_PPP2024_Output_PopTot.csv', encoding='ISO-8859-1')

# User interface for selecting country and year
st.title('National Nutrient-Based Meal Planner')

# Select country and year
country = st.selectbox('Select Country', nutrient_needs_df['Region, subregion, country or area'].unique())
year = st.selectbox('Select Year', nutrient_needs_df['Year'].unique())

# Filter nutrient needs for the selected country and year
filtered_needs = nutrient_needs_df[(nutrient_needs_df['Region, subregion, country or area'] == country) & 
                                   (nutrient_needs_df['Year'] == year)]

# Retrieve population for the selected country and year
population_row = population_df[(population_df['Region, subregion, country or area *'] == country)]
population = population_row[str(year)].values[0] if not population_row.empty else 1  # Default to 1 if data is missing

# Calculate daily nutrient needs per citizen
daily_needs_per_citizen = filtered_needs.copy()
numeric_columns = daily_needs_per_citizen.select_dtypes(include=['float64', 'int64']).columns
daily_needs_per_citizen[numeric_columns] /= population

# Display the total nutrient needs for the country
st.subheader(f'Total Nutrient Needs for {country} in {year} (Countrywide)')
st.write(filtered_needs)

# Display the per capita daily nutrient needs for the country
st.subheader(f'Per Capita Daily Nutrient Needs for {country} in {year}')
st.write(daily_needs_per_citizen)

# Define food group calorie limits for daily intake
food_group_calorie_limits = {
    "DAIRY": 250,
    "MEAT": 56,
    "FISH": 28,
    "FATS AND OILS": 40,
    "GRAINS": 250,
    "STARCHY ROOTS/TUBERS": 100,
    "LEGUMES SOAKED & BOILED & DRAINED": 100,
    "VEGETABLES": 400,
    "FRUITS": 200,
    "NUTS": 75
}

# Set maximum foods and attempts
max_foods = 30
max_attempts = 50

# Helper function to clean nutrient values
def clean_nutrient_value(value):
    try:
        value = str(value).replace('[', '').replace(']', '').strip()
        return float(value)
    except ValueError:
        return 0.0

# Function to calculate percentage of nutrient needs met
def calculate_percentage_met(nutrient_needs_df, total_nutrients):
    percentage_met = {}
    for nutrient in total_nutrients:
        if nutrient in nutrient_needs_df.columns:
            required_amount = nutrient_needs_df[nutrient].values[0]
            if required_amount > 0:
                percentage_met[nutrient] = (total_nutrients[nutrient] / required_amount) * 100
    return percentage_met

# Function to generate optimized meal plans and select the best
def generate_optimized_meal_plan(daily_needs_per_citizen, food_data, max_foods, max_attempts, population, total_needs):
    best_iteration = None
    best_coverage_score = float('-inf')  # Track best-fit score

    all_iterations_results = []

    for attempt in range(max_attempts):
        meal_plan = {}
        total_nutrients = {nutrient: 0 for nutrient in daily_needs_per_citizen.columns[2:]}
        food_type_sums = {food_type: 0 for food_type in food_group_calorie_limits}
        total_foods_selected = 0

        def add_food_item_to_plan(food_item, food_type, grams):
            if food_type not in meal_plan:
                meal_plan[food_type] = []
            meal_plan[food_type].append({"Food": food_item['Food name in English'], "Grams": grams})

            nutrient_values_per_100g = {
                'Vitamin A (RAE, mcg)': clean_nutrient_value(food_item.get('Vitamin A (RAE, mcg)', 0)),
                'Thiamine (vitamin B1) (mg)': clean_nutrient_value(food_item.get('Thiamine (vitamin B1) (mg)', 0)),
                'Riboflavin (vitamin B2) (mg)': clean_nutrient_value(food_item.get('Riboflavin (vitamin B2) (mg)', 0)),
                'Niacin equivalents or [niacin, preformed] (vitamin B3) (mg)': clean_nutrient_value(food_item.get('Niacin equivalents or [niacin, preformed] (vitamin B3) (mg)', 0)),
                'Vitamin B6 (mg)': clean_nutrient_value(food_item.get('Vitamin B6 (mg)', 0)),
                'Folate, total or [folate, sum of vitamers] (vitamin B9) (mcg)': clean_nutrient_value(food_item.get('Folate, total or [folate, sum of vitamers] (vitamin B9) (mcg)', 0)),
                'Vitamin B12 (mcg)': clean_nutrient_value(food_item.get('Vitamin B12 (mcg)', 0)),
                'Vitamin C (mg)': clean_nutrient_value(food_item.get('Vitamin C (mg)', 0)),
                'Vitamin E (expressed in alpha-tocopherol equivalents) or [alpha-tocopherol] (mg)': clean_nutrient_value(food_item.get('Vitamin E (expressed in alpha-tocopherol equivalents) or [alpha-tocopherol] (mg)', 0)),
                'Calcium (mg)': clean_nutrient_value(food_item.get('Calcium (mg)', 0)),
                'Potassium (mg)': clean_nutrient_value(food_item.get('Potassium (mg)', 0)),
                'Copper (mg)': clean_nutrient_value(food_item.get('Copper (mg)', 0)),
                'Iron (mg)': clean_nutrient_value(food_item.get('Iron (mg)', 0)),
                'Magnesium (mg)': clean_nutrient_value(food_item.get('Magnesium (mg)', 0)),
                'Zinc (mg)': clean_nutrient_value(food_item.get('Zinc (mg)', 0))
            }

            for nutrient, value in nutrient_values_per_100g.items():
                total_nutrients[nutrient] += value * (grams / 100.0)

            if food_type in food_type_sums:
                food_type_sums[food_type] += grams

        while total_foods_selected < max_foods:
            food_was_added = False

            for food_type, limit in food_group_calorie_limits.items():
                if food_type_sums[food_type] < limit:
                    food_items = food_data[food_data['FOOD TYPE'] == food_type]
                    if not food_items.empty:
                        food_item = food_items.sample(n=1).iloc[0]
                        grams_to_add = min(limit - food_type_sums[food_type], 50)

                        if grams_to_add > 0:
                            add_food_item_to_plan(food_item, food_type, grams_to_add)
                            total_foods_selected += 1
                            food_was_added = True
                            if total_foods_selected >= max_foods:
                                break

            if not food_was_added:
                break

        # Calculate daily nutrient fulfillment and percentage per nutrient
        daily_percentage_met = calculate_percentage_met(daily_needs_per_citizen, total_nutrients)
        avg_coverage_score = sum(daily_percentage_met.values()) / len(daily_percentage_met)

        all_iterations_results.append({
            "Iteration": attempt + 1,
            "Meal Plan (grams per type)": meal_plan,
            "Total Nutrients": total_nutrients,
            "Percentage Fulfillment (%)": daily_percentage_met
        })

        if avg_coverage_score > best_coverage_score:
            best_coverage_score = avg_coverage_score
            best_iteration = all_iterations_results[-1]

    # Ensure we have a best iteration based on the highest average coverage score
    if best_iteration is None and all_iterations_results:
        best_iteration = max(all_iterations_results, key=lambda x: sum(x["Percentage Fulfillment (%)"].values()) / len(x["Percentage Fulfillment (%)"]))

    final_scaled_plan = {
        food_type: [
            {**item, "Total (kg)": item["Grams"] * population / 1000} for item in items
        ] for food_type, items in best_iteration["Meal Plan (grams per type)"].items()
    }

    # Return the results
    return all_iterations_results, best_iteration, final_scaled_plan

# Streamlit UI to generate and display results
if st.button("Generate Country-Scale Meal Plan"):
    all_iterations, best_iteration, final_scaled_plan = generate_optimized_meal_plan(
        daily_needs_per_citizen, food_data_df, max_foods, max_attempts, population, filtered_needs
    )

    # Display all iterations with nutrient percentages and totals
    st.subheader("Iterations Summary")
    for result in all_iterations:
        st.write(f"Iteration {result['Iteration']}:")
        st.write("Meal Plan (in grams per type):", result["Meal Plan (grams per type)"])
        st.write("Total Nutrients:", result["Total Nutrients"])
        st.write("Percentage Fulfillment (%) per Nutrient:", result["Percentage Fulfillment (%)"])
        st.write("----------------------------------------------------")

    # Display the best iteration if found
    if best_iteration:
        st.subheader("Best-Fit Iteration")
        st.write("Best Meal Plan (in grams per type):", best_iteration["Meal Plan (grams per type)"])
        st.write("Total Nutrients (unscaled):", best_iteration["Total Nutrients"])
        st.write("Percentage Fulfillment (%) per Nutrient:", best_iteration["Percentage Fulfillment (%)"])

        # Scale best iteration to meet total population needs
        st.subheader("Final Scaled-Up Meal Plan for Total Population")
        st.write("Final Meal Plan (in kg per type):", final_scaled_plan)

        # Calculate scaled-up nutrients and percentage fulfillment
        scaled_total_nutrients = {nutrient: value * population for nutrient, value in best_iteration["Total Nutrients"].items()}
        scaled_percentage_fulfillment = calculate_percentage_met(filtered_needs, scaled_total_nutrients)

        # Display scaled-up nutrients and fulfillment percentages
        st.subheader("Final Nutrient Totals and Fulfillment for Total Population")
        st.write("Scaled-Up Total Nutrients:", scaled_total_nutrients)
        st.write("Percentage Fulfillment (%) for Total Population:", scaled_percentage_fulfillment)
    else:
        st.error("No best-fit iteration found to scale up.")