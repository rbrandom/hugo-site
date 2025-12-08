# HTML to Markdown Converter

This tool converts HTML files to Markdown format using the [html-to-markdown](https://github.com/JohannesKaufmann/html-to-markdown) library.

## Prerequisites

You need to have Go installed on your system. Download it from [golang.org](https://golang.org/dl/).

## Setup

1. Navigate to this directory:
   ```bash
   cd tools/html-to-md
   ```

2. Install dependencies:
   ```bash
   go mod download
   ```

## Usage

### Convert a Single File

```bash
# Specify both input and output files
go run main.go input.html output.md

# Auto-generate output filename (input.html -> input.md)
go run main.go input.html
```

### Convert All HTML Files in a Directory

```bash
go run main.go /path/to/html-files /path/to/output-markdown
```

This will:
- Find all `.html` files in the input directory (including subdirectories)
- Convert them to Markdown
- Save them with `.md` extension in the output directory
- Preserve the directory structure

## Examples

### Example 1: Convert a single HTML file
```bash
go run main.go ../../content/courses/old-syllabus.html ../../content/courses/syllabus.md
```

### Example 2: Batch convert HTML files
```bash
# Convert all HTML files from a folder
go run main.go ~/Downloads/html-content ../../content/courses/converted
```

### Example 3: Quick conversion
```bash
# Just provide input file, output will be auto-named
go run main.go page.html
# Creates: page.md
```

## Building a Standalone Binary

If you want to compile the tool for repeated use:

```bash
go build -o html2md
```

Then use it directly:
```bash
./html2md input.html output.md
```

## Notes

- Only files with `.html` extension are processed in directory mode
- Output directories are created automatically if they don't exist
- Existing files will be overwritten
- The converter preserves most HTML structure in Markdown format
