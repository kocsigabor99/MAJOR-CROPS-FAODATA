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