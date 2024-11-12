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