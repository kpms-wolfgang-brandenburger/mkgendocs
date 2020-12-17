import os
import shutil
import yaml
import pathlib
from mkgendocs.parse import GoogleDocString, Extract
import argparse
from mako.template import Template
import logging

logging.basicConfig(level=logging.INFO,
                    format=">%(message)s")

DOCSTRING_TEMPLATE = """
## if we are processing a method function
%if header['function']:
    %if header['class']:
${h3} .${header['function']}
    %else:
${h3} ${header['function']}
    %endif
```python
.${signature}
```
%elif header['class']:
${h2} ${header['class']}

```python 
${signature}
```

%endif 

%for section in sections:
    %if section['header']:

**${section['header']}**

    %else:
---
    %endif
    %if section['args']:
        %for arg in section['args']:
        %if arg['field']:
* **${arg['field']}** ${arg['signature']} : ${arg['description']}
        %else:
* ${arg['description']}
        %endif
        %endfor
    %endif
${section['text']}
%endfor
"""


def copy_examples(examples_dir, destination_dir):
    """Copy the examples directory in the documentation.

    Prettify files by extracting the docstrings written in Markdown.
    """
    pathlib.Path(destination_dir).mkdir(exist_ok=True)
    for file in os.listdir(examples_dir):
        if not file.endswith('.py'):
            continue
        module_path = os.path.join(examples_dir, file)
        extract = Extract(module_path)
        docstring, lineno = extract.get_docstring(get_lineno=True)

        destination_file = os.path.join(destination_dir, file[:-2] + 'md')
        with open(destination_file, 'w+', encoding='utf-8') as f_out, \
                open(os.path.join(examples_dir, file),
                     'r+', encoding='utf-8') as f_in:

            f_out.write(docstring + '\n\n')

            # skip docstring
            for _ in range(lineno):
                next(f_in)

            f_out.write('```python\n')
            # next line might be empty.
            line = next(f_in)
            if line != '\n':
                f_out.write(line)

            # copy the rest of the file.
            for line in f_in:
                f_out.write(line)
            f_out.write('```')


def to_markdown(target_info, template):
    """ converts object data and docstring to markdown

    Args:
        target_info: object name, signature, and docstring
        template: markdown template for docstring to be rendered in markdown

    Returns:
        markdown (str): a string with the object documentation rendered in markdown

    """
    docstring = target_info['docstring']
    docstring_parser = GoogleDocString(docstring)
    try:
        docstring_parser.parse()
    except SyntaxError as e:
        e2 = f"Error while processing docstrings for {target_info['class']}.{target_info['function']}"
        raise Exception(e2 + ":\n\t" + str(e)).with_traceback(e.__traceback__)

    headers, data = docstring_parser.markdown()

    # if docstring contains a signature, override the source
    if data and "signature" in data[0]:
        signature = data[0]["signature"]
    else:
        signature = target_info['signature']

    # in mako ## is a comment
    markdown_str = template.render(header=target_info,
                                   signature=signature,
                                   sections=data,
                                   headers=headers,
                                   h2='##', h3='###')

    return markdown_str


def build_index(pages):
    root = pathlib.Path().absolute()

    # source->class->page
    # source->fn->page

    cls_index = dict()
    fn_index = dict()
    for page_data in pages:
        is_index = page_data.get("index", False)
        if not is_index:
            source = page_data['source']
            page = page_data["page"]
            if "classes" in page_data:
                classes = [list(cls)[0] if isinstance(cls,dict) else cls for cls in page_data["classes"]]
                classes = set(classes)
            clss = classes
            fns = set(list(page_data.get('functions', [])))

            if source not in cls_index:
                cls_index[source] = dict()
            if source not in fn_index:
                fn_index[source] = dict()

            for cls in clss:
                cls_index[source][cls] = page

            for fn in fns:
                fn_index[source][fn] = page

    return cls_index, fn_index


