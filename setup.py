"""Setup the package."""
from setuptools import setup, find_packages
from webhooks.const import VERSION

setup(
    name="webhooks",
    version=VERSION,
    url="https://github.com/ludeeus/webhooks",
    author="Ludeeus",
    author_email="hi@ludeeus.dev",
    description="Handle webhook connections for various automations",
    packages=find_packages(),
    install_requires=["aiogithubapi", "integrationhelper", "aiohttp"],
)
