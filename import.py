import streamlit as st
import pandas as pd
import os
import zipfile
import shutil
from io import BytesIO

# -------------------- HELPER FUNCTIONS (Super App Core) -------------------- #

def extract_zip(uploaded_file, extract_to="temp_extracted"):
    """Extracts uploaded ZIP file"""
    temp_dir = extract_to
    if os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
        except OSError as e:
            st.error(f"Error removing directory: {e}")
            return None
    os.makedirs(temp_dir)

    with zipfile.ZipFile(uploaded_file, "r") as zip_ref:
        zip_ref.extractall(temp_dir)
        
    return temp_dir

def convert_zendesk_csv_to_markdown(csv_folder):
    """Convert all Zendesk CSV files in the extracted ZIP to Markdown"""
    temp_dir = "converted_zendesk"
    os.makedirs(temp_dir, exist_ok=True)
    summary_structure = {}

    for file in os.listdir(csv_folder):
        if file.endswith(".csv"):
            df = pd.read_csv(os.path.join(csv_folder, file))
            if not all(col in df.columns for col in ["Article Body", "Section", "Article Title"]):
                st.error(f"Invalid CSV format in {file}. Skipping...")
                continue

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

def convert_mdx_to_md(mdx_folder, output_dir):
    """Convert all MDX files in the extracted ZIP to Markdown"""
    os.makedirs(output_dir, exist_ok=True)

    for root, _, files in os.walk(mdx_folder):
        for file in files:
            if file.endswith(".mdx"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    mdx_content = f.read()

                md_content = "\n".join(
                    line for line in mdx_content.splitlines()
                    if not line.strip().startswith(("import", "export"))
                )

                markdown_filename = file.replace(".mdx", ".md")
                output_file_path = os.path.join(output_dir, markdown_filename)

                with open(output_file_path, "w", encoding="utf-8") as output_file:
                    output_file.write(md_content)

    return output_dir

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

# -------------------- STREAMLIT APP (Conversion) -------------------- #

st.title("📥 Super Importer: Upload ZIP & Convert to GitBook")

source = st.selectbox("Select your source:", ["Zendesk ZIP", "MDX ZIP"])

uploaded_zip = st.file_uploader("Upload ZIP file", type=["zip"])
if uploaded_zip:
    extracted_dir = extract_zip(uploaded_zip, extract_to="extracted_files")
    if extracted_dir:
        if source == "Zendesk ZIP":
            converted_dir = convert_zendesk_csv_to_markdown(extracted_dir)
        elif source == "MDX ZIP":
            converted_dir = convert_mdx_to_md(extracted_dir, "converted_mdx")

        if converted_dir:
            zip_buffer = zip_directory(converted_dir)
            st.success("✅ Conversion successful!")
            st.download_button("Download Converted Files", zip_buffer, f"{source.lower().replace(' ', '_')}_markdown.zip", "application/zip")
            st.session_state.converted_dir = converted_dir
            st.session_state.extracted_dir = extracted_dir
            st.session_state.source = source
