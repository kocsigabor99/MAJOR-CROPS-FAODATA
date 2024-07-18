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
birth_rate_url = 'https://raw.githubusercontent.com/kocsigabor99/MAJOR-CROPS-FAODATA/main/UN_PPP2022_Birth%20rate_Single_Year.csv'

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
for age in range(15, 50):  # Assuming age ranges from 15 to 49
    age_str = str(age)
    birth_rate_col = f'{age_str}_y'
    if age_str in merged_df.columns and birth_rate_col in merged_df.columns:
        merged_df[f'Births_{age}'] = merged_df[age_str] * merged_df[birth_rate_col]

# Sum up the number of births across all age groups to get total births
birth_columns = [f'Births_{age}' for age in range(15, 50) if f'Births_{age}' in merged_df.columns]
merged_df['Total_Births'] = merged_df[birth_columns].sum(axis=1)

# Calculate the number of pregnant women per single age group
pregnant_cols = {f'Pregnant_{age}': merged_df[f'Births_{age}'] for age in range(15, 50)}

# Extrapolate for pregnant teens aged 14 based on births in age 15
pregnant_cols['Pregnant_14'] = merged_df['Births_15']

# Calculate the number of breastfeeding women per single age group
breastfeeding_cols = {f'Breastfeeding_{age}': merged_df[f'Births_{age-2}'] + merged_df[f'Births_{age-1}'] for age in range(17, 50)}

# Special cases for ages 15 and 16
breastfeeding_cols['Breastfeeding_15'] = merged_df['Births_15']
breastfeeding_cols['Breastfeeding_16'] = merged_df['Births_15'] + merged_df['Births_16']

# Create a new DataFrame with these columns
new_cols = {**pregnant_cols, **breastfeeding_cols}
new_df = pd.DataFrame(new_cols)

# Concatenate the new DataFrame with the original DataFrame
merged_df = pd.concat([merged_df, new_df], axis=1)

# Optionally, save the updated DataFrame to a new CSV file
merged_df.to_csv('updated_birth_data.csv', index=False)


# 2. Subtract the numbers in the 'Pregnant_14' to 'Pregnant_49' columns from the corresponding female single age groups
pregnant_columns = {f'Pregnant_{age}': age for age in range(14, 50)}
for col, age in pregnant_columns.items():
    merged_df[str(age)] -= merged_df[col] / 1000

# 3. Subtract the numbers in the 'Breastfeeding_15' to 'Breastfeeding_49' columns from the corresponding female single age groups
breastfeeding_columns = {f'Breastfeeding_{age}': age for age in range(15, 50)}
for col, age in breastfeeding_columns.items():
    merged_df[str(age)] -= merged_df[col] / 1000


rounded_df = merged_df.round(10)


# Create a copy of the DataFrame to apply scaling
scaled_df = rounded_df.copy()

# Define columns to scale (pregnant and breastfeeding columns)
columns_to_scale = [f'Pregnant_{age}' for age in range(14, 50)] + [f'Breastfeeding_{age}' for age in range(15, 50)]

# Scale the specified columns by dividing by 1000
scaled_df[columns_to_scale] /= 1000






import pandas as pd

# Example DataFrame (replace with your actual DataFrame)
# scaled_df = ...

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
        '1-3': [str(i) + '_male' for i in range(1, 4)],
        '4-8': [str(i) + '_male' for i in range(4, 9)],
        '9-13': [str(i) + '_male' for i in range(9, 14)],
        '14-18': [str(i) + '_male' for i in range(14, 19)],
        '19-50': [str(i) + '_male' for i in range(19, 51)],
        '51-70': [str(i) + '_male' for i in range(51, 71)],
        '71-100+': [str(i) + '_male' for i in range(71, 100)] + ['100+_male']
    },
    'Female': {
        '0': ['0_female'],
        '1-3': [str(i) + '_female' for i in range(1, 4)],
        '4-8': [str(i) + '_female' for i in range(4, 9)],
        '9-13': [str(i) + '_female' for i in range(9, 14)],
        '14-18': [str(i) + '_female' for i in range(14, 19)],
        '19-50': [str(i) + '_female' for i in range(19, 51)],
        '51-70': [str(i) + '_female' for i in range(51, 71)],
        '71-100+': [str(i) + '_female' for i in range(71, 100)] + ['100+_female']
    },
    'Pregnant': {
        '15-19': ['Pregnant_' + str(i) for i in range(15, 20)],
        '20-49': ['Pregnant_' + str(i) for i in range(20, 50)]
    },
    'Breastfeeding': {
        '15-19': ['Breastfeeding_' + str(i) for i in range(15, 20)],
        '20-49': ['Breastfeeding_' + str(i) for i in range(20, 50)]
    }
}

