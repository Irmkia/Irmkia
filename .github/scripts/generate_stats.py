"""
Генератор SVG-картинки с топом языков.
Читает ВСЕ репозитории пользователя (включая приватные),
считает байты кода по языкам и рисует красивую SVG.
"""
import os
import json
import urllib.request
import urllib.error

# ============================================================
# НАСТРОЙКИ
# ============================================================
USERNAME = "Irmkia"
TOKEN = os.environ.get("GITHUB_TOKEN")  # Автоматически даёт Actions
OUTPUT_FILE = "assets/top-langs.svg"

# Цвета языков (можно расширять)
LANG_COLORS = {
    "Python": "#3572A5",
    "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "SCSS": "#c6538c",
    "Shell": "#89e051",
    "Dockerfile": "#384d54",
    "JSON": "#292929",
    "YAML": "#cb171e",
    "Markdown": "#083fa1",
    "SQL": "#e38c00",
    "Rust": "#dea584",
    "Go": "#00ADD8",
    "C": "#555555",
    "C++": "#f34b7d",
    "C#": "#178600",
    "Java": "#b07219",
    "PHP": "#4F5D95",
    "Ruby": "#701516",
    "Vue": "#41b883",
    "Svelte": "#ff3e00",
    "Kotlin": "#A97BFF",
    "Swift": "#F05138",
}

DEFAULT_COLOR = "#858585"


# ============================================================
# GITHUB API
# ============================================================
def api_request(url):
    """Делает запрос к GitHub API с токеном."""
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"token {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "Irmkia-Stats")
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"❌ Ошибка {e.code}: {url}")
        return None


def get_all_repos():
    """Получает ВСЕ репозитории пользователя (публичные + приватные)."""
    repos = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/user/repos"
            f"?per_page=100&page={page}&affiliation=owner"
        )
        data = api_request(url)
        if not data:
            break
        if not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1
    return repos


def get_languages(repo_full_name):
    """Получает языки для конкретного репо (байты по языкам)."""
    url = f"https://api.github.com/repos/{repo_full_name}/languages"
    data = api_request(url)
    return data or {}


# ============================================================
# ПОДСЧЁТ
# ============================================================
def count_all_languages():
    """Считает суммарные байты по каждому языку во всех репо."""
    print(f"🔍 Получаю репозитории {USERNAME}...")
    repos = get_all_repos()
    print(f"📦 Найдено репозиториев: {len(repos)}")
    
    total = {}
    for repo in repos:
        name = repo["full_name"]
        is_private = repo["private"]
        marker = "🔒" if is_private else "🌐"
        print(f"  {marker} {name}")
        
        langs = get_languages(name)
        for lang, bytes_count in langs.items():
            total[lang] = total.get(lang, 0) + bytes_count
    
    return total


# ============================================================
# SVG-ГЕНЕРАЦИЯ
# ============================================================
def make_svg(languages, width=550):
    """Рисует SVG с топом языков."""
    # Сортируем по байтам
    total_bytes = sum(languages.values()) or 1
    sorted_langs = sorted(languages.items(), key=lambda x: -x[1])
    
    # Берём топ-8
    top = sorted_langs[:8]
    
    # Размеры
    pad = 25
    header_h = 45
    row_h = 30
    bar_h = 8
    height = header_h + len(top) * row_h + pad * 2
    
    # Собираем SVG
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
    
    # Стили
    svg.append('''
    <style>
        .title { font: 600 18px 'Segoe UI', Ubuntu, sans-serif; fill: #58A6FF; }
        .lang  { font: 400 14px 'Segoe UI', Ubuntu, sans-serif; fill: #C9D1D9; }
        .pct   { font: 600 13px 'Segoe UI', Ubuntu, sans-serif; fill: #8B949E; }
    </style>
    ''')
    
    # Фон (прозрачный, как в оригинале)
    svg.append(f'<rect width="{width}" height="{height}" fill="none"/>')
    
    # Заголовок
    svg.append(f'<text x="{pad}" y="{pad + 20}" class="title">Самые используемые языки</text>')
    
    # Строки
    y = pad + header_h + 10
    for lang, bytes_count in top:
        pct = bytes_count / total_bytes * 100
        color = LANG_COLORS.get(lang, DEFAULT_COLOR)
        bar_width = int((width - pad * 2 - 100) * pct / 100)
        
        # Название языка
        svg.append(f'<text x="{pad}" y="{y}" class="lang">{lang}</text>')
        
        # Процент
        svg.append(f'<text x="{width - pad}" y="{y}" class="pct" text-anchor="end">{pct:.2f}%</text>')
        
        # Полоска
        svg.append(f'<rect x="{pad}" y="{y + 8}" width="{bar_width}" height="{bar_h}" rx="4" fill="{color}"/>')
        
        y += row_h
    
    svg.append('</svg>')
    return "\n".join(svg)


# ============================================================
# ГЛАВНАЯ
# ============================================================
def main():
    if not TOKEN:
        print("❌ Нет GITHUB_TOKEN! Запусти через GitHub Actions.")
        return
    
    languages = count_all_languages()
    
    if not languages:
        print("❌ Нет данных о языках.")
        return
    
    print(f"\n📊 Всего языков: {len(languages)}")
    total = sum(languages.values())
    for lang, b in sorted(languages.items(), key=lambda x: -x[1])[:8]:
        print(f"  {lang}: {b / total * 100:.2f}%")
    
    svg = make_svg(languages)
    
    # Создаём папку
    os.makedirs("assets", exist_ok=True)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(svg)
    
    print(f"\n✅ Сохранено: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
