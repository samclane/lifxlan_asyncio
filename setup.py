from distutils.core import setup
import re


with open("lifxlan_asyncio/__init__.py") as meta_file:
    metadata = dict(re.findall("__([a-z]+)__\s*=\s*'([^']+)'", meta_file.read()))

setup(name='lifxlan_asyncio',
      version=metadata['version'],
      description=metadata['description'],
      url=metadata['url'],
      author=metadata['author'],
      author_email=metadata['authoremail'],
      license=metadata['license'],
      packages=['lifxlan'],
      install_requires=[
          "lifxlan",
          ],
      zip_safe=False,
      classifiers=[
          # Pick your license as you wish (should match "license" above)
          'License :: OSI Approved :: MIT License',

          # Specify the Python versions you support here. In particular, ensure
          # that you indicate whether you support Python 2, Python 3 or both.
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.7'
      ])