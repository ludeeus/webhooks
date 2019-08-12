"""Setup the package."""
from setuptools import setup, find_packages

setup(
    name="webhooks",
    version="0.1.0",
    url="https://github.com/ludeeus/webhooks",
    author="Ludeeus",
    author_email="hi@ludeeus.dev",
    description="Handle webhook connections for various automations",
    packages=find_packages(),
    install_requires=["aiogithubapi", "integrationhelper", "aiohttp", "PyJWT"],
)
