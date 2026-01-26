Choose Your Setup
Python
API

Install the package
Terminal window
pip install llama-cloud-services

Parse from CLI
You can parse your first PDF file using the command line interface. Use the command llama-parse [file_paths]. See the help text with llama-parse --help.
Terminal window
export LLAMA_CLOUD_API_KEY='llx-...'

# output as text

llama-parse my_file.pdf --result-type text --output-file output.txt

# output as markdown

llama-parse my_file.pdf --result-type markdown --output-file output.md

# output as raw json

llama-parse my_file.pdf --output-raw-json --output-file output.json

Parse in Python
You can also create simple scripts:
from llama_cloud_services import LlamaParse

parser = LlamaParse(
api_key="llx-...", # can also be set in your env as LLAMA_CLOUD_API_KEY
num_workers=4, # if multiple files passed, split in `num_workers` API calls
verbose=True,
language="en", # optionally define a language, default=en
)

# sync

result = parser.parse("./my_file.pdf")

# sync batch

results = parser.parse(["./my_file1.pdf", "./my_file2.pdf"])

# async

result = await parser.aparse("./my_file.pdf")

# async batch

results = await parser.aparse(["./my_file1.pdf", "./my_file2.pdf"])

The result object is a fully typed JobResult object. You can interact with it to parse and transform various parts of the result:

# get the llama-index markdown documents

markdown_documents = result.get_markdown_documents(split_by_page=True)

# get the llama-index text documents

text_documents = result.get_text_documents(split_by_page=False)

# get the image documents

image_documents = result.get_image_documents(
include_screenshot_images=True,
include_object_images=False, # Optional: download the images to a directory # (default is to return the image bytes in ImageDocument objects)
image_download_dir="./images",
)

# access the raw job result

# Items will vary based on the parser configuration

for page in result.pages:
print(page.text)
print(page.md)
print(page.images)
print(page.layout)
print(page.structuredData)

That’s it! Take a look at the examples below or head to the Python client docs .
Examples
Several end-to-end indexing examples can be found in the Client’s examples folder:
Result Object Tour
Getting Started
Advanced RAG Example

Parsing options
Set language
LlamaParse uses OCR to extract text from images. Our OCR supports a long list of languages. You can specify one or more languages by separating them with a comma. This only affects text extracted from images.
Python
API
Terminal window
curl -X 'POST' \
 'https://api.cloud.llamaindex.ai/api/v1/parsing/upload' \
 -H 'accept: application/json' \
 -H 'Content-Type: multipart/form-data' \
 -H "Authorization: Bearer $LLAMA_CLOUD_API_KEY" \
 --form 'language="fr"' \
 -F 'file=@/path/to/your/file.pdf;type=application/pdf'

Disable OCR
By default, LlamaParse runs OCR on images embedded in the document. You can disable it with disable_ocr=True.
Python
API
parser = LlamaParse(
disable_ocr=True
)

Skip diagonal text
By default, LlamaParse will attempt to parse text that is diagonal on the page. This can be useful for some documents, but also introduce noise and errors. To avoid parsing diagonal text, set skip_diagonal_text=True.
Python
API
parser = LlamaParse(
skip_diagonal_text=True
)

Do not unroll columns
By default, LlamaParse tries to unroll columns into reading order. Set do_not_unroll_columns=True to prevent LlamaParse from doing so.
Python
API
parser = LlamaParse(
do_not_unroll_columns=True
)

Target pages
By default, all pages will be extracted. To parse specific pages only, use a comma-separated string. Page numbering starts at 0.
Python
API
parser = LlamaParse(
target_pages="0,2,7"
)

Page separator
By default, LlamaParse will separate pages in the markdown and text output by \n---\n. You can change this separator by setting page_separator to the desired string.
It’s also possible to include the page number within the separator using {pageNumber} in the string. It will be replaced by the page number of the next page.
Python
API
parser = LlamaParse(
page_separator="\n=================\n",

# page_separator="\n== {pageNumber} ==\n" # Will transform to "\n== 4 ==\n" to separate page 3 and 4.

)

Page prefix and suffix
It’s possible to specify a prefix or a suffix to be added to each page. These strings can contain {pageNumber} as well and will be replaced by the current page number. Both parameters are optional and empty by default.
Python
API
parser = LlamaParse(
page_prefix="START OF PAGE: {pageNumber}\n"
page_suffix="\nEND OF PAGE: {pageNumber}"
)

Bounding box
Specify an area of a document that you want to parse. This can be helpful to remove headers and footers. To do so you need to provide the bounding box margin in clockwise order from the top in a comma-separated. The margins are expressed as a fraction of the page size, a number between 0 and 1.
Examples:
To exclude the top 10% of a document: bounding_box=“0.1,0,0,0”
To exclude the top 10% and bottom 20% of a document: bounding_box=“0.1,0,0.2,0”
Python
API
parser = LlamaParse(
bounding_box="0.1,0,0.2,0"
)

