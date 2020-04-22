## mkgendocs
A Python package for automatically generating documentation pages in markdown for 
Python source files by parsing **Google style docstring**. The markdown output makes it
ideal to combine with [mkdocs](https://www.mkdocs.org/). 

Instead of executing the python code (using the `inspect` package to access signatures and docstrings), we extract information directly from the source files by parsing them into Abstract Syntax Trees (AST) using the `ast` package. 

The `astor` (AST observe/rewrite) package is also used to convert function or class signatures from AST nodes back into source code strings.
 
![mkgendocs](mkgendocs.png)

## Installation
Install mkgendocs from [PyPI](https://pypi.org/project/mkgendocs/)

```python
pip install mkgendocs
```

## Usage

```
gendocs --config mkgendocs.yml
```

A sources directory is created with the documentation that was automatically generated.
Any examples in a "examples" directory are automatically copied over to the documentation, 
the module level docstrings are copied 


### Configuration Example

````yaml
sources_dir: docs/sources
templates_dir: docs/templates

pages:
  - page: "train/model.md"
    source: "tensorx/train/model.py"
    methods:
      - Model:
          - train
          - set_optimizer
  - page: "layers/core.md"
    source: 'tensorx/layers.py'
    classes:
      - Linear
      - Module
  - page: "math.md"
    source: 'tensorx/math.py'
    functions:
      - sparse_multiply_dense
````

* **sources_dir**: directory where the resulting markdown files are created
* **templates_dir**: directory where template files can be stored. All the folders and files are 
copied to the sources directory. Any markdown files are used as templates with the 
tag `{{autogenerated}}` in the template files being replaced by the generated documentation.
* **pages**: list of pages to be automatically generated from the respective source files and templates:
    * **page**: path for page template / sources dir for the resulting page;
    * **source**: path to source file from which the page is to be genrated;
    * **methods**: list of class to method name dictionaries;
    * **classes**: list of classes to be fully documented;
    * **functions**: list of functions to be documented.

## Buy me a coffee
If you find any of this useful, consider getting me some coffee, coffee is great!
<br/><br/>
<a href='https://ko-fi.com/Y8Y0RZO6' target='_blank'><img height='36' style='border:0px;height:36px;' src='https://az743702.vo.msecnd.net/cdn/kofi3.png?v=0' border='0' alt='Buy Me a Coffee at ko-fi.com' /></a>
