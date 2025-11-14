from setuptools import find_packages
from setuptools import setup


long_description = "\n\n".join(
    [
        open("README.rst").read(),
        open("CHANGES.rst").read(),
    ]
)


setup(
    name="recensio.plone",
    version="2.0.0.dev0",
    description="Base package of the Recensio Plone portal.",
    long_description=long_description,
    # Get more from https://pypi.org/classifiers/
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: Addon",
        "Framework :: Plone :: 6.1",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
    keywords="Python Plone CMS",
    author="Syslab.com GmbH",
    author_email="info@syslab.com",
    url="https://github.com/syslabcom/recensio.plone",
    project_urls={
        "Source": "https://github.com/syslabcom/recensio.plone",
        "Tracker": "https://github.com/syslabcom/recensio.plone/issues",
    },
    license="GPL version 2",
    packages=find_packages("src"),
    namespace_packages=["recensio"],
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.10",
    install_requires=[
        "setuptools",
        "beautifulsoup4",
        "collective.solr",
        "eea.facetednavigation",
        "ftw.upgrade>=3.4.0a0",
        "guess-language>0.2",
        "plone.api",
        "plone.app.discussion",
        "collective.solr>=10.0.0.dev0",
        "collective.vdexvocabulary",
        "collective.z3cform.datagridfield",
        "pypdf",
        "reportlab",
        "xlrd",
        "z3c.jbot",
    ],
    extras_require={
        "test": [
            "plone.app.testing",
            "plone.testing>=5.0.0",
            "plone.app.contenttypes[test]",
        ],
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
