package main

import (
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
	"strings"

	md "github.com/JohannesKaufmann/html-to-markdown"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage:")
		fmt.Println("  Convert a single file:")
		fmt.Println("    go run main.go <input.html> [output.md]")
		fmt.Println("  Convert all HTML files in a directory:")
		fmt.Println("    go run main.go <input-directory> <output-directory>")
		fmt.Println("\nExamples:")
		fmt.Println("  go run main.go page.html page.md")
		fmt.Println("  go run main.go ./html-files ./markdown-files")
		os.Exit(1)
	}

	inputPath := os.Args[1]

	// Check if input is a file or directory
	info, err := os.Stat(inputPath)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		os.Exit(1)
	}

	converter := md.NewConverter("", true, nil)

	if info.IsDir() {
		// Directory mode
		if len(os.Args) < 3 {
			fmt.Println("Error: Output directory required when input is a directory")
			os.Exit(1)
		}
		outputDir := os.Args[2]
		convertDirectory(converter, inputPath, outputDir)
	} else {
		// Single file mode
		outputPath := ""
		if len(os.Args) >= 3 {
			outputPath = os.Args[2]
		} else {
			// Auto-generate output filename
			outputPath = strings.TrimSuffix(inputPath, filepath.Ext(inputPath)) + ".md"
		}
		convertFile(converter, inputPath, outputPath)
	}
}

func convertFile(converter *md.Converter, inputPath, outputPath string) {
	fmt.Printf("Converting: %s -> %s\n", inputPath, outputPath)

	// Read HTML file
	htmlContent, err := ioutil.ReadFile(inputPath)
	if err != nil {
		fmt.Printf("Error reading file: %v\n", err)
		return
	}

	// Convert to Markdown
	markdown, err := converter.ConvertString(string(htmlContent))
	if err != nil {
		fmt.Printf("Error converting: %v\n", err)
		return
	}

	// Write Markdown file
	err = ioutil.WriteFile(outputPath, []byte(markdown), 0644)
	if err != nil {
		fmt.Printf("Error writing file: %v\n", err)
		return
	}

	fmt.Printf("Successfully converted to: %s\n", outputPath)
}

func convertDirectory(converter *md.Converter, inputDir, outputDir string) {
	// Create output directory if it doesn't exist
	err := os.MkdirAll(outputDir, 0755)
	if err != nil {
		fmt.Printf("Error creating output directory: %v\n", err)
		os.Exit(1)
	}

	// Walk through input directory
	err = filepath.Walk(inputDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		// Skip directories
		if info.IsDir() {
			return nil
		}

		// Only process .html files
		if !strings.HasSuffix(strings.ToLower(path), ".html") {
			return nil
		}

		// Calculate relative path and output path
		relPath, err := filepath.Rel(inputDir, path)
		if err != nil {
			return err
		}

		outputPath := filepath.Join(outputDir, strings.TrimSuffix(relPath, ".html")+".md")

		// Create subdirectories if needed
		outputSubDir := filepath.Dir(outputPath)
		if err := os.MkdirAll(outputSubDir, 0755); err != nil {
			return err
		}

		convertFile(converter, path, outputPath)
		return nil
	})

	if err != nil {
		fmt.Printf("Error walking directory: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("\nBatch conversion completed!")
}
