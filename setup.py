import setuptools

with open("README.md", "r") as file:
    long_description = file.read()

setuptools.setup(
    name='atlassian-api-py',
    version='0.0.3',
    description='Atlassian REST API Python Wrapper.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/shenxianpeng/atlassian-api-py',
    author='Xianpeng Shen',
    author_email='xianpeng.shen@qq.com',
    keywords=['atlassian', 'jira', 'rest', 'api'],
    python_requires='>=3',
    license='Apache License 2.0',
    packages=setuptools.find_packages(exclude=["tests"]),
    project_urls={
        "Source": "https://github.com/shenxianpeng/atlassian-api-py",
        # "Documentation": "https://github.com/shenxianpeng/atlassian-api-py/docs/atlassian.html",
        "Tracker": "https://github.com/shenxianpeng/atlassian-api-py/issues"
    },
    install_requires=['requests'],
    classifiers=[
        # https://pypi.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Information Technology',
        'Natural Language :: English',
        'Natural Language :: Chinese (Simplified)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities',
        'Topic :: Internet',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Libraries :: Application Frameworks'
    ]
)