# Create a list of columns to keep based on the age group mappings
columns_to_keep = ['Region, subregion, country or area', 'Year', 'Total_Births']

for category, groups in age_groups.items():
    for age_range, columns in groups.items():
        # Aggregate columns for the current age group
        merged_data[f'{age_range}_{category}'] = merged_data[columns].sum(axis=1)
        # Drop individual columns after aggregation
        merged_data.drop(columns, axis=1, inplace=True)
        # Add aggregated column to columns_to_keep
        columns_to_keep.append(f'{age_range}_{category}')

# Filter the DataFrame to keep only the desired columns
merged_data_filtered = merged_data[columns_to_keep]




# Load your data
url_nutritional = 'https://raw.githubusercontent.com/kocsigabor99/MAJOR-CROPS-FAODATA/main/Micronutrient%20Needs%20by%20single%20year%20Pregnant%20and%20Breastfeeding%20included.csv'
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
special_age_groups = ['15-19', '20-49']
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

# Debug output
print(result_df)

import streamlit as st

# Define unique options for each dropdown
regions = result_df['Region, subregion, country or area'].unique()
years = result_df['Year'].unique()

# Vitamins/Minerals columns based on your dataset
vitamins_minerals = [col for col in result_df.columns if col.endswith((
    '_Vitamin A', '_Vitamin B1', '_Vitamin B2', '_Vitamin B3', '_Vitamin B5',
    '_Vitamin B6', '_Vitamin B7', '_Vitamin B9', '_Vitamin B12', '_Vitamin C',
    '_Vitamin D', '_Vitamin E', '_Vitamin K', '_Calcium', '_Copper', '_Iodine',
    '_Iron heme', '_Iron (non-heme)', '_Magnesium', '_Manganese', '_Molybdenum',
    '_Phosphorus', '_Potassium', '_Selenium', '_Zinc'
))]

# Extract unique age groups and genders/conditions
age_groups = sorted(set([col.split('_')[0] for col in merged_data_filtered.columns]))
genders_conditions = ['Male', 'Female', 'Pregnant', 'Breastfeeding']

# Create Streamlit sidebar widgets for selection
selected_region = st.sidebar.multiselect('Select Region', regions)
selected_year = st.sidebar.multiselect('Select Year', years)
selected_age_group = st.sidebar.selectbox('Select Age Group', ['Select All'] + age_groups)
selected_gender_condition = st.sidebar.selectbox('Select Gender/Condition', ['Select All'] + genders_conditions)
selected_vitamin_mineral = st.sidebar.selectbox('Select Vitamin/Mineral', ['Select All'] + vitamins_minerals)

# Filtering logic based on user selections
filtered_data = result_df[
    (result_df['Region, subregion, country or area'].isin(selected_region)) &
    (result_df['Year'].isin(selected_year))
]

if selected_age_group != 'Select All':
    age_columns = [col for col in result_df.columns if col.startswith(selected_age_group)]
    filtered_data = filtered_data[age_columns + ['Region, subregion, country or area', 'Year']]

if selected_gender_condition != 'Select All':
    gender_condition_columns = [col for col in filtered_data.columns if col.endswith(f'_{selected_gender_condition}')]
    filtered_data = filtered_data[gender_condition_columns + ['Region, subregion, country or area', 'Year']]

if selected_vitamin_mineral != 'Select All':
    filtered_data = filtered_data[['Region, subregion, country or area', 'Year', selected_vitamin_mineral]]

# Display filtered data or any other output as needed
st.write(filtered_data)
