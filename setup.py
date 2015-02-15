from setuptools import setup

setup(
    name="consulalerting",
    version="0.0.2",
    description="A set of python files for Consul for checks, watches, and notifications",
    url="https://github.com/jrxFive/Consul-Alerting",
    author="Jonathan R. Cross",
    author_email="jrxfive@gmail.com",
    license=open('LICENSE').read(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.6',
    ],
    keywords="consul notifications",
    install_requires=['consulate',
    'python-simple-hipchat']
)