# Code taken from https://mkdocstrings.github.io/recipes/

"""Generate the code reference pages and navigation."""

from pathlib import Path

import mkdocs_gen_files

nav = mkdocs_gen_files.Nav()

build_params = [
    ("cli/medperf", "cli/medperf", "cli/medperf", "reference"),
    # ("server", "server", "", "reference"),
]

exclude_paths = ["tests", "templates", "logging"]

for path, mod, doc, full_doc in build_params:
    for path in sorted(Path(path).rglob("*.py")):
        module_path = path.relative_to(mod).with_suffix("")
        doc_path = path.relative_to(doc).with_suffix(".md")
        full_doc_path = Path(full_doc, doc_path)

        parts = tuple(module_path.parts)

        if parts[-1] == "__init__":
            parts = parts[:-1]
            continue
        elif parts[-1] in ["__main__", "setup"]:
            continue
        if parts == ():
            continue
        if parts[0] in exclude_paths:
            continue

        nav[parts] = str(doc_path)  #

        with mkdocs_gen_files.open(full_doc_path, "w") as fd:
            ident = ".".join(parts)
            fd.write(f"::: {ident}")

        mkdocs_gen_files.set_edit_path(full_doc_path, path)

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:  #

    nav_file.writelines(nav.build_literate_nav())  #
