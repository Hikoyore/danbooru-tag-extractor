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
        match = re.search(r'/posts/(\d+)', path)
        if match:
            return domain, match.group(1)
        match = re.search(r'/data/[^?]+\?(\d+)', url)
        if match:
            return domain, match.group(1)
        match = re.search(r'/([a-f0-9]{32})\.[a-z]+', url, re.IGNORECASE)
        if match:
            md5 = match.group(1)
            return domain, f"md5:{md5}"

    elif 'konachan.com' in domain or 'konachan.net' in domain:
        match = re.search(r'/post/show/(\d+)', path)
        if match:
            return domain, match.group(1)
        match = re.search(r'/posts/(\d+)', path)
        if match:
            return domain, match.group(1)
        match = re.search(r'/([a-f0-9]{32})\.[a-z]+', url, re.IGNORECASE)
        if match:
            md5 = match.group(1)
            return domain, f"md5:{md5}"
        match = re.search(r'[?&]post_id=(\d+)', query)
        if match:
            return domain, match.group(1)

    return None, None

def get_clean_tags_from_url(url):
    print("🔄 Получаю теги...")

    domain, identifier = extract_identifier(url)
    if not domain or not identifier:
        print("❌ Не удалось определить идентификатор поста из ссылки")
        return None

    if 'danbooru.donmai.us' in domain or 'aibooru.online' in domain:
        api_base = f"https://{domain}"
        endpoint = "/posts.json"
        tag_field = "tag_string"
    elif 'konachan.com' in domain or 'konachan.net' in domain:
        api_base = f"https://{domain}"
        endpoint = "/post.json"
        tag_field = "tags"
    else:
        print(f"❌ Домен {domain} не поддерживается")
        return None

    if identifier.startswith("md5:"):
        params = {"tags": identifier}
    else:
        params = {"tags": f"id:{identifier}"}

    api_url = api_base + endpoint

    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, list) or len(data) == 0:
            print("❌ Пост не найден")
            return None

        post = data[0]
        post_id = post.get('id', identifier)
        raw_tags = post.get(tag_field, "").split()
        if not raw_tags:
            print("⚠️ У поста нет тегов")
            return None

        clean_tags = [clean_tag(tag) for tag in raw_tags]
        clean_tags.sort()

        domain_slug = domain.replace('.', '_')
        filename = f"tags_{domain_slug}_{post_id}_clean.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(", ".join(clean_tags))
            f.write(f"\n\nВсего тегов: {len(clean_tags)}")

        print(f"✅ Сохранено {len(clean_tags)} тегов в {filename}")
        return clean_tags

    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при запросе: {e}")
        return None
    except (KeyError, ValueError) as e:
        print(f"❌ Ошибка при обработке данных: {e}")
        return None

def main():
    print("=" * 50)
    print("Tag Extractor для Danbooru, Aibooru, Konachan")
    print("=" * 50)
    print("Вставьте ссылку на страницу поста или изображение")
    print("Поддерживаемые сайты: danbooru.donmai.us, aibooru.online, konachan.com, konachan.net")
    print("Примеры:")
    print("  https://danbooru.donmai.us/posts/123456")
    print("  https://konachan.com/post/show/123456")
    print()
    print("Для выхода введите exit, quit или пустую строку")
    print()

    while True:
        url = input("🔗 Ссылка: ").strip()
        if url.lower() in ['exit', 'quit', 'q', '']:
            print("Программа завершена.")
            break
        if url:
            get_clean_tags_from_url(url)
            print()

if __name__ == "__main__":
    main()
