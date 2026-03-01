import requests
import re
from urllib.parse import urlparse

def clean_tag(tag):
    return tag.replace('_', ' ')

def extract_identifier(url):
    parsed = urlparse(url)
    domain = parsed.netloc
    path = parsed.path
    query = parsed.query

    if 'danbooru.donmai.us' in domain or 'aibooru.online' in domain:
        m = re.search(r'/posts/(\d+)', path)
        if m:
            return domain, m.group(1)
        m = re.search(r'/data/[^?]+\?(\d+)', url)
        if m:
            return domain, m.group(1)
        m = re.search(r'/([a-f0-9]{32})\.[a-z]+', url, re.I)
        if m:
            return domain, f"md5:{m.group(1)}"

    elif 'konachan.com' in domain or 'konachan.net' in domain:
        m = re.search(r'/post/show/(\d+)', path)
        if m:
            return domain, m.group(1)
        m = re.search(r'/posts/(\d+)', path)
        if m:
            return domain, m.group(1)
        m = re.search(r'/([a-f0-9]{32})\.[a-z]+', url, re.I)
        if m:
            return domain, f"md5:{m.group(1)}"
        m = re.search(r'[?&]post_id=(\d+)', query)
        if m:
            return domain, m.group(1)

    elif 'yande.re' in domain:
        m = re.search(r'/post/show/(\d+)', path)
        if m:
            return domain, m.group(1)
        m = re.search(r'/posts/(\d+)', path)
        if m:
            return domain, m.group(1)

    elif 'gelbooru.com' in domain:
        m = re.search(r'id=(\d+)', query)
        if m:
            return domain, m.group(1)
        m = re.search(r'/posts/(\d+)', path)
        if m:
            return domain, m.group(1)

    return None, None

def get_danbooru_tags(identifier):
    if str(identifier).startswith('md5:'):
        params = {'tags': identifier}
    else:
        params = {'tags': f'id:{identifier}'}
    url = 'https://danbooru.donmai.us/posts.json'

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list) or len(data) == 0:
            return None
        post = data[0]
        raw_tags = post.get('tag_string', '').split()
        if not raw_tags:
            return None
        return [clean_tag(t) for t in raw_tags]
    except:
        return None

def get_konachan_tags(domain, identifier):
    base_url = f"https://{domain}"
    if str(identifier).startswith('md5:'):
        params = {'tags': identifier}
    else:
        params = {'tags': f'id:{identifier}'}
    url = f"{base_url}/post.json"

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list) or len(data) == 0:
            return None
        post = data[0]
        raw_tags = post.get('tags', '').split()
        if not raw_tags:
            return None
        return [clean_tag(t) for t in raw_tags]
    except:
        return None

def get_image_info_from_source(domain, post_id):
    info = {'file_url': None, 'md5': None}

    if 'yande.re' in domain:
        api_url = f"https://yande.re/post.json?tags=id:{post_id}"
        try:
            resp = requests.get(api_url, timeout=10)
            data = resp.json()
            if data and len(data) > 0:
                info['file_url'] = data[0].get('file_url')
                info['md5'] = data[0].get('md5')
        except:
            pass

    elif 'gelbooru.com' in domain:
        api_url = "https://gelbooru.com/index.php"
        params = {
            'page': 'dapi',
            's': 'post',
            'q': 'index',
            'json': '1',
            'id': post_id
        }
        try:
            resp = requests.get(api_url, params=params, timeout=10)
            data = resp.json()
            if data and isinstance(data, list) and len(data) > 0:
                info['file_url'] = data[0].get('file_url')
                info['md5'] = data[0].get('md5')
            elif data and 'post' in data and isinstance(data['post'], list) and len(data['post']) > 0:
                info['file_url'] = data['post'][0].get('file_url')
                info['md5'] = data['post'][0].get('md5')
        except Exception as e:
            try:
                html_url = f"https://gelbooru.com/index.php?page=post&s=view&id={post_id}"
                html_resp = requests.get(html_url, timeout=10)
                match = re.search(r'<meta property="og:image" content="([^"]+)"', html_resp.text)
                if match:
                    info['file_url'] = match.group(1)
                if info['file_url']:
                    md5_match = re.search(r'/([a-f0-9]{32})\.[a-z]+', info['file_url'], re.I)
                    if md5_match:
                        info['md5'] = md5_match.group(1)
            except:
                pass

    return info

def search_on_danbooru_by_md5(md5):
    url = f"https://danbooru.donmai.us/posts.json?tags=md5:{md5}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data and len(data) > 0:
            return data[0].get('id')
    except:
        pass
    return None

