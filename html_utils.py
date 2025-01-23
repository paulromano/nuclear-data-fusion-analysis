import nbformat
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell
from bs4 import BeautifulSoup


def inline_pandas_styles(html):
    """
    Takes an HTML string (typically from pandas .to_html()) that includes
    a <style> block with ID-based rules, and converts those rules to
    inline 'style' attributes on the relevant elements. The original
    <style> block(s) and IDs are removed.
    """

    soup = BeautifulSoup(html, "html.parser")

    # 1. Find and process all <style> tags
    style_tags = soup.find_all("style")
    for style_tag in style_tags:
        style_text = style_tag.string
        if not style_text:
            # Remove empty or invalid <style> tags
            style_tag.decompose()
            continue

        # Split style text by '}' to get individual rules
        # Each block looks like: "#id1, #id2 { color: #000; background-color: #fff; }"
        rules = style_text.split("}")
        for rule in rules:
            rule = rule.strip()
            if not rule:
                continue

            # Split each rule into selector part and declaration part
            if "{" not in rule:
                continue
            selector_part, declaration_part = rule.split("{", 1)
            selector_part = selector_part.strip()
            declaration_part = declaration_part.strip().rstrip(";")

            # Parse the selectors (comma-separated)
            selectors = [sel.strip() for sel in selector_part.split(",") if sel.strip()]

            # Parse the declarations (semi-colon separated)
            # e.g. "background-color: #f7f6f6; color: #000000"
            declarations_list = [decl.strip() for decl in declaration_part.split(";") if decl.strip()]

            # Turn the declarations into a dictionary, e.g. {'background-color': '#f7f6f6', 'color': '#000000'}
            style_dict = {}
            for decl in declarations_list:
                if ":" not in decl:
                    continue
                prop, val = decl.split(":", 1)
                style_dict[prop.strip()] = val.strip()

            # 2. Apply the inline styles to the matching elements (by ID)
            for selector in selectors:
                # We only handle ID selectors of the form "#something"
                if selector.startswith("#"):
                    elem_id = selector[1:]
                    element = soup.find(id=elem_id)
                    if not element:
                        continue

                    # Merge with existing inline style if present
                    existing_style = element.get("style", "")
                    # Convert existing style into a dict for proper merging (simple approach here)
                    # For simplicity, we just append. If you need real merging, you'd parse properly.
                    for prop, val in style_dict.items():
                        # If you want to avoid duplicating properties, you'd parse existing_style here.
                        existing_style += f"{prop}: {val}; "

                    # Update or set the style attribute
                    element["style"] = existing_style.strip()

        # Remove the style tag after processing
        style_tag.decompose()

    # 3. Remove id attributes entirely (so they don't clutter the final HTML)
    for elem in soup.find_all():
        if elem.has_attr("id"):
            del elem["id"]

    return str(soup)



def create_notebook_with_html_output(html_str, notebook_path):
    """
    Creates a Jupyter notebook at `notebook_path` with one code cell.
    That cell outputs the given HTML string when run.

    :param html_str: The HTML content you want to display.
    :param notebook_path: Filename/path for the .ipynb to create.
    """

    # Create a new (empty) notebook
    nb = new_notebook()

    # Optionally, you could just create a Markdown cell that *includes* HTML inline:
    # markdown_content = f"Below is some raw HTML:\n\n```html\n{html_str}\n```\n\nOr direct usage:\n\n{html_str}"
    nb.cells.append(new_markdown_cell(html_str))

    # Write the notebook to disk
    with open(notebook_path, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)
