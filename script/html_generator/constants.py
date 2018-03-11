from collections import namedtuple

DEBUG = False

FRAMEWORK_DIR = './conspectus-framework'
README_FILE = './readme.md'
SITE_DIR = './_site'
TEMPLATE_DIR = './_template'

MAIN_TEMPLATE_FILE = './conspectus-framework/templates/main_template.html'
TOC_TEMPLATE_FILE = './conspectus-framework/templates/toc_template.html'

Config = namedtuple('Config', ['username', 'repo', 'meta_title', 'meta_description', 'github_host', 'pages_host'])
Content = namedtuple('Content', ['folders', 'sources', 'images'])


def normalize_path(path: str):
    res = path.replace('/./', '/')
    if res.endswith('/.'):
        res = res[:-2]
    if res == './':
        res = '.'
    return res
