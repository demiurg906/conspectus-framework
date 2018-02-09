import json
import shutil
import subprocess
import os

FRAMEWORK_DIR = './conspectus-framework'
README_FILE = './readme.md'
SITE_DIR = './_site'
TEMPLATE_DIR = './_template'


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
        return check_file(file, {'.png', '.bmp', '.jpg', '.svg'})

    def check_folder(dir):
        dir_name = os.path.split(dir)[-1]
        return os.path.isdir(dir) and dir != FRAMEWORK_DIR and not dir_name.startswith('.')

    dir_content = list(map(lambda file: os.path.join(path, file), os.listdir(path)))

    sources = list(filter(check_source, dir_content))
    images = list(filter(check_image, dir_content))

    data = {
        'sources': sources,
        'images': images,
        'dirs': []
    }

    dirs_copy = list(filter(check_folder, dir_content))

    for dir in dirs_copy:
        d = find(dir)
        if not (d['sources'] or d['images']):
            continue
        data['sources'].extend(d['sources'])
        data['images'].extend(d['images'])
        data['dirs'].extend(d['dirs'])
    data['dirs'].append((path, bool(data['sources'])))
    for l in data.values():
        l.sort()
    return data


def generate_table_of_content():
    content = find('./')
    with open('__content__.json', 'w') as f:
        json.dump(content, f)
    return content


def generate_folders(content):
    os.chdir(SITE_DIR)
    for dir in content['dirs']:
        os.makedirs(dir)
    os.chdir('..')


def copy_images(content):
    for img in content['images']:
        shutil.copy(img, os.path.join(SITE_DIR, img))


if __name__ == '__main__':
    with open('.config.json') as f:
        config = json.load(f)

    username = config.get('username')
    repo = config.get('repo')
    github_host = '{}.github.io/{}'.format(username, repo)
    pages_host = '{}/{}'.format(username, repo)
    telegram_chat_id = config.get('chat_id', 0)

    def run_script(script):
        subprocess.run([f'./conspectus-framework/script/{script}', pages_host, github_host, str(telegram_chat_id)])

    content = generate_table_of_content()
    run_script('clone_repo.sh')
    generate_folders(content)
    copy_images(content)
    run_script('build.sh')