def search_on_danbooru_by_iqdb(image_url):
    try:
        img_resp = requests.get(image_url, stream=True, timeout=15)
        if img_resp.status_code != 200:
            return None
        files = {'file': ('image.jpg', img_resp.content, 'image/jpeg')}
        iqdb_resp = requests.post('https://iqdb.org/', files=files, timeout=20)
        if iqdb_resp.status_code != 200:
            return None
        pattern = r'danbooru\.donmai\.us/posts/(\d+)'
        matches = re.findall(pattern, iqdb_resp.text)
        if matches:
            return matches[0]
    except:
        pass
    return None

def save_tags_to_file(tags, source_url, danbooru_url=None, domain_slug=None, post_id=None):
    if not domain_slug or not post_id:
        domain, ident = extract_identifier(source_url)
        if domain and ident:
            domain_slug = domain.replace('.', '_')
            post_id = ident.replace(':', '_')
        else:
            domain_slug = 'unknown'
            post_id = 'unknown'

    filename = f"tags_{domain_slug}_{post_id}_clean.txt"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(", ".join(tags))
            f.write(f"\n\nВсего тегов: {len(tags)}")
            f.write(f"\n\nSource: {source_url}")
            if danbooru_url and danbooru_url != source_url:
                f.write(f"\nDanbooru: {danbooru_url}")
        print(f"✅ Сохранено {len(tags)} тегов в {filename}")
        return filename
    except Exception as e:
        print(f"❌ Ошибка при сохранении файла: {e}")
        return None

def process_url(url):
    print("🔄 Анализирую ссылку...")
    domain, identifier = extract_identifier(url)
    if not domain or not identifier:
        print("❌ Не удалось распознать ссылку")
        return None

    file_id = identifier.replace(':', '_')

    if 'danbooru.donmai.us' in domain or 'aibooru.online' in domain:
        print(f"📌 Прямой запрос к {domain}")
        tags = get_danbooru_tags(identifier)
        if not tags:
            print("❌ Не удалось получить теги")
            return None
        save_tags_to_file(tags, url, domain_slug=domain.replace('.','_'), post_id=file_id)
        return tags

    elif 'konachan.com' in domain or 'konachan.net' in domain:
        print(f"📌 Прямой запрос к {domain}")
        tags = get_konachan_tags(domain, identifier)
        if not tags:
            print("❌ Не удалось получить теги")
            return None
        save_tags_to_file(tags, url, domain_slug=domain.replace('.','_'), post_id=file_id)
        return tags

    elif 'yande.re' in domain or 'gelbooru.com' in domain:
        print(f"📌 Источник: {domain}, ID: {identifier}")
        info = get_image_info_from_source(domain, identifier)
        if not info['file_url']:
            print("❌ Не удалось получить информацию об изображении")
            return None
        print(f"🖼️ Изображение: {info['file_url']}")

        danbooru_id = None
        if info['md5']:
            print("🔎 Ищу по MD5...")
            danbooru_id = search_on_danbooru_by_md5(info['md5'])
            if danbooru_id:
                print("✅ Найдено по MD5")
        if not danbooru_id:
            print("🔎 Ищу через IQDB...")
            danbooru_id = search_on_danbooru_by_iqdb(info['file_url'])
            if danbooru_id:
                print("✅ Найдено через IQDB")
        if not danbooru_id:
            print("❌ Не удалось найти изображение на Danbooru")
            return None

        print(f"📌 Пост на Danbooru: ID {danbooru_id}")
        tags = get_danbooru_tags(danbooru_id)
        if not tags:
            print("❌ Не удалось получить теги с Danbooru")
            return None

        danbooru_url = f"https://danbooru.donmai.us/posts/{danbooru_id}"
        save_tags_to_file(tags, url, danbooru_url=danbooru_url,
                          domain_slug=domain.replace('.','_'), post_id=file_id)
        return tags

    else:
        print(f"❌ Домен {domain} не поддерживается")
        return None

def main():
    print("=" * 60)
    print("Универсальный Tag Extractor")
    print("=" * 60)
    print("Поддерживаются ссылки:")
    print("  - danbooru.donmai.us / aibooru.online")
    print("  - konachan.com / konachan.net")
    print("  - yande.re / gelbooru.com (поиск на Danbooru)")
    print()
    print("Примеры:")
    print("  https://danbooru.donmai.us/posts/123456")
    print("  https://konachan.com/post/show/123456")
    print("  https://yande.re/post/show/123456")
    print("  https://gelbooru.com/index.php?page=post&s=view&id=123456")
    print()
    print("Для выхода введите exit / quit / пустую строку")
    print()

    while True:
        url = input("🔗 Ссылка: ").strip()
        if url.lower() in ('exit', 'quit', 'q', ''):
            print("Программа завершена.")
            break
        if url:
            process_url(url)
            print()

if __name__ == "__main__":
    main()
