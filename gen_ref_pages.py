# Code taken from https://mkdocstrings.github.io/recipes/

"""Generate the code reference pages and navigation."""

from pathlib import Path

import mkdocs_gen_files

nav = mkdocs_gen_files.Nav()

for path in sorted(Path("cli/medperf").rglob("*.py")):
    module_path = path.relative_to("cli/medperf").with_suffix("")
    doc_path = path.relative_to("cli/medperf").with_suffix(".md")
    full_doc_path = Path("cli/reference", doc_path)

    parts = tuple(module_path.parts)

    if parts[-1] == "__init__":
        parts = parts[:-1]
    elif parts[-1] == "__main__":
        continue
    if parts == ():
        continue

    print(full_doc_path)
    print(nav)
    print(doc_path)
    print(parts)
    nav[parts] = str(doc_path)  #

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        ident = ".".join(parts)
        fd.write(f"::: {ident}")

    mkdocs_gen_files.set_edit_path(full_doc_path, path)

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:  #

    nav_file.writelines(nav.build_literate_nav())  #
