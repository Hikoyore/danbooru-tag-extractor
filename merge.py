import os
import glob

def merge_all_tags():
    """
    Объединяет все строки с тегами из всех файлов в один файл
    """
    print("="*50)
    print("Объединение всех тегов в один файл")
    print("="*50)
    
    # Находим все файлы с тегами
    tag_files = glob.glob("tags_*_clean.txt")
    
    if not tag_files:
        print("❌ Не найдено файлов с тегами (tags_*_clean.txt)")
        return
    
    print(f"Найдено файлов: {len(tag_files)}")
    print()
    
    # Создаем выходной файл
    output_filename = "all_tags_combined.txt"
    
    with open(output_filename, 'w', encoding='utf-8') as outfile:
        file_count = 0
        
        for filename in sorted(tag_files):  # сортируем для порядка
            try:
                with open(filename, 'r', encoding='utf-8') as infile:
                    # Читаем только первую строку (с тегами)
                    first_line = infile.readline().strip()
                    
                    # Проверяем, что строка не пустая
                    if first_line:
                        # Записываем теги в выходной файл
                        outfile.write(first_line + '\n\n')
                        file_count += 1
                        print(f"✅ {filename}")
                    else:
                        print(f"⚠️ {filename} - пустой файл")
                        
            except Exception as e:
                print(f"❌ Ошибка с файлом {filename}: {e}")
    
    print(f"\n{'='*50}")
    print(f"✅ Готово! Обработано файлов: {file_count}")
    print(f"📄 Результат сохранен в: {output_filename}")

if __name__ == "__main__":
    merge_all_tags()
    input("\nНажмите Enter для выхода...")