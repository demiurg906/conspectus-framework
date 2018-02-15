import json
import os.path

import itertools

from jinja2 import Template

try:
    from .constants import *
    from .terms import generate_terms_info
except ModuleNotFoundError:
    from constants import *
    from terms import generate_terms_info


def get_template_from_file(template):
    with open(template) as f:
        return Template(''.join(f.readlines()))


Paths = namedtuple('Paths', ['source', 'template', 'result'])
FolderContent = namedtuple('FolderContent', ['subfolders', 'sources'])


class HtmlGenerator:
    def __init__(self, content: Content, config: Config):
        self.content = content
        self.config = config
        self.content_template = '{}\n<script>\nvar terms = {};\n</script>'
        self.new_issue = 'https://github.com/{}/{}/issues/new'.format(config.username, config.repo)
        self.host = 'https://{}'.format(config.github_host)
        self.main_template = get_template_from_file(MAIN_TEMPLATE_FILE)
        self.toc_template = get_template_from_file(TOC_TEMPLATE_FILE)

    def generate_paths(self) -> Paths:
        return {
            source: Paths(
                source,
                normalize_path(os.path.join(TEMPLATE_DIR, source)),
                normalize_path(os.path.join(SITE_DIR, source))
            ) for source in self.content.sources
        }

    def group_files_by_folders(self):
        # все файлы, относящиеся к конкретной папке
        data = {
            folder: FolderContent([], [])
            for folder, source_folder in self.content.folders
            if source_folder
        }
        # ищем всех непосредственных детей каждой папки
        for parent, child in itertools.permutations(data.keys(), 2):
            if child.startswith(parent):
                tail = child[len(parent):]
                if tail.count('/') != 1:
                    continue
                data[parent].subfolders.append(child)

        # для каждой папки ищем файлы, которые в ней лежат
        for source in self.content.sources:
            path = os.path.join(*os.path.split(source)[:-1])
            data[path].sources.append(source)
        for folder_content in data.values():
            folder_content.subfolders.sort()
            folder_content.sources.sort()
        return data

    def generate_folder_content(self, folder: str, content: FolderContent):
        html_filenames, toc_list, envs = [], [], []
        folders_toc_list = [
            (os.path.split(subfolder)[-1], {
                'anchor': '',
                'tag': 1,
                'title': os.path.split(subfolder)[-1]
            })
            for subfolder in content.subfolders
        ]

        for source in content.sources:
            html_filename, toc_list_part, env = self.generate_source_html_data(source)
            html_filenames.append(html_filename)
            toc_list.extend(toc_list_part)
            envs.append(env)

        # ------------------ generation ------------------
        sources_toc = self.generate_toc_dict(toc_list)
        folders_toc = self.generate_toc_dict(folders_toc_list)
        prev_next_refs = self.generate_prev_next_refs(html_filenames)

        for (res_file, env), (left, right) in zip(envs, prev_next_refs):
            env['left_page'] = left
            env['right_page'] = right
            with open(res_file, 'w') as f:
                f.write(self.main_template.render(env))
                print('{} generated'.format(res_file))

        index_file = os.path.join(SITE_DIR, folder, 'index.html')
        with open(index_file, 'w') as f:
            toc_html = self.toc_template.render({
                'folders_toc': folders_toc,
                'sources_toc': sources_toc
            })
            # TODO: change meta
            f.write(self.main_template.render({
                'content': toc_html,
                'meta_title': 'Конспект по алгоритмам',
                'meta_description': 'Конспект всех лекций А. Смаля',
                'index_page': True,
                'new_issue': self.new_issue,
                'host': self.host,
                'main_page': folder == '.'
            }))
            print('{} generated'.format(index_file))

    def generate_source_html_data(self, source: str):
        def helper_names() -> [str]:
            base = normalize_path(os.path.join(TEMPLATE_DIR, os.path.splitext(source)[0]))
            extensions = ('.html', '.headers.json', '.desc.txt', '.terms.json')
            return [base + ext for ext in extensions]

        html_file, headers_file, description_file, terms_file = helper_names()
        result_html_file = html_file.replace(TEMPLATE_DIR, SITE_DIR)
        relative_file_ref = os.path.split(result_html_file)[-1]

        # основное тело html
        with open(html_file) as f:
            html_content = ''.join(f.readlines())

        # заголовки из html
        with open(headers_file) as f:
            toc_list = [(relative_file_ref, el) for el in json.load(f)]

        # собираем информацию о терминах
        if DEBUG:
            terms = {}
        else:
            terms = generate_terms_info(terms_file)

        # собираем мета-информацию
        # TODO
        meta_title = 'Заголовок'
        with open(description_file) as f:
            description = f.readline()

        env = (result_html_file, {
            'content': self.content_template.format(html_content, terms),
            'meta_title': meta_title,
            'meta_description': description,
            'new_issue': self.new_issue,
            'host': self.host
        })

        return relative_file_ref, toc_list, env

    @staticmethod
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

    def generate_prev_next_refs(self, html_filenames: [str]) -> [(str, str)]:
        res = []
        # href_template = 'https://{}/'.format(self.config.github_host) + '{}'
        for i in range(len(html_filenames)):
            # left = None if i == 0 else href_template.format(html_filenames[i - 1])
            # right = None if i == len(html_filenames) - 1 else href_template.format(html_filenames[i + 1])
            left = None if i == 0 else html_filenames[i - 1]
            right = None if i == len(html_filenames) - 1 else html_filenames[i + 1]
            res.append((left, right))
        return res

    def generate_htmls(self):
        folders = self.group_files_by_folders()
        for folder, folder_content in folders.items():
            self.generate_folder_content(folder, folder_content)
