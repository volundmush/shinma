import os
import sys
from setuptools import setup, find_packages

os.chdir(os.path.dirname(os.path.realpath(__file__)))

VERSION_PATH = os.path.join("shinma", "VERSION.txt")
OS_WINDOWS = os.name == "nt"


def get_requirements():
    """
    To update the requirements for Shinma, edit the requirements.txt file.
    """
    with open("requirements.txt", "r") as f:
        req_lines = f.readlines()
    reqs = []
    for line in req_lines:
        # Avoid adding comments.
        line = line.split("#")[0].strip()
        if line:
            reqs.append(line)
    return reqs


def get_version():
    """
    When updating the Evennia package for release, remember to increment the
    version number in evennia/VERSION.txt
    """
    return open(VERSION_PATH).read().strip()


def get_scripts():
    """
    Determine which executable scripts should be added. For Windows,
    this means creating a .bat file.
    """
    if OS_WINDOWS:
        batpath = os.path.join("bin", "windows", "shinma.bat")
        scriptpath = os.path.join(sys.prefix, "Scripts", "shinma_launcher.py")
        with open(batpath, "w") as batfile:
            batfile.write('@"%s" "%s" %%*' % (sys.executable, scriptpath))
        return [batpath, os.path.join("bin", "windows", "shinma_launcher.py")]
    else:
        return [os.path.join("bin", "unix", "shinma")]


def package_data():
    """
    By default, the distribution tools ignore all non-python files.

    Make sure we get everything.
    """
    file_set = []
    for root, dirs, files in os.walk("shinma"):
        for f in files:
            if ".git" in f.split(os.path.normpath(os.path.join(root, f))):
                # Prevent the repo from being added.
                continue
            file_name = os.path.relpath(os.path.join(root, f), "shinma")
            file_set.append(file_name)
    return file_set


# setup the package
setup(
    name="shinma",
    version=get_version(),
    author="Volund",
    maintainer="Volund",
    url="https://github.com/volundmush/shinma",
    description="",
    license="BSD",
    long_description="""
    
    """,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    scripts=get_scripts(),
    install_requires=get_requirements(),
    package_data={"": package_data()},
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: JavaScript",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: BSD License",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Topic :: Database",
        "Topic :: Education",
        "Topic :: Games/Entertainment :: Multi-User Dungeons (MUD)",
        "Topic :: Games/Entertainment :: Puzzle Games",
        "Topic :: Games/Entertainment :: Role-Playing",
        "Topic :: Games/Entertainment :: Simulation",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Server",
    ],
    python_requires=">=3.8",
    project_urls={
        "Source": "https://github.com/volundmush/shinma",
        "Issue tracker": "https://github.com/volundmush/shinma/issues",
        "Patreon": "https://www.patreon.com/volund",
    },
)
