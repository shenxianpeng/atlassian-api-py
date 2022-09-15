"""Python Wrapper for Atlassian REST API"""
import setuptools


with open("README.md", "r") as file:
    long_description = file.read()

setuptools.setup(
    name="atlassian-api-py",
    version="0.4.0",
    description="Python Wrapper for Atlassian REST API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    # url='https://github.com/shenxianpeng/atlassian-api-py',
    author="Peter Shen",
    author_email="xianpeng.shen@gmail.com",
    keywords=["atlassian", "jira", "bitbucket", "rest", "api"],
    python_requires=">=3",
    license="MIT License",
    packages=setuptools.find_packages(exclude=["tests"]),
    project_urls={
        "Download": "https://pypi.org/project/atlassian-api-py/#files",
        # "Source": "https://github.com/shenxianpeng/atlassian-api-py",
        # "Documentation": "https://github.com/shenxianpeng/atlassian-api-py/docs/atlassian.html",
        # "Tracker": "https://github.com/shenxianpeng/atlassian-api-py/issues"
    },
    install_requires=["requests"],
    classifiers=[
        # https://pypi.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Information Technology",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6",
        "Topic :: Utilities",
        "Topic :: Internet",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
)
