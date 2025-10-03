from setuptools import setup, find_packages

setup(
    name='ioc',
    version='0.1.0',
    description='A Dependency Injection Framework For Python Projects',
    author='Khaled Adrani',
    author_email='khaledadrani@gmail.com',
    url='https://github.com/khaledadrani/ioc',
    packages=find_packages(),
    python_requires='>=3.8',
    install_requires=[
        'pyyaml>=6.0',
    ],
    extras_require={
        'dev': ['pytest>=7.0', 'pytest-cov', 'pydantic>=1.0'],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
