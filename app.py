import streamlit as st
import pandas as pd
import urllib.parse
import os
import io

# Function to clean URL with additional conditions
def clean_url(url: str) -> str:
    # Remove unwanted terms from the URL
    unwanted_terms = [
        '-courses', '-pictures', '-admission', '-connect', '-campus', '-placement', '-reviews', '-scholarship',
        '/reviews', '/cut-off', '/courses_fees', '/pictures', '/admission', '/campus'
    ]

    cleaned_url = url.replace('/colleges/', '').replace('/college/', '')

    for term in unwanted_terms:
        cleaned_url = cleaned_url.replace(term, '')

    if '-dpid' in cleaned_url:
        cleaned_url = cleaned_url.split('-dpid')[0]
    if '-dp' in cleaned_url:
        cleaned_url = cleaned_url.split('-dp')[0]
    if '-cpd' in cleaned_url:
        cleaned_url = cleaned_url.split('-cpd')[0]

    parsed_url = urllib.parse.urlparse(cleaned_url)
    return f'{parsed_url.path.lstrip("/")}'

# Normalize column names to lowercase
def normalize_columns(df):
    df.columns = df.columns.str.lower()
    return df

# Function to process and aggregate data
def process_and_aggregate_data(input_url_files, mapper_file, website_type):
    final_result = pd.DataFrame()

    # Define required columns (normalized to lowercase)
    required_columns = ['url', 'sessions', 'cleaned_url', 'stream']
    custom_column_names = [
        'This_week_2024_Total_session',
        'Last_week_2024_Total_session',
        'This_week_2023_Total_session'
    ]
    
    for idx, input_file in enumerate(input_url_files):
        # Read and normalize input file
        df1 = normalize_columns(pd.read_excel(input_file))
        
        # Validate required columns in the input file
        if 'url' not in df1.columns or 'sessions' not in df1.columns:
            raise ValueError(f"Missing required columns 'url' or 'sessions' in input file {input_file.name}")
        
        # Clean the 'url' column
        df1['cleaned_url'] = df1['url'].apply(clean_url)

        # Read and normalize the mapper file
        df2 = normalize_columns(pd.read_excel(mapper_file))

        # Validate required columns in the mapper file
        if 'cleaned_url' not in df2.columns:
            raise ValueError(f"Column 'cleaned_url' not found in mapper file {mapper_file.name}")

        # Merge and aggregate
        mrgdf = pd.merge(df1, df2, on='cleaned_url', how='left')

        # Ensure the 'stream' column exists for aggregation
        if 'stream' not in mrgdf.columns:
            raise ValueError(f"Column 'stream' not found after merging in input file {input_file.name}")
        
        result = mrgdf.pivot_table(index='stream', values='sessions', aggfunc='sum')
        result.columns = [custom_column_names[idx]]

        if final_result.empty:
            final_result = result
        else:
            final_result = final_result.merge(result, left_index=True, right_index=True, how='outer')

    return final_result

# Streamlit UI setup
def main():
    st.title("Stream-Wise Sessions Calculator")
    st.write("""
    Upload the necessary input files based on your selected website, and the app will process the data and provide a download link for the Stream-wise total sessions.
    """)

    # Dropdown to select website (CollegeDekho or GetMyUni)
    website_type = st.selectbox("Select Website", ["CollegeDekho", "GetMyUni"])

    # File uploaders for input files
    if website_type == "CollegeDekho":
        st.header("Upload Files for CollegeDekho")
        input_file_1 = st.file_uploader("Select Input file (Excel) From CLD GA contains Column1 'url' &  Column2 'sessions' for this week 2024", type=["xlsx", "xls"])
        input_file_2 = st.file_uploader("Select Input file (Excel) From CLD GA contains Column1 'url' &  Column2 'sessions' for last week 2024", type=["xlsx", "xls"])
        input_file_3 = st.file_uploader("Select Input file (Excel) From CLD GA contains Column1 'url' &  Column2 'sessions' for this week 2023", type=["xlsx", "xls"])
        cld_mapper_file = st.file_uploader("Select CLD Mapper (Excel) File contains column1 'Cleaned_URL' &  Column2 'Stream' ", type=["xlsx", "xls"])
    else:  # GetMyUni
        st.header("Upload Files for GMU")
        input_file_1 = st.file_uploader("Select Input file (Excel) From GMU GA contains Column1 'url' &  Column2 'sessions' for this week 2024", type=["xlsx", "xls"])
        input_file_2 = st.file_uploader("Select Input file (Excel) From GMU GA contains Column1 'url' &  Column2 'sessions' for last week 2024", type=["xlsx", "xls"])
        input_file_3 = st.file_uploader("Select Input file (Excel) From GMU GA contains Column1 'url' &  Column2 'sessions' for this week 2023", type=["xlsx", "xls"])
        gmu_mapper_file = st.file_uploader("Select GMU Mapper (Excel) File contains Column1 'Cleaned_URL' & Column2 'Stream' ", type=["xlsx", "xls"])

    # Default output folder path (you can change this to any desired folder)
    default_output_folder = "output_files"
    os.makedirs(default_output_folder, exist_ok=True)

    # Button to trigger the aggregation process
    if st.button("Run Aggregation"):
        # Ensure that the right files are uploaded based on website type
        if website_type == "CollegeDekho":
            input_files = [input_file_1, input_file_2, input_file_3]
            mapper_file = cld_mapper_file
        else:  # GetMyUni
            input_files = [input_file_1, input_file_2, input_file_3]
            mapper_file = gmu_mapper_file

        if not all(input_files) or not mapper_file:
            st.error("Please make sure all fields are filled.")
        else:
            try:
                # Process the data
                result_df = process_and_aggregate_data(input_files, mapper_file, website_type)

                # Save the result to a default file path in the output directory
                output_file = os.path.join(default_output_folder, f"{website_type}_aggregated_data.xlsx")
                result_df.to_excel(output_file, index=True, engine='openpyxl')

                # Convert result to a BytesIO object for download
                output = io.BytesIO()
                result_df.to_excel(output, index=True, engine='openpyxl')
                output.seek(0)

                # Provide a download link
                st.success("Aggregation completed successfully! Click below to download the result.")
                st.download_button(
                    label="Download Aggregated Data",
                    data=output,
                    file_name=f"{website_type}_aggregated_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                # Optionally, display the dataframe in the app
                st.dataframe(result_df)

            except Exception as e:
                st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