Take screenshot
Take a screenshot of each page and add it to JSON output in the following format:
{
"images": [
{
"name": "page_1.jpg",
"height": 792,
"width": 612,
"x": 0,
"y": 0,
"type": "full_page_screenshot"
}
]
}

Python
API
parser = LlamaParse(
take_screenshot=True
)

Disable image extraction
It is possible to disable the extraction of image for better performance using disable_image_extraction=true
Python
API
parser = LlamaParse(
disable_image_extraction=True
)

Extract multiple table per sheet in spreadsheet
By default LlamaParse extract each sheet of a spreadsheet as one table. Using spreadsheet_extract_sub_tables=true, LlamaParse will try to identify spreadsheet sheet with multiple table and return them as separated tables.
Python
API
parser = LlamaParse(
spreadsheet_extract_sub_tables=True
)

Force re-computation of cells containing formulas in spreadsheet
By default, for spreadsheet cells containing formulas, LlamaParse extracts cached (pre-computed) values if a cached cell value exists in the document. When spreadsheet_force_formula_computation=true, LlamaParse will re-compute values for all spreadsheet cells containing formulas.
Python
API
parser = LlamaParse(
spreadsheet_force_formula_computation=True
)

Note that using spreadsheet_force_formula_computation=true will have a negative performance impact when parsing spreadsheets containing formulas.

Output table as HTML in markdown
A common issue with markdown table is that they do not handle merged cells well. It is possible to ask LlamaParse to return table as html with colspan and rowspan to get a better representation of the table. When output_tables_as_HTML=true, tables present in the markdown will be output as HTML tables.
Python
API
parser = LlamaParse(
output_tables_as_HTML=True
)

Preserve alignment across pages
If set to preserve_layout_alignment_across_pages=True will try to keep the text align in text mode accross pages. Useful for document with continuous table / alignment accross pages.
Python
API
parser = LlamaParse(
preserve_layout_alignment_across_pages=True
)

Preserve very small text
If set to preserve_very_small_text=True, LlamaParse will try to preserve very small text lines. This can be useful for documents containing vector graphics with very small text lines that may not be recognized by OCR or a vision model (such as in CAD drawings).
Python
API
parser = LlamaParse(
preserve_very_small_text=True
)

Hide headers
When set to true, LlamaParse will try to not output page headers in the Markdown output. The removed headers will be present in the JSON object inside the pageHeaderMarkdown field if needed.
LlamaParse will use different techniques to identify the headers of the page based on the chosen mode; headers will not be detected in Fast Mode.
Python
API
parser = LlamaParse(
hide_headers=True
)

Hide footers
When set to true, LlamaParse will try to not output page footers in the Markdown output. The removed footers will be present in the JSON object inside the pageFooterMarkdown field if needed.
LlamaParse will use different techniques to identify the footers of the page based on the chosen mode; footers will not be detected in Fast Mode.
Python
API
parser = LlamaParse(
hide_footers=True
)

Page header/footer prefix/suffix
LlamaParse allows you to prefix/suffix the headers/footers of a page’s Markdown with a string. This allows control of how headers/footers are displayed in the Markdown.
It is possible to set them using the following properties:
page_header_prefix : Allows you to define the prefix to put before the page header
page_header_suffix : Allows you to define the suffix to put after the page header
page_footer_prefix : Allows you to define the prefix to put before page footer
page_footer_suffix :Allows you to define the suffix to put after page footer
Note that headers and footers will not be detected in Fast Mode, so these parameters will have no effect.
Python
API
parser = LlamaParse(
page_header_prefix="[Header]",
page_header_suffix="[/Header]",
page_footer_prefix="[Footer]",
page_footer_suffix="[/Footer]"
)

With such a query the markdown for a page where header and footer are detected will look like:
[Header]
Journal of computer science, April 3 2025 edition
[/Header]

Some content

[Footer]
All right reserved, Corp Inc.
Page 2
[/Footer]

Merge tables across pages in markdown
When set to true, LlamaParse will try to merge table across pages in the output markdown when it make sense. As a result the markdown will not be paginated, and all footer and headers will be removed.
Python
API
parser = LlamaParse(
merge_tables_across_pages_in_markdown=True
)

Extract out of bounds content in presentation slides
When set to true, for supported presentation formats, LlamaParse will extract out of bounds content from slides. By default, out of bounds content is not extracted.
Python
API
parser = LlamaParse(
presentation_out_of_bounds_content=True
)

Currently supported formats for out of bounds slide content extraction:
.pptx (PowerPoint 2007+)