def generate(config_path):
    """Generates the markdown files for the documentation.

    # Arguments
        sources_dir: Where to put the markdown files.
    """

    root = pathlib.Path().absolute()
    logging.info("Loading configuration file")
    config = yaml.full_load(open(config_path))

    sources_dir = config.get('sources_dir', 'docs/sources')
    if not sources_dir:
        sources_dir = "docs/sources"
    template_dir = config.get('templates', None)

    logging.info('Cleaning up existing sources directory.')
    if sources_dir and os.path.exists(sources_dir):
        shutil.rmtree(sources_dir)

    logging.info('Populating sources directory with templates.')
    if template_dir:
        if not os.path.exists(template_dir):
            raise FileNotFoundError("No such directory: %s" % template_dir)
        shutil.copytree(template_dir, sources_dir)

    # if there are no templates, sources are not created from the files copied
    if not os.path.exists(sources_dir):
        os.makedirs(sources_dir)

    readme = ""
    if os.path.exists('README.md'):
        readme = open('README.md').read()

    if template_dir and os.path.exists(os.path.join(template_dir, 'index.md')):
        index = open(os.path.join(template_dir, 'index.md')).read()
        index = index.replace('{{autogenerated}}', readme[readme.find('##'):])
    else:
        index = readme

    # TODO this and README are still hardcoded filenames
    if os.path.exists('CONTRIBUTING.md'):
        shutil.copyfile('CONTRIBUTING.md', os.path.join(sources_dir, 'contributing.md'))

    if os.path.exists('examples'):
        copy_examples(os.path.join('examples'),
                      os.path.join(sources_dir, 'examples'))

    with open(os.path.join(sources_dir, 'index.md'), 'w', encoding='utf-8') as f:
        f.write(index)

    logging.info("Generating docs ...")
    docstring_template = DOCSTRING_TEMPLATE
    if "docstring_template" in config:
        try:
            docstring_template = open(config["docstring_template"]).read()
        except FileNotFoundError as e:
            raise e
    markdown_template = Template(text=docstring_template)

    pages = config.get("pages", dict())
    # check which classes and functions are being documented
    # TODO link index to individual pages based on headers when we have multiple classes in the same page (local links)
    cls_index, fn_index = build_index(pages)
    for page_data in pages:
        is_index = page_data.get("index", False)
        # build index page
        if is_index:
            source = os.path.join(root, page_data['source'])
            extract = Extract(source)
            all_cls = extract.get_classes()
            all_fn = extract.get_functions()
            if source in cls_index and len(cls_index[source]) > 0:
                all_cls = [cls_name for cls_name in all_cls if cls_name in cls_index[source]]
            if source in fn_index and len(fn_index[source]) > 0:
                all_fn = [fn_name for fn_name in all_fn if fn_name in fn_index[source]]

            markdown = ["## Classes"] + [f"class **{cls_name}**" for cls_name in all_cls] + ["\n\n"]
            markdown += ["## Functions"] + [f"**{cls_name}**" for cls_name in all_cls] + ["\n\n"]

            markdown = "\n".join(markdown)
        # build class or function page
        else:
            source = os.path.join(root, page_data['source'])
            extract = Extract(source)

            markdown_docstrings = []
            page_classes = page_data.get('classes', [])
            logging.debug(f"page classes {page_classes}")
            # page_methods = page_data.get('methods', [])
            page_functions = page_data.get('functions', [])

            def add_class_mkd(cls_name, methods):
                class_spec = extract.get_class(cls_name)
                mkd_str = to_markdown(class_spec, markdown_template)
                markdown_docstrings.append(mkd_str)

                if methods:
                    markdown_docstrings[-1] += "\n\n**Methods:**\n\n"
                    for method in methods:
                        logging.info(f"Generating docs for {cls_name}.{method}")
                        try:
                            method_spec = extract.get_method(class_name=cls_name,
                                                             method_name=method)
                            mkd_str = to_markdown(method_spec, markdown_template)
                            markdown_docstrings[-1] += mkd_str
                        except NameError:
                            pass

            for class_entry in page_classes:
                if isinstance(class_entry, dict):
                    class_name = list(class_entry.keys())[0]
                    all_methods = set(extract.get_methods(class_name))
                    method_names = class_entry.get(class_name)
                    excluded = set()
                    included = set()
                    for method_name in method_names:
                        if method_name.lstrip().startswith("!"):
                            method_name = method_name[method_name.find("!") + 1:]
                            if len(method_name) > 0 and method_name in all_methods:
                                excluded.add(method_name)
                            elif method_name not in all_methods:
                                raise ValueError(f"{method_name} not a method of {class_name}")
                        else:
                            included.add(method_name)
                    if excluded:
                        excluded_str = "\n".join(excluded)
                        logging.info(f"\tExcluded: {excluded_str}")

                    if len(excluded) > 0 and len(included) == 0:
                        included.update()
                    logging.info(class_name)
                    add_class_mkd(class_name, included)
                else:
                    # add all methods to documentation
                    class_methods = extract.get_methods(class_entry)
                    add_class_mkd(class_entry, class_methods)

            # for class_dict in page_methods:
            #     for class_name, class_methods in class_dict.items():
            #         add_class_mkd(class_name, class_methods)

            for fn in page_functions:
                logging.info(f"Generating docs for {fn}")
                fn_info = extract.get_function(fn)
                markdown_str = to_markdown(fn_info, markdown_template)
                markdown_docstrings.append(markdown_str)
            #    for method name in class_name:

            markdown = '\n----\n\n'.join(markdown_docstrings)

        # Either insert content into existing template or create new page
        page_name = page_data['page']
        path = os.path.join(sources_dir, page_name)
        if os.path.exists(path):
            page_template = open(path).read()

            if '{{autogenerated}}' not in page_template:
                raise RuntimeError('Template found for ' + path +
                                   ' but missing {{autogenerated}}'
                                   ' tag.')
            markdown = page_template.replace('{{autogenerated}}', markdown)
            logging.info(f"Inserting autogenerated content into template:{path}")
        else:
            logging.info(f"Creating new page with autogenerated content:{path}")

        subdir = os.path.dirname(path)
        if not os.path.exists(subdir):
            os.makedirs(subdir)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(markdown)


def main():
    parser = argparse.ArgumentParser(description='Generate docs')
    parser.add_argument('-c', '--config', dest='config', help='path to config file', default="mkgendocs.yml")
    args = parser.parse_args()
    generate(args.config)


if __name__ == '__main__':
    main()
