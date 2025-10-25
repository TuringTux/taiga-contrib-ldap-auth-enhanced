#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from pathlib import Path

# See https://github.com/pypa/sampleproject/blob/db5806e0a3204034c51b1c00dde7d5eb3fa2532e/setup.py
repo_dir = Path(__file__).parent
long_description = (repo_dir / "README.md").read_text(encoding="utf-8")

setup(
    name='taiga-contrib-ldap-auth-enhanced',
    version=":versiontools:taiga_contrib_ldap_auth_enhanced:",
    description="LDAP authentication plugin for self-hosted Taiga.io project management instances",
    long_description=long_description,
    keywords='taiga, ldap, auth, plugin',
    author='TuringTux',
    author_email='hi@turingtux.me',
    url='https://github.com/TuringTux/taiga-contrib-ldap-auth-enhanced',
    license='AGPL',
    include_package_data=True,
    packages=find_packages(),
    install_requires=[
        'django >= 1.7',
        'ldap3 >= 0.9.8.4'
    ],
    setup_requires=[
        'versiontools >= 1.8',
    ],
    classifiers=[
        "Programming Language :: Python",
        'Development Status :: 5 - Production/Stable',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
