import json
import os
import sys

from collections import namedtuple
from jinja2 import Template

from .terms import generate_terms_info


def get_toc_from_file(filename):
    with open(filename) as f:
        return json.load(f)


def generate_toc_dict(toc_list):
    it = iter(toc_list)
    toc = []
    current_h1 = {'h2': []}
    current_h2 = {}
    try:
        while True:
            file, el = next(it)
            tag = int(el['tag'])
            title = el['title']
            anchor = '{}#{}'.format(file, el['anchor'])
            try:
                if tag == 1:
                    current_h1['h2'].append(current_h2)
                    current_h2 = {}
                    toc.append(current_h1)
                    current_h1 = {'title': title, 'anchor': anchor, 'h2': []}
                elif tag == 2:
                    current_h1['h2'].append(current_h2)
                    current_h2 = {'title': title, 'anchor': anchor, 'h3': []}
                elif tag == 3:
                    current_h2['h3'].append({'title': title, 'anchor': anchor})
            except KeyError:
                pass
    except StopIteration:
        current_h1['h2'].append(current_h2)
        toc.append(current_h1)
    toc = toc[1:]
    for h1 in toc:
        if not h1['h2'][0]:
            del h1['h2'][0]
    return toc


def generate_htmls(github_host, pages_host, input_folder='./conspectus-framework/terms/input', output_folder='./conspectus-framework/terms/output', template_name='main_template.html'):
    files = [file for file in sorted(os.listdir(input_folder)) if file.endswith('.html')]
    content_template = '{}\n<script>\nvar terms = {};\n</script>'
    envs = []
    toc_list = []
    html_filenames = []
    new_issue = 'https://github.com/{}/issues/new'.format(github_host)
    for file in files:
        if file == 'main_template.html':
            continue
        filename = '{}/{}'.format(input_folder, file)
        with open(filename) as f:
            content = ''.join(f.readlines())
        res_filename = file
        html_filenames.append(res_filename)
        res_file = '{}/{}'.format(output_folder, res_filename)

        headers_file = filename.replace('.html', '.headers.json')
        toc_list.extend([(res_filename, el) for el in get_toc_from_file(headers_file)])

        terms_file = filename.replace('.html', '.terms.json')
        terms_json = generate_terms_info(terms_file)

        md_file = '{}'.format(file.replace('.html', '.md'))
        meta_title = 'Конспект по алгоритмам'
        with open(md_file) as f:
            for line in f:
                if line.startswith('#'):
                    meta_title += '. ' + line.replace('#', '').strip()
                    break

        description_file = filename.replace('.html', '.desc.txt')
        with open(description_file) as f:
            description = f.readline()


        envs.append((res_file, {
            'content': content_template.format(content, terms_json),
            'meta_title': meta_title,
            'meta_description': description,
            'new_issue': new_issue
        }))

    # --------------------FILE TOC--------------------
    toc = generate_toc_dict(toc_list)
    with open('./conspectus-framework/terms/sources_toc_template.html') as f:
        ninja_template = ''.join(f.readlines())
        ninja_template = Template(ninja_template)

    with open(template_name) as f:
        template = ''.join(f.readlines())
        template = Template(template)

    prev_next_refs = []
    href_template = 'https://{}/'.format(pages_host) + '{}'
    for i in range(len(html_filenames)):
        left = None if i == 0 else href_template.format(html_filenames[i-1])
        right = None if i == len(html_filenames) - 1 else href_template.format(html_filenames[i+1])
        prev_next_refs.append((left, right))

    for (res_file, env), (left, right) in zip(envs, prev_next_refs):
        env['left_page'] = left
        env['right_page'] = right
        with open(res_file, 'w') as f:
            f.write(template.render(env))
            print('{} generated'.format(res_file))
    with open('{}/index.html'.format(output_folder), 'w') as f:
        toc_html = ninja_template.render({'toc': toc})
        f.write(template.render({
            'content': toc_html,
            'meta_title': 'Конспект по алгоритмам',
            'meta_description': 'Конспект всех лекций А. Смаля',
            'index_page': True,
            'new_issue': new_issue
        }))


def generate_indices():
    pass


def main():
    github_host, pages_host, input_folder, output_folder = sys.argv[1:]
    generate_htmls(github_host, pages_host, input_folder, output_folder, template_name='./conspectus-framework/ast/main_template.html')


if __name__ == '__main__':
    """
    usage: python html_generator.py input_folder output_folder
    if no args, './input' './output' uses as default
    """
    main()
    # toc = [
    #     {'title': 'hello1', 'anchor': 'hello1', 'tag': 1},
    #     {'title': 'hello2', 'anchor': 'hello2', 'tag': 2},
    #     {'title': 'hello3', 'anchor': 'hello3', 'tag': 3},
    #     {'title': 'hello4', 'anchor': 'hello4', 'tag': 2},
    #     {'title': 'hello5', 'anchor': 'hello5', 'tag': 3},
    #     {'title': 'hello6', 'anchor': 'hello6', 'tag': 1},
    # ]
    # toc = [('hello.html', el) for el in toc]
    # toc = generate_toc(toc)
    #
    # with open('terms/sources_toc_template.html') as f:
    #     ninja_template = ''.join(f.readlines())
    #     ninja_template = Template(ninja_template)
    # page = ninja_template.render({'toc': toc})
    # print(page)
