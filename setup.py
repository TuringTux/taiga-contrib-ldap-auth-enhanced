#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='taiga-contrib-ldap-auth-enhanced',
    version=":versiontools:taiga-contrib-ldap-auth-enhanced:",
    description="Enhaned Taiga plugin for LDAP authentication",
    long_description="Extended Taiga plugin for LDAP authentication. Fork of monogramm/taiga-contrib-ldap-auth-ext (which is a fork of ensky/taiga-contrib-ldap-auth) with several extensions.",
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
