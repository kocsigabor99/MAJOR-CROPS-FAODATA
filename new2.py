import streamlit as st
import pandas as pd

# Load the dataset
file_path = r'C:\Users\kocsi\OneDrive\Asztali gép\ACT PROJ\1 FIND JOB 4 DAYS, (+IMPACT (EA UNI CHAPTER) + VOLUNTEER 1 DAY)\00 PLANT JOB\SUPPORT MATERIALS\ARTICLE 43 NUTRITION FOR EVERYONE\CSV\TOTALSNEW_RESULT_df_seperate.csv'

# Load CSV file into DataFrame
try:
    df = pd.read_csv(file_path)
except Exception as e:
    st.error(f"Error loading CSV file: {e}")
    st.stop()

# Sidebar - Filters
st.sidebar.title('Filters')

# Filter options
countries = df['Region, subregion, country or area'].unique()  # Use the correct column for countries
selected_country = st.sidebar.selectbox('Select Country', countries)

years = df['Year'].unique()
selected_year = st.sidebar.selectbox('Select Year', years)

genders_conditions = ['Male', 'Female', 'Breastfeeding', 'Pregnant', 'Women']
selected_gender_condition = st.sidebar.selectbox('Select Gender/Condition', genders_conditions)

# Extracting vitamin and mineral names from columns
vitamins_and_minerals = [col.split('_')[-1] for col in df.columns if 'Total_' in col]
selected_vitamin_mineral = st.sidebar.selectbox('Select Vitamin/Mineral', vitamins_and_minerals)

# Filtering the dataframe based on selections
filtered_df = df[(df['Region, subregion, country or area'] == selected_country) &
                 (df['Year'] == selected_year)]

# Display filtered results
st.title('Filtered Results')
st.write(f"Showing data for: {selected_country}, Year: {selected_year}, Gender/Condition: {selected_gender_condition}, Vitamin/Mineral: {selected_vitamin_mineral}")
if filtered_df.empty:
    st.write("No data available with the current filters.")
else:
    st.write(filtered_df[[f'Total_{selected_gender_condition}_{selected_vitamin_mineral}']])
