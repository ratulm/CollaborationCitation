#!/usr/bin/env python3
"""Convert analysis.md to analysis.html with custom styling."""

import markdown
import sys
from pathlib import Path

def convert_md_to_html(md_file: str, html_file: str):
    """Convert markdown file to HTML with custom CSS."""
    
    # Read markdown content
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convert markdown to HTML
    html_body = markdown.markdown(
        md_content,
        extensions=['extra', 'nl2br', 'sane_lists']
    )
    
    # CSS styling
    css = """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f8f9fa;
            padding: 20px;
        }

        p {
            margin-bottom: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 40px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
        }

        h1 {
            font-size: 2.5em;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 10px;
            text-align: center;
        }

        h1 + p em {
            font-size: 1.1em;
            color: #6c757d;
            font-weight: 400;
            display: block;
            text-align: center;
            margin-bottom: 30px;
        }

        h2 {
            font-size: 1.8em;
            font-weight: 600;
            color: #2c3e50;
            margin-top: 50px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid #e9ecef;
        }

        h3 {
            font-size: 1.3em;
            font-weight: 600;
            color: #495057;
            margin-top: 40px;
            margin-bottom: 15px;
        }

        hr {
            border: none;
            border-top: 2px solid #e9ecef;
            margin: 30px 0;
        }

        blockquote {
            background-color: #f8f9fa;
            padding: 20px;
            border-left: 4px solid #007bff;
            margin: 20px 0;
            border-radius: 4px;
        }

        blockquote p {
            margin-bottom: 10px;
            color: #495057;
        }

        blockquote p:last-child {
            margin-bottom: 0;
        }

        img {
            max-width: 50%;
            height: auto;
            display: block;
            margin: 30px auto;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }

        p:has(img) + p em {
            display: block;
            text-align: center;
            margin-top: 15px;
            font-size: 0.95em;
            color: #6c757d;
        }

        .grid-container {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 30px;
            margin: 30px 0;
        }

        .grid-container img {
            max-width: 100%;
            margin: 10px auto;
        }

        .grid-container p {
            text-align: center;
            margin-bottom: 10px;
        }

        .grid-container p em {
            margin-top: 10px;
            font-size: 0.9em;
        }

        @media print {
            body {
                background-color: white;
                padding: 0;
            }
            
            .container {
                box-shadow: none;
                padding: 20px;
            }
        }

        @media (max-width: 768px) {
            .container {
                padding: 20px;
            }

            h1 {
                font-size: 2em;
            }

            h2 {
                font-size: 1.5em;
            }

            .grid-container {
                grid-template-columns: 1fr;
                gap: 20px;
            }

            img {
                max-width: 100%;
            }
        }
    """
    
    # Extract title from first H1 in markdown
    title = "Document"
    lines = md_content.split('\n')
    for line in lines:
        if line.startswith('# '):
            title = line[2:].strip()
            break
    
    # Complete HTML template
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
{css}
    </style>
</head>
<body>
    <div class="container">
{html_body}
    </div>
</body>
</html>
"""
    
    # Write HTML file
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"Converted {md_file} to {html_file}")

if __name__ == "__main__":
    md_file = "analysis.md"
    html_file = "analysis.html"
    
    if len(sys.argv) > 1:
        md_file = sys.argv[1]
    if len(sys.argv) > 2:
        html_file = sys.argv[2]
    
    convert_md_to_html(md_file, html_file)
