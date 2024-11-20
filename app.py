import streamlit as st
import pandas as pd
import urllib.parse
import os

# Function to clean URL with additional conditions
def clean_url(url: str) -> str:
    cleaned_url = url.replace('/colleges/', '')
    if '-dpid' in cleaned_url:
        cleaned_url = cleaned_url.split('-dpid')[0]
    if '-dp' in cleaned_url:
        cleaned_url = cleaned_url.split('-dp')[0]
    if '-cpd' in cleaned_url:
        cleaned_url = cleaned_url.split('-cpd')[0]
    parsed_url = urllib.parse.urlparse(cleaned_url)
    return f'{parsed_url.path.lstrip("/")}'

# Function to process and aggregate data
def process_and_aggregate_data(input_url_files, cld_mapper_file):
    final_result = pd.DataFrame()
    custom_column_names = ['This_week_2024_Total_session', 'Last_week_2024_Total_session', 'This_week_2023_Total_session']
    
    for idx, input_url_file in enumerate(input_url_files):
        df1 = pd.read_excel(input_url_file)
        df1['Cleaned_URL'] = df1['URL'].apply(clean_url)
        
        df2 = pd.read_excel(cld_mapper_file)
        mrgdf = pd.merge(df1, df2, on="Cleaned_URL", how='left')
        result = mrgdf.pivot_table(index='Stream', values='sessions', aggfunc='sum')
        result.columns = [custom_column_names[idx]]
        
        if final_result.empty:
            final_result = result
        else:
            final_result = final_result.merge(result, left_index=True, right_index=True, how='outer')
    
    return final_result

# Streamlit UI setup
def main():
    st.title("Session Aggregation Tool")
    st.write("""
    Upload three input files containing URLs, the CLD Mapper file, and let the app process the data and provide a download link.
    """)

    # File uploaders for input files
    input_file_1 = st.file_uploader("Select Input File 1 (Excel)", type=["xlsx", "xls"])
    input_file_2 = st.file_uploader("Select Input File 2 (Excel)", type=["xlsx", "xls"])
    input_file_3 = st.file_uploader("Select Input File 3 (Excel)", type=["xlsx", "xls"])

    # File uploader for the CLD Mapper file
    cld_mapper_file = st.file_uploader("Select CLD Mapper Excel File", type=["xlsx", "xls"])

    # Button to trigger the aggregation process
    if st.button("Run Aggregation"):
        if not input_file_1 or not input_file_2 or not input_file_3 or not cld_mapper_file:
            st.error("Please make sure all fields are filled.")
        else:
            try:
                # Process the files
                input_files = [input_file_1, input_file_2, input_file_3]
                
                # Convert file-like objects to actual file paths (needed for pandas to read)
                input_files_paths = [file.name for file in input_files]
                mapper_file_path = cld_mapper_file.name

                # Process the data
                result_df = process_and_aggregate_data(input_files_paths, mapper_file_path)

                # Convert result to a BytesIO object for download
                import io
                output = io.BytesIO()
                result_df.to_excel(output, index=True, engine='openpyxl')
                output.seek(0)

                # Provide a download link
                st.success("Aggregation completed successfully! Click below to download the result.")
                st.download_button(
                    label="Download Aggregated Data",
                    data=output,
                    file_name="aggregated_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                # Optionally, display the dataframe in the app
                st.dataframe(result_df)

            except Exception as e:
                st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
