import re
import os
import sys

def inline_resources(html_file):
    # Read the original HTML content.
    with open(html_file, "r", encoding="utf-8") as f:
        html = f.read()

    # Get the directory of the HTML file to resolve relative paths.
    html_dir = os.path.dirname(os.path.abspath(html_file))

    # Replace <script src="..."></script> with inline script tag.
    def replace_script(match):
        src = match.group(1)
        file_path = os.path.join(html_dir, src)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Create an inline script tag.
            return f"<script>\n{content}\n</script>"
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            # Return the original tag if file not found.
            return match.group(0)

    # The regex matches a script tag with a src attribute.
    html = re.sub(r'<script\s+src="([^"]+)"></script>', replace_script, html)

    # Replace <link rel="stylesheet" href="..."> with inline style tag.
    def replace_link(match):
        href = match.group(1)
        file_path = os.path.join(html_dir, href)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Create an inline style tag.
            return f"<style>\n{content}\n</style>"
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            # Return the original tag if file not found.
            return match.group(0)

    # The regex matches a link tag for stylesheets.
    html = re.sub(r'<link\s+rel="stylesheet"\s+href="([^"]+)"\s*/?>', replace_link, html)

    return html

if __name__ == "__main__":
    # Change the cd to the directory of this script.
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Usage: python inline_html.py [input.html] [output.html]
    input_file = sys.argv[1] if len(sys.argv) > 1 else "index.html"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "index_packed.html"

    new_html = inline_resources(input_file)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(new_html)

    print(f"Written output to {output_file}")
