import os
from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-offermaker',
    version='0.9.1',
    packages=['offermaker'],
    include_package_data=True,
    license='LGPL',
    description='Django application that allows creation, preview and usage of custom multivariant restrictions applied on the forms.',
    long_description=README,
    url='http://offermaker.kjw.pt',
    author='Kamil Kujawinski',
    author_email='kamil@kujawinski.net',
    tests_require=[
        'unittest2',
    ],
    test_suite="tests",
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
