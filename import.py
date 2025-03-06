import streamlit as st
import pandas as pd
import os
import zipfile
import yaml
import shutil
from bs4 import BeautifulSoup
from io import BytesIO
import json

# -------------------- HELPER FUNCTIONS (Existing Super App) -------------------- #

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

# -------------------- SUMMARY.md GENERATOR FUNCTIONS -------------------- #

def extract_structure_yaml_summary(data, summary_lines, level=2, indent=""):
    # ... (Your existing extract_structure_yaml function)

def extract_structure_json_summary(data, summary_lines, level=2, indent=""):
    # ... (Your existing extract_structure_json function)

def parse_data_summary(content, format_type):
    # ... (Your existing parse_data function)

# -------------------- STREAMLIT APP -------------------- #

st.title("📥 Super Importer: Upload ZIP & Convert to GitBook")

source = st.selectbox("Select your source:", ["Zendesk ZIP", "Mintlify ZIP", "Fern ZIP", "Mint JSON/YAML"])

uploaded_zip = st.file_uploader("Upload ZIP file", type=["zip"])
uploaded_file_json_yaml = st.file_uploader("Upload JSON/YAML file", type=["json", "yml", "yaml"])

if source in ["Zendesk ZIP", "Mintlify ZIP", "Fern ZIP"]:
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

            if st.button("Generate SUMMARY.md"):
                if source == "Fern ZIP":
                    yaml_path = os.path.join(extracted_dir, "docs.yml")
                    if os.path.exists(yaml_path):
                        with open(yaml_path, "r", encoding="utf-8") as f:
                            yaml_content = f.read()
                        summary_md = parse_data_summary(yaml_content, "yaml")
                        st.subheader("Generated SUMMARY.md")
                        st.code(summary_md, language="markdown")
                        summary_bytes = summary_md.encode("utf-8")
                        st.download_button("Download SUMMARY.md", summary_bytes, "SUMMARY.md", "text/markdown")
                else:
                    st.warning("SUMMARY.md generation is only available for Fern ZIP.")

elif source == "Mint JSON/YAML":
    if uploaded_file_json_yaml:
        content = uploaded_file_json_yaml.read().decode("utf-8")
        if uploaded_file_json_yaml.name.endswith(".json"):
            file_type = "json"
        else:
            file_type = "yaml"

        if st.button("Convert"):
            summary_md = parse_data_summary(content, file_type)
            st.subheader("Generated SUMMARY.md")
            st.code(summary_md, language="markdown")
            summary_bytes = summary_md.encode("utf-8")
            st.download_button("Download SUMMARY.md", summary_bytes, "SUMMARY.md", "text/markdown")
