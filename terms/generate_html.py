import json
import lxml.html
import os
import regex
import requests
import sys

from jinja2 import Template
from lxml.cssselect import CSSSelector
from textile import textile

WIKI_SEARCH_URL_TEMPLATE = 'https://ru.wikipedia.org/w/index.php?search={}&title=Служебная:Поиск&profile=default&fulltext=1'
NEERC_SEARCH_URL_TEMPLATE = 'https://neerc.ifmo.ru/wiki/index.php?title=%D0%A1%D0%BB%D1%83%D0%B6%D0%B5%D0%B1%D0%BD%D0%B0%D1%8F%3ASearch&profile=advanced&search={}&fulltext=Search&ns0=1&redirs=1&profile=advanced'


def convert_encoding(s):
    return s.encode('ISO-8859-1', 'ignore').decode('utf-8')


def get_tree_by_url(url: str):
    try:
        resp = requests.get(url)
    except requests.ConnectionError:
        # TODO: написать в лог
        return None
    if resp.status_code != 200:
        return None
    tree = lxml.html.fromstring(resp.content)
    return tree


def search_wiki(term: str):
    """
    находит ссылку на страницу в вики
    :param term: термин
    :return: title, url
    """
    url = WIKI_SEARCH_URL_TEMPLATE.format(term)
    tree = get_tree_by_url(url)
    if tree is None:
        return

    did_you_mean = CSSSelector('div.searchdidyoumean a')(tree)
    if did_you_mean:
        url = 'https://ru.wikipedia.org{}'.format(did_you_mean[0].attrib['href'])
        tree = get_tree_by_url(url)
        if tree is None:
            return None

    finded_sel = CSSSelector('.mw-search-results')
    finded = finded_sel(tree)
    if finded:
        # поиск что-то нашел, выбираем первую ссылку
        el = finded[0]
        # TODO: проверить, что нашли то, что нужно
        page = CSSSelector('div.mw-search-result-heading a')(el)[0]
        ref = 'https://ru.wikipedia.org' + page.attrib['href']
        title = page.attrib['title']
        return title, ref
    else:
        return None


def get_wiki_info(term: str):
    """
    находит информацию по термину в вики
    :return: словарь с инфо о странице:
             заголовок, адрес, текст и html для превью
    """
    info = search_wiki(term)
    if info is None:
        return None
    title, base_url = info

    url = 'https://ru.wikipedia.org/api/rest_v1/page/summary/{}'.format(title)
    try:
        resp = requests.get(url)
    except requests.ConnectionError:
        # TODO: написать в лог
        return None
    if resp.status_code != 200:
        return None
    data = json.loads(resp.text)

    def delete_key(data, key: str):
        try:
            del data[key]
        except KeyError:
            pass

    delete_key(data, 'displaytitle')
    delete_key(data, 'pageid')
    delete_key(data, 'dir')
    delete_key(data, 'lang')
    delete_key(data, 'timestamp')
    delete_key(data, 'originalimage')

    if 'thumbnail' in data:
        delete_key(data['thumbnail'], 'original')

    data['wiki_url'] = base_url
    return data


def search_neerc(term: str):
    """
    находит ссылку на страницу на neerc.ifmo
    :param term: термин
    :return: title, url
    """
    url = NEERC_SEARCH_URL_TEMPLATE.format(term)
    tree = get_tree_by_url(url)
    if tree is None:
        return None
    finded_sel = CSSSelector('.mw-search-results')
    finded = finded_sel(tree)
    if finded:
        # поиск что-то нашел, выбираем первую ссылку
        el = finded[0]
        # TODO: проверить, что нашли то, что нужно
        page = CSSSelector('div.mw-search-result-heading a')(el)[0]
        ref = 'https://neerc.ifmo.ru' + page.attrib['href']
        title = convert_encoding(page.attrib['title'])
        return title, ref
    else:
        return None


