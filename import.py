import streamlit as st
import pandas as pd
import os
import zipfile
from io import BytesIO
import re
from bs4 import BeautifulSoup

# Function to convert MDX files (Mintlify & Fern)
def process_mdx_zip(uploaded_file):
    temp_dir = "temp_mdx_files"
    os.makedirs(temp_dir, exist_ok=True)

    # Extract ZIP file
    with zipfile.ZipFile(uploaded_file, "r") as zip_ref:
        zip_ref.extractall(temp_dir)

    # Find and process MDX files
    summary_structure = {}
    
    for root, _, files in os.walk(temp_dir):
        for file in files:
            if file.endswith(".mdx"):
                file_path = os.path.join(root, file)
                section = os.path.basename(root)  # Use folder name as section

                with open(file_path, "r", encoding="utf-8") as f:
                    mdx_content = f.read()

                # Convert MDX (Modify if you need special processing)
                markdown_content = convert_mdx_to_markdown(mdx_content)

                # Safe filename processing
                safe_title = os.path.splitext(file)[0].replace(" ", "-").lower()
                new_filename = f"{safe_title}.md"

                # Save processed markdown
                section_folder = os.path.join(temp_dir, section)
                os.makedirs(section_folder, exist_ok=True)

                with open(os.path.join(section_folder, new_filename), "w", encoding="utf-8") as f:
                    f.write(markdown_content)

                # Update SUMMARY.md
                if section not in summary_structure:
                    summary_structure[section] = []
                summary_structure[section].append((safe_title, f"{section}/{new_filename}"))

    # Create SUMMARY.md
    summary_content = "# Summary\n\n"
    for section, pages in summary_structure.items():
        summary_content += f"## {section}\n"
        for title, path in pages:
            summary_content += f"* [{title}]({path})\n"
        summary_content += "\n"

    with open(os.path.join(temp_dir, "SUMMARY.md"), "w", encoding="utf-8") as summary_file:
        summary_file.write(summary_content)

    # Create ZIP
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(temp_dir):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, temp_dir)
                zipf.write(full_path, arcname)

    # Cleanup
    for root, _, files in os.walk(temp_dir, topdown=False):
        for file in files:
            os.remove(os.path.join(root, file))
        os.rmdir(root)

    zip_buffer.seek(0)
    return zip_buffer

# Function to convert MDX to Markdown (modify as needed)
def convert_mdx_to_markdown(mdx_content):
    # Example: Replace MDX-style callouts with Markdown callouts
    mdx_content = re.sub(r'<Callout>(.*?)</Callout>', r'{% hint style="info" %}\n\1\n{% endhint %}', mdx_content, flags=re.DOTALL)
    return mdx_content

# Function to process CSV from Zendesk
def process_csv_file(uploaded_csv):
    temp_dir = "temp_csv_files"
    os.makedirs(temp_dir, exist_ok=True)

    df = pd.read_csv(uploaded_csv)
    
    if not all(col in df.columns for col in ["Article Body", "Section", "Article Title"]):
        st.error("CSV must contain `Article Body`, `Section`, and `Article Title` columns.")
        return None

    summary_structure = {}

    for index, row in df.iterrows():
        title = re.sub(r'\d+', '', row["Article Title"])  # Remove numbers from title
        body = row["Article Body"]
        section = row["Section"]

        markdown_content = f"# {title}\n\n{body}"

        safe_title = "".join(c for c in title if c.isalnum() or c in " -_").rstrip().replace(" ", "-").lower()
        filename = f"{safe_title or 'article'}.md"

        safe_section = section.replace(" ", "-").lower()
        section_folder = os.path.join(temp_dir, safe_section)
        os.makedirs(section_folder, exist_ok=True)

        file_path = os.path.join(section_folder, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

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

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(temp_dir):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, temp_dir)
                zipf.write(full_path, arcname)

    for root, _, files in os.walk(temp_dir, topdown=False):
        for file in files:
            os.remove(os.path.join(root, file))
        os.rmdir(root)

    zip_buffer.seek(0)
    return zip_buffer

# Streamlit UI
def main():
    st.title("Import & Convert Documentation")

    import_source = st.selectbox(
        "Choose your source",
        ["GitHub (MDX & HTML)", "Mintlify (MDX)", "Fern (MDX)", "Zendesk (CSV)"]
    )

    uploaded_file = None

    if import_source in ["GitHub (MDX & HTML)", "Mintlify (MDX)", "Fern (MDX)"]:
        uploaded_file = st.file_uploader("Upload your repository as a ZIP file", type="zip")
        
        if uploaded_file and st.button("Process MDX Files"):
            zip_buffer = process_mdx_zip(uploaded_file)
            if zip_buffer:
                st.success(f"{import_source} files processed successfully!")
                st.download_button(
                    label="Download Markdown ZIP",
                    data=zip_buffer,
                    file_name="processed_markdown.zip",
                    mime="application/zip",
                )

    elif import_source == "Zendesk (CSV)":
        uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

        if uploaded_file and st.button("Process CSV File"):
            zip_buffer = process_csv_file(uploaded_file)
            if zip_buffer:
                st.success("CSV converted to Markdown successfully!")
                st.download_button(
                    label="Download Markdown ZIP",
                    data=zip_buffer,
                    file_name="zendesk_markdown.zip",
                    mime="application/zip",
                )

if __name__ == "__main__":
    main()
