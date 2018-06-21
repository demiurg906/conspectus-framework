import json
import shutil
import subprocess
import os

try:
    from .html_generator.html_generator import HtmlGenerator
    from .html_generator.constants import *
except ModuleNotFoundError:
    from html_generator.html_generator import HtmlGenerator
    from html_generator.constants import *


def clean():
    for folder in [SITE_DIR, TEMPLATE_DIR]:
        if os.path.exists(folder):
            shutil.rmtree(folder)


def generate_table_of_content():
    def find(path):
        def check_file(file, exts):
            if file.lower() == README_FILE:
                return False
            file_name = os.path.split(file)[-1]
            _, ext = os.path.splitext(file)
            return os.path.isfile(file) and ext in exts and not file_name.startswith('.')

        def check_source(file):
            return check_file(file, {'.md'})

        def check_image(file):
            return check_file(file, {'.png', '.bmp', '.jpg', '.svg', '.gif'})

        def check_folder(dir):
            dir_name = os.path.split(dir)[-1]
            return os.path.isdir(dir) and dir != FRAMEWORK_DIR and not dir_name.startswith('.')

        dir_content = list(map(lambda file: os.path.join(path, file), os.listdir(path)))

        sources = list(filter(check_source, dir_content))
        images = list(filter(check_image, dir_content))

        data = Content([], sources, images)

        dirs_copy = list(filter(check_folder, dir_content))

        for dir in dirs_copy:
            d = find(dir)
            if not (d.sources or d.images):
                continue
            data.sources.extend(d.sources)
            data.images.extend(d.images)
            data.folders.extend(d.folders)
        data.folders.append((path, bool(data.sources)))
        for l in data:
            l.sort()
        return Content(
            folders=list(map(lambda p: (normalize_path(p[0]), p[1]), data.folders)),
            sources=list(map(normalize_path, data.sources)),
            images=list(map(normalize_path, data.images))
        )

    return find('./')


def generate_folders(content: Content, base_dir):
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    os.chdir(base_dir)
    for dir, _ in content.folders:
        if not os.path.exists(dir):
            os.makedirs(dir)
    os.chdir('..')


def copy_images(content: Content):
    for img in content.images:
        shutil.copy(img, os.path.join(SITE_DIR, img))


def run_ast_script(content: Content):
    for source in content.sources:
        base_dir = os.path.abspath(os.curdir)
        source_dir = os.path.join(*os.path.split(source)[:-1])
        path = os.path.join(base_dir, TEMPLATE_DIR, source_dir)
        source_filename = os.path.split(source)[-1]
        subprocess.run(['node', './conspectus-framework/ast/index.js', source, path, source_filename])


def generate_html(content: Content, config: Config):
    HtmlGenerator(content, config).generate_htmls()


if __name__ == '__main__':
    with open('.config.json') as f:
        config = json.load(f)

    username = config.get('username')
    repo = config.get('repo')
    github_host = '{}.github.io/{}'.format(username, repo)
    pages_host = '{}/{}'.format(username, repo)
    telegram_chat_id = config.get('chat_id', 0)
    meta_title = config.get('meta_title', '')
    meta_description = config.get('meta_description', '')

    config = Config(username, repo, meta_title, meta_description, github_host, pages_host)


    def run_script(script):
        subprocess.run([f'./conspectus-framework/script/{script}', pages_host, github_host, str(telegram_chat_id)])


    if DEBUG:
        content = generate_table_of_content()
        generate_html(content, config)
    else:
        clean()
        content = generate_table_of_content()
        run_script('clone_repo.sh')
        generate_folders(content, TEMPLATE_DIR)
        generate_folders(content, SITE_DIR)
        copy_images(content)
        run_ast_script(content)
        generate_html(content, config)
        run_script('push_and_notify.sh')