def get_neerc_info(term: str):
    """
    находит информацию по термину в вики
    :return: словарь с инфо о странице:
             заголовок, адрес, текст и html для превью
    """
    info = search_neerc(term)
    if info is None:
        return None
    title, base_url = info

    # TODO: проверить, что работает на страницах без определений
    def get_text():
        url = '{}&action=edit'.format(base_url)
        tree = get_tree_by_url(url)
        if tree is None:
            return None
        el = CSSSelector('#wpTextbox1')(tree)[0]
        text = convert_encoding(el.text)

        def process_text(text: str):
            res = []
            buf = ''
            step = 0
            for c in text:
                if step == 0:
                    if c != '|':
                        res.append(c)
                    else:
                        step = 1
                elif step == 1:
                    buf += c
                    if 'definition =' in buf:
                        step = 2
                else:
                    res.append(c)
            res = ''.join(res)
            res = regex.sub(r'<tex.*?>|</tex>', '$', res)
            res = regex.sub(r'\[.*?\||\]', '', res)
            res = regex.sub(r'|.?|definition\s*=', '', res)
            res = res.replace('{{---}}', '—')
            res = res.replace('*', '* ')
            res = regex.sub(r"'''\s*(.*?)\s*'''", ' *\g<1>* ', res)
            return res

        try:
            preview_text = process_text(regex.findall(r'{{((?>[^{}]+|(?R))*)}}', text)[0].strip())
            preview_text = '{}\n{}'.format(regex.findall(r'==.+?==', text)[0].strip(), preview_text)
        except IndexError:
            return None

        preview_html = textile(preview_text).replace('<strong', '<b').replace('</strong', '</b')
        return preview_text, preview_html

    def get_thumbnail():
        tree = get_tree_by_url(base_url)
        if tree is None:
            return None
        thumbnails = CSSSelector('img.thumbimage')(tree)
        if thumbnails is None or not thumbnails:
            return None
        thumbnail = thumbnails[0]
        args = thumbnail.attrib
        data = {
            'source': 'https://neerc.ifmo.ru' + args['src'],
            'width': args['width'],
            'height': args['height']
        }
        return data

    text = get_text()
    if text is None:
        return None
    text, html = text
    data = {
        'title': title,
        'wiki_url': base_url,
        'extract': text,
        'extract_html': html
    }

    thumbnail = get_thumbnail()
    if thumbnail is not None:
        data['thumbnail'] = thumbnail
    return data


def get_info(term: str):
    wiki_info = get_wiki_info(term)
    neerc_info = get_neerc_info(term)
    res = {}
    if wiki_info is not None:
        res['wiki'] = wiki_info
    if neerc_info is not None:
        res['neerc'] = neerc_info
    return res


def get_terms(filename):
    with open(filename) as f:
        return json.load(f)


def generate_terms_info(filename):
    """
    дописывает информацию он новых терминах из
    `get_terms` в индекс
    """
    data = {}
    for term in get_terms(filename):
        if term in data:
            continue
        info = get_info(term)
        if info:
            data[term] = info
            print('info about "{}" added'.format(term))
    return json.dumps(data)


def get_toc_from_file(filename):
    with open(filename) as f:
        return json.load(f)


def generate_toc(toc_list):
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


def generate_htmls(github_host, pages_host, input_folder='./conspectus-framework/terms/input', output_folder='./conspectus-framework/terms/output', template_name='template.html'):
    files = [file for file in sorted(os.listdir(input_folder)) if file.endswith('.html')]
    content_template = '{}\n<script>\nvar terms = {};\n</script>'
    envs = []
    toc_list = []
    html_filenames = []
    new_issue = 'https://github.com/{}/issues/new'.format(github_host)
    for file in files:
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

        md_file = 'source/{}'.format(file.replace('.html', '.md'))
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

    toc = generate_toc(toc_list)
    with open('./terms/n_template.html') as f:
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


def main():
    github_host, pages_host, input_folder, output_folder = sys.argv[1:]
    generate_htmls(github_host, pages_host, input_folder, output_folder, template_name='./conspectus-framework/ast/template.html')


if __name__ == '__main__':
    """
    usage: python generate_html.py input_folder output_folder
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
    # with open('terms/n_template.html') as f:
    #     ninja_template = ''.join(f.readlines())
    #     ninja_template = Template(ninja_template)
    # page = ninja_template.render({'toc': toc})
    # print(page)
