import requests
import re

def clean_tag(tag):
    """Заменяет подчеркивания на пробелы"""
    return tag.replace('_', ' ')

def extract_post_id_from_url(url):
    """Извлекает ID поста из различных форматов URL Danbooru"""
    
    # Паттерны для разных форматов URL
    patterns = [
        r'danbooru\.donmai\.us/posts/(\d+)',  # /posts/123456
        r'danbooru\.donmai\.us/data/[^?]+\?(\d+)',  # /data/xxx.jpg?123456
        r'danbooru\.donmai\.us/original/[^/]+/[^/]+/[^/]+\.([a-f0-9]{32})',  # MD5 хеш
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            if pattern == patterns[2]:  # MD5 паттерн
                return f"md5:{match.group(1)}"
            return match.group(1)
    
    return None

def get_clean_tags_from_url(url):
    """
    Получает теги по URL изображения Danbooru
    """
    print("🔄 Получаю теги...")
    
    # Извлекаем ID или MD5 из URL
    post_id_or_md5 = extract_post_id_from_url(url)
    
    if not post_id_or_md5:
        print("❌ Не удалось определить ID поста из ссылки")
        return None
    
    # Формируем запрос к API
    if post_id_or_md5.startswith('md5:'):
        # Поиск по MD5
        md5 = post_id_or_md5[4:]
        api_url = f"https://danbooru.donmai.us/posts.json?tags=md5:{md5}"
    else:
        # Прямой запрос по ID
        api_url = f"https://danbooru.donmai.us/posts/{post_id_or_md5}.json"
    
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        
        data = response.json()
        
        # Если искали по MD5, берем первый результат
        if isinstance(data, list):
            if not data:
                print("❌ Пост не найден")
                return None
            data = data[0]
            post_id = data['id']
        else:
            post_id = post_id_or_md5
        
        # Получаем сырые теги
        raw_tags = data['tag_string'].split()
        
        # Очищаем теги (заменяем _ на пробелы)
        clean_tags = [clean_tag(tag) for tag in raw_tags]
        
        # Сортируем
        clean_tags.sort()
        
        # Сохраняем в файл
        filename = f"tags_{post_id}_clean.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            # Все теги в одну строку через запятую
            f.write(", ".join(clean_tags))
            f.write(f"\n\nВсего тегов: {len(clean_tags)}")
        
        # МИНИМАЛЬНЫЙ ВЫВОД
        print(f"✅ Сохранено {len(clean_tags)} тегов в {filename}")
        
        return clean_tags
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при запросе: {e}")
        return None
    except KeyError as e:
        print(f"❌ Ошибка при обработке данных: {e}")
        return None

def main():
    print("="*50)
    print("Danbooru Tag Extractor")
    print("="*50)
    print("Вставьте ссылку на изображение Danbooru")
    print("(Пример: https://danbooru.donmai.us/posts/123456)")
    print()
    
    while True:
        url = input("🔗 Ссылка: ").strip()
        
        if url.lower() in ['exit', 'quit', 'q', '']:
            print("Программа завершена.")
            break
        
        if url:
            get_clean_tags_from_url(url)
            print()  # Пустая строка для разделения

if __name__ == "__main__":
    main()
