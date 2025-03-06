import streamlit as st
import pandas as pd
import os
import zipfile
import yaml
import shutil
from io import BytesIO

# -------------------- HELPER FUNCTIONS (Super App Core) -------------------- #

def extract_zip(uploaded_file, extract_to="temp_extracted"):
    # ... (Your existing extract_zip function)

def convert_zendesk_csv_to_markdown(csv_folder):
    # ... (Your existing convert_zendesk_csv_to_markdown function)

def convert_mdx_to_md(mdx_folder, output_dir):
    # ... (Your existing convert_mdx_to_md function)

def extract_structure_from_yaml(data, summary_lines, base_dir, output_dir, level=2):
    # ... (Your existing extract_structure_from_yaml function)

def convert_fern_yaml(yaml_folder):
    # ... (Your existing convert_fern_yaml function)

def zip_directory(directory):
    # ... (Your existing zip_directory function)

# -------------------- STREAMLIT APP (Conversion) -------------------- #

st.title("📥 Super Importer: Upload ZIP & Convert to GitBook")

source = st.selectbox("Select your source:", ["Zendesk ZIP", "Mintlify ZIP", "Fern ZIP"])

uploaded_zip = st.file_uploader("Upload ZIP file", type=["zip"])
if uploaded_zip:
    extracted_dir = extract_zip(uploaded_zip, extract_to="extracted_files")

    if source == "Zendesk ZIP":
        converted_dir = convert_zendesk_csv_to_markdown(extracted_dir)
    elif source == "Mintlify ZIP":
        converted_dir = convert_mdx_to_md(extracted_dir, "converted_mintlify")
    elif source == "Fern ZIP":
        converted_dir = convert_fern_yaml(extracted_dir)

    if converted_dir:
        zip_buffer = zip_directory(converted_dir)
        st.success("✅ Conversion successful!")
        st.download_button("Download Converted Files", zip_buffer, f"{source.lower().replace(' ', '_')}_markdown.zip", "application/zip")
        st.session_state.converted_dir = converted_dir # Add this line.
        st.session_state.extracted_dir = extracted_dir #Add this line.
        st.session_state.source = source #add this line.
