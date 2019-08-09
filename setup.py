#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from setuptools import setup, find_packages, Command

__version__ = "0.6.0"


class Docs(Command):
    description = "Generate & optionally upload documentation to docs server"
    user_options = [("upload", None, "Upload to BBP internal docs server")]
    finalize_options = lambda self: None

    def initialize_options(self):
        self.upload = False

    def run(self):
        self._create_metadata_file()
        self.reinitialize_command('build_ext', inplace=1)
        self.run_command('build_ext')
        self.run_command('build_sphinx')  # requires metadata file
        if self.upload:
            self._upload()

    def _create_metadata_file(self):
        import textwrap
        import time
        md = self.distribution.metadata
        with open("docs/metadata.md", "w") as mdf:
            mdf.write(textwrap.dedent(f"""\
                ---
                name: {md.name}
                version: {md.version}
                description: {md.description}
                homepage: {md.url}
                license: {md.license}
                maintainers: {md.author}
                repository: {md.project_urls.get("Source", '')}
                issuesurl: {md.project_urls.get("Tracker", '')}
                contributors: {md.maintainer}
                updated: {time.strftime("%d/%m/%Y")}
                ---
                """))

    def _upload(self):
        from docs_internal_upload import docs_internal_upload
        print("Uploading....")
        docs_internal_upload("docs/_build/html", metadata_path="docs/metadata.md")


def setup_package():
    docs_require = ["sphinx-limestone-theme", "docs_internal_upload"]
    maybe_docs_reqs = docs_require if "docs" in sys.argv else []
    maybe_test_runner = ['pytest-runner'] if "test" in sys.argv else []

    setup(
        name='neurodamus',
        version=__version__,
        packages=find_packages(exclude=["tests"]),
        install_requires=[
            'NEURON',
            'h5py',
            'enum34;python_version<"3.4"',
            'lazy-property',
            'docopt',
            'six',
        ],
        setup_requires=maybe_docs_reqs + maybe_test_runner,
        tests_require=["pytest"],
        extras_require=dict(
            plotting=['matplotlib'],
            full=['matplotlib'],
        ),
        cmdclass=dict(
            docs=Docs
        ),
        entry_points=dict(
            console_scripts=[
                'neurodamus = neurodamus.commands:neurodamus'
            ]
        ),
        dependency_links=[
            "https://bbpteam.epfl.ch/repository/devpi/simple/sphinx-limestone-theme/",
            "https://bbpteam.epfl.ch/repository/devpi/simple/docs_internal_upload"
        ]
    )


if __name__ == "__main__":
    setup_package()
