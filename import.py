
import streamlit as st
import os
import zipfile
import tempfile
from pathlib import Path
import shutil
import re
import pandas as pd
from bs4 import BeautifulSoup
from io import BytesIO

# Streamlit UI setup
st.title("Super App: Convert Files to Markdown")

# Dropdown for selecting the import source
import_source = st.selectbox(
    "Select Import Source",
    ["MDX (ZIP)", "Zendesk (CSV)"]
)

# Helper Functions
def find_files(repo_path):
    """Find all files in the repository."""
    all_files = []
    for root, _, files in os.walk(repo_path):
        for file in files:
            all_files.append(Path(root) / file)
    return all_files

def read_file_with_fallback(file_path):
    """Read a file with encoding fallback."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(file_path, "r", encoding="latin-1") as f:
            return f.read()

def convert_mdx_to_markdown(content):
    """Convert MDX content to Markdown by removing JSX-like tags."""
    content = re.sub(r'<[^<>]+>', '', content)  # Remove JSX/HTML-like tags
    content = re.sub(r'{[^{}]+}', '', content)  # Remove JSX expressions
    return content

def create_output_zip(output_dir, zip_name):
    """Create a ZIP file for the converted files."""
    zip_path = Path(tempfile.gettempdir()) / f"{zip_name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(output_dir):
            for file in files:
                full_path = Path(root) / file
                zipf.write(full_path, full_path.relative_to(output_dir))
    return zip_path

# ========== Processing MDX (ZIP) ==========
if import_source == "MDX (ZIP)":
    uploaded_repo = st.file_uploader("Upload your MDX repository as a ZIP file", type="zip")
    output_file_name = st.text_input("Enter a name for the output ZIP file:", "converted_mdx_repo")

    if uploaded_repo and output_file_name.strip():
        st.info("Processing your uploaded MDX repository...")
        with tempfile.TemporaryDirectory() as tmpdirname:
            zip_path = Path(tmpdirname) / "uploaded_repo.zip"
            with open(zip_path, "wb") as f:
                f.write(uploaded_repo.read())

            if not zipfile.is_zipfile(zip_path):
                st.error("The uploaded file is not a valid ZIP file.")
                st.stop()

            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    extracted_dir = Path(tmpdirname) / "uploaded_repo"
                    zip_ref.extractall(extracted_dir)

                repo_path = extracted_dir
                output_dir = Path(tmpdirname) / "converted_repo"
                output_dir.mkdir()

                # Process files
                all_files = find_files(repo_path)
                for file_path in all_files:
                    relative_path = file_path.relative_to(repo_path)
                    target_path = output_dir / relative_path

                    if file_path.suffix == ".mdx":
                        st.write(f"Processing MDX file: {file_path}")
                        mdx_content = read_file_with_fallback(file_path)
                        markdown_content = convert_mdx_to_markdown(mdx_content)
                        target_path = target_path.with_suffix(".md")

                        with open(target_path, "w", encoding="utf-8") as f:
                            f.write(markdown_content)

                    else:
                        shutil.copy(file_path, target_path)

                # Create a ZIP of the output directory
                st.write("Creating output ZIP...")
                zip_path = create_output_zip(output_dir, output_file_name.strip())

                with open(zip_path, "rb") as f:
                    st.download_button(
                        label="Download Converted Repository",
                        data=f.read(),
                        file_name=f"{output_file_name.strip()}.zip",
                        mime="application/zip",
                    )

                st.success("MDX Repository processed successfully!")
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")

# ========== Processing Zendesk (CSV) ==========
elif import_source == "Zendesk (CSV)":
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            st.write("CSV File Preview:")
            st.dataframe(df)

            # Check for required columns
            required_columns = ["Article Body", "Section", "Article Title"]
            if all(col in df.columns for col in required_columns):
                st.success("Found required columns!")
                
                # Button to generate Markdown files
                if st.button("Generate Markdown Files"):
                    with tempfile.TemporaryDirectory() as temp_dir:
                        summary_structure = {}

                        for index, row in df.iterrows():
                            title = row["Article Title"]
                            body = row["Article Body"]
                            section = row["Section"]

                            # Clean title for filenames
                            title = re.sub(r'\d+', '', title)
                            safe_title = "".join(c for c in title if c.isalnum() or c in " -_").rstrip()
                            safe_title = safe_title.replace(" ", "-").lower()
                            filename = f"{safe_title or 'article'}.md"

                            # Create section folder
                            safe_section = section.replace(" ", "-").lower()
                            section_folder = Path(temp_dir) / safe_section
                            section_folder.mkdir(parents=True, exist_ok=True)

                            # Convert to Markdown
                            markdown_content = f"# {title}\n\n{body}"

                            # Save Markdown file
                            file_path = section_folder / filename
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.write(markdown_content)

                            # Update summary
                            if section not in summary_structure:
                                summary_structure[section] = []
                            summary_structure[section].append((title, f"{safe_section}/{filename}"))

                        # Create SUMMARY.md
                        summary_content = "# Summary\n\n"
                        for section, pages in summary_structure.items():
                            summary_content += f"## {section}\n"
                            for page_title, page_path in pages:
                                summary_content += f"* [{page_title}]({page_path})\n"
                            summary_content += "\n"

                        summary_file_path = Path(temp_dir) / "SUMMARY.md"
                        with open(summary_file_path, "w", encoding="utf-8") as summary_file:
                            summary_file.write(summary_content)

                        # Create ZIP file
                        zip_buffer = BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                            for root, _, files in os.walk(temp_dir):
                                for file_name in files:
                                    full_path = Path(root) / file_name
                                    arcname = full_path.relative_to(temp_dir)
                                    zipf.write(full_path, arcname)

                        zip_buffer.seek(0)

                        # Provide download button
                        st.success("Markdown files generated successfully!")
                        st.download_button(
                            label="Download ZIP file",
                            data=zip_buffer,
                            file_name="zendesk_markdown.zip",
                            mime="application/zip",
                        )
            else:
                st.error("CSV file must contain `Article Body`, `Section`, and `Article Title` columns.")
        except Exception as e:
            st.error(f"An error occurred: {e}")
