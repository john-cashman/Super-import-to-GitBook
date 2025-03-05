import streamlit as st
import pandas as pd
import os
import zipfile
import yaml
import shutil
from bs4 import BeautifulSoup
from io import BytesIO

# -------------------- HELPER FUNCTIONS -------------------- #

def convert_zendesk_csv_to_markdown(df):
    """Convert Zendesk CSV to Markdown files with SUMMARY.md"""
    temp_dir = "converted_zendesk"
    os.makedirs(temp_dir, exist_ok=True)

    if not all(col in df.columns for col in ["Article Body", "Section", "Article Title"]):
        st.error("CSV must contain 'Article Body', 'Section', and 'Article Title'.")
        return None

    summary_structure = {}

    for index, row in df.iterrows():
        title = row["Article Title"]
        body = row["Article Body"]
        section = row["Section"]

        safe_title = title.replace(" ", "-").lower()
        filename = f"{safe_title}.md"

        safe_section = section.replace(" ", "-").lower()
        section_folder = os.path.join(temp_dir, safe_section)
        os.makedirs(section_folder, exist_ok=True)

        file_path = os.path.join(section_folder, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n{body}")

        if section not in summary_structure:
            summary_structure[section] = []
        summary_structure[section].append((title, f"{safe_section}/{filename}"))

    summary_content = "# Summary\n\n"
    for section, pages in summary_structure.items():
        summary_content += f"## {section}\n"
        for page_title, page_path in pages:
            summary_content += f"* [{page_title}]({page_path})\n"
        summary_content += "\n"

    with open(os.path.join(temp_dir, "SUMMARY.md"), "w", encoding="utf-8") as summary_file:
        summary_file.write(summary_content)

    return temp_dir

def convert_mdx_to_md(mdx_path, base_dir, output_dir):
    """Convert MDX files to Markdown"""
    full_path = os.path.join(base_dir, mdx_path)
    if os.path.exists(full_path) and full_path.endswith(".mdx"):
        with open(full_path, "r", encoding="utf-8") as file:
            mdx_content = file.read()

        md_content = "\n".join(
            line for line in mdx_content.splitlines()
            if not line.strip().startswith(("import", "export"))
        )

        markdown_filename = os.path.basename(mdx_path).replace(".mdx", ".md")
        output_file_path = os.path.join(output_dir, markdown_filename)

        with open(output_file_path, "w", encoding="utf-8") as output_file:
            output_file.write(md_content)

        return markdown_filename
    return None

def extract_structure_from_yaml(data, summary_lines, base_dir, output_dir, level=2):
    """Extract sections and pages from docs.yml"""
    if isinstance(data, list):
        for item in data:
            extract_structure_from_yaml(item, summary_lines, base_dir, output_dir, level)
    elif isinstance(data, dict):
        if "section" in data:
            summary_lines.append(f"{'#' * level} {data['section']}\n")

        if "page" in data and "path" in data:
            markdown_path = convert_mdx_to_md(data["path"], base_dir, output_dir)
            if markdown_path:
                summary_lines.append(f"* [{data['page']}]({markdown_path})\n")

        for key, value in data.items():
            if isinstance(value, (list, dict)):
                extract_structure_from_yaml(value, summary_lines, base_dir, output_dir, level + 1)

def convert_fern_yaml(yaml_content, base_dir):
    """Parse Fern's docs.yml and convert MDX files to Markdown"""
    try:
        data = yaml.safe_load(yaml_content)
        summary_lines = ["# Table of contents\n"]
        output_dir = "converted_fern"
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        extract_structure_from_yaml(data, summary_lines, base_dir, output_dir)
        summary_md = "\n".join(summary_lines)

        with open(os.path.join(output_dir, "SUMMARY.md"), "w", encoding="utf-8") as summary_file:
            summary_file.write(summary_md)

        return output_dir
    except Exception as e:
        return None

def zip_directory(directory):
    """Zip all files in a directory"""
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(directory):
            for file_name in files:
                full_path = os.path.join(root, file_name)
                arcname = os.path.relpath(full_path, directory)
                zipf.write(full_path, arcname)
    zip_buffer.seek(0)
    return zip_buffer

# -------------------- STREAMLIT APP -------------------- #

st.title("📥 Super Importer: Convert Zendesk, Mintlify & Fern to GitBook")

source = st.selectbox("Select your source:", ["Zendesk CSV", "Mintlify (MDX)", "Fern (docs.yml)"])

if source == "Zendesk CSV":
    uploaded_file = st.file_uploader("Upload Zendesk CSV", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        converted_dir = convert_zendesk_csv_to_markdown(df)

        if converted_dir:
            zip_buffer = zip_directory(converted_dir)
            st.success("✅ Zendesk converted successfully!")
            st.download_button("Download Converted Files", zip_buffer, "zendesk_markdown.zip", "application/zip")

elif source == "Mintlify (MDX)":
    uploaded_files = st.file_uploader("Upload Mintlify MDX files", type=["mdx"], accept_multiple_files=True)
    if uploaded_files:
        output_dir = "converted_mintlify"
        os.makedirs(output_dir, exist_ok=True)

        for uploaded_file in uploaded_files:
            mdx_content = uploaded_file.read().decode("utf-8")
            md_filename = uploaded_file.name.replace(".mdx", ".md")

            with open(os.path.join(output_dir, md_filename), "w", encoding="utf-8") as md_file:
                md_file.write(mdx_content)

        zip_buffer = zip_directory(output_dir)
        st.success("✅ Mintlify files converted successfully!")
        st.download_button("Download Converted Files", zip_buffer, "mintlify_markdown.zip", "application/zip")

elif source == "Fern (docs.yml)":
    uploaded_yaml = st.file_uploader("Upload Fern docs.yml", type=["yml", "yaml"])
    base_directory = st.text_input("Base directory for MDX files", value="docs")

    if uploaded_yaml:
        yaml_content = uploaded_yaml.read().decode("utf-8")
        converted_dir = convert_fern_yaml(yaml_content, base_directory)

        if converted_dir:
            zip_buffer = zip_directory(converted_dir)
            st.success("✅ Fern files converted successfully!")
            st.download_button("Download Converted Files", zip_buffer, "fern_markdown.zip", "application/zip")
