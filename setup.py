import os

from setuptools import setup
from setuptools import Command

README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))


class TestCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.distribution.fetch_build_eggs(self.distribution.tests_require)
        from django.utils._os import upath
        from django.conf import settings
        settings.configure(
            DATABASES={
                'default': {
                    'NAME': ':memory:',
                    'ENGINE': 'django.db.backends.sqlite3'
                }
            },
            INSTALLED_APPS=(
                'django.contrib.admin',
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'django.contrib.sessions',
                'jsonfield',
                'offermaker',
                'offermaker.tests2',
            ),
            TEMPLATE_CONTEXT_PROCESSORS = (
                'django.contrib.auth.context_processors.auth',
            ),
            MIDDLEWARE_CLASSES = (
                'django.contrib.sessions.middleware.SessionMiddleware',
                'django.middleware.common.CommonMiddleware',
                'django.contrib.auth.middleware.AuthenticationMiddleware',
                'django.contrib.messages.middleware.MessageMiddleware',
            ),
            TEMPLATE_DIRS=(
                os.path.join(os.path.dirname(upath(__file__)), 'offermaker', 'tests2', 'templates'),
            ),
            TEMPLATE_LOADERS = (
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
                'django.template.loaders.eggs.Loader',
            ),
            STATIC_URL='/static/',
            ROOT_URLCONF='',
        )

        from django.core.management import call_command
        import django

        if django.VERSION[:2] >= (1, 7):
            django.setup()

        call_command('test', 'offermaker')


setup(
    name='django-offermaker',
    version='0.9.8',
    packages=['offermaker'],
    include_package_data=True,
    license='LGPL',
    description='Django application that allows creation, preview and usage of custom multivariant restrictions applied on the forms.',
    long_description=README,
    url='http://offermaker.kjw.pt',
    author='Kamil Kujawinski',
    author_email='kamil@kujawinski.net',
    install_requires=[
        'jsonfield>=1.0.0',
    ],
    tests_require=[
        'django>=1.5',
        'jsonfield>=1.0.0',
        'selenium',
    ],
    test_suite="tests",
    cmdclass={'test': TestCommand},
    zip_safe=False,
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
