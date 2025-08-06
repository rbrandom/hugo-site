# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Hugo Academic Website

This is a Hugo-based academic website using the PaperMod theme, designed for academic professionals to showcase courses. The site is deployed via Netlify at https://spaceofreasons.netlify.app.

## Development Commands

### Local Development
- `hugo server` - Start local development server at http://localhost:1313
- `hugo server --buildDrafts` - Include draft content in local preview

### Build and Deploy  
- `hugo` - Build static site to `public/` directory
- Built site is automatically deployed to Netlify when pushed to main branch

### Content Management
- `hugo new courses/course-name/index.md` - Create new course entry

## Site Architecture

### Content Structure
The site follows Hugo's content organization with one main section:

- **Courses** (`content/courses/`) - Course materials with meeting folders containing PDFs and handouts

Each course uses bundle structure (index.md + assets in same folder).

### Theme Customization
- Uses PaperMod theme located in `themes/PaperMod/`
- Custom layouts in `layouts/` override theme defaults
- Profile mode enabled showing author bio and navigation buttons
- Math rendering enabled via KaTeX

### Configuration
- Main config in `config.yml` with site metadata, navigation, and theme parameters
- Base URL: https://spaceofreasons.netlify.app
- Social icons configured for CV, email, publications, etc.
- Main sections: courses

### Static Assets
- Static files in `static/` (PDFs, images, favicon)
- Generated images and resources in `resources/_gen/`
- Built site output in `public/` (ignored in git)

## Content Types

### Courses  
- Located in `content/courses/course-name/`
- Meeting folders (`meeting1/`, `meeting2/`, etc.) contain session materials
- PDFs for handouts, notes, readings organized by week/meeting

## Content Management System

### Sveltia CMS
- CMS configuration in `static/admin/config.yml`
- Manages only Courses collection after simplification
- Access via `/admin` route when deployed
- Known issue: CMS prepends `https://` to relative links - use `./filename.pdf` syntax to prevent this

## Development Notes

- Hugo minimum version: 0.112.4 (theme requirement)  
- Markup rendering allows unsafe HTML for academic formatting
- Table of contents configured for h2-h3 headings
- Syntax highlighting with autumn theme
- No build tools like npm/package.json - pure Hugo site