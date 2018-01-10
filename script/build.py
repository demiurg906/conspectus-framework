import json
import subprocess

if __name__ == '__main__':
    with open('.config.json') as f:
        config = json.load(f)

    username = config.get('username')
    repo = config.get('repo')
    github_host = '{}.github.io/{}'.format(username, repo)
    pages_host = '{}/{}'.format(username, repo)
    telegram_chat_id = config.get('chat_id', 0)
    # print(' '.join(['./conspectus-framework/script/build.sh', pages_host, github_host, str(telegram_chat_id)]))
    subprocess.run(['./conspectus-framework/script/build.sh', pages_host, github_host, str(telegram_chat_id)])
