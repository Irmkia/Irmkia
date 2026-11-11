"""
Генератор SVG-картинок для профиля: языки + статистика.
Читает ВСЕ репозитории (включая приватные).
"""
import os
import json
import urllib.request
import urllib.error

# ============================================================
# НАСТРОЙКИ
# ============================================================
USERNAME = "Irmkia"
TOKEN = os.environ.get("GITHUB_TOKEN")

LANG_COLORS = {
    "Python": "#3572A5", "TypeScript": "#3178c6", "JavaScript": "#f1e05a",
    "HTML": "#e34c26", "CSS": "#563d7c", "Shell": "#89e051",
    "Dockerfile": "#384d54", "JSON": "#292929", "Markdown": "#083fa1",
    "SQL": "#e38c00", "Rust": "#dea584", "Go": "#00ADD8",
}
DEFAULT_COLOR = "#858585"

# ============================================================
# GITHUB API
# ============================================================
def api_request(url, is_search=False):
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"token {TOKEN}")
    req.add_header("User-Agent", "Irmkia-Stats")
    # Для поиска коммитов нужен специальный заголовок
    if is_search:
        req.add_header("Accept", "application/vnd.github.cloak-preview")
    else:
        req.add_header("Accept", "application/vnd.github+json")
        
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"❌ Ошибка {e.code}: {url}")
        return None

def get_all_repos():
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/user/repos?per_page=100&page={page}&affiliation=owner"
        data = api_request(url)
        if not data: break
        repos.extend(data)
        if len(data) < 100: break
        page += 1
    return repos

def get_languages(repo_full_name):
    url = f"https://api.github.com/repos/{repo_full_name}/languages"
    return api_request(url) or {}

def get_user_stats():
    """Получает общую статистику пользователя (коммиты, PR, issues, звезды)."""
    user = api_request(f"https://api.github.com/users/{USERNAME}")
    repos = get_all_repos()
    
    # Считаем звезды
    total_stars = sum(repo.get("stargazers_count", 0) for repo in repos)
    
    # Ищем коммиты (через поиск GitHub API)
    commit_data = api_request(f"https://api.github.com/search/commits?q=author:{USERNAME}", is_search=True)
    total_commits = commit_data.get("total_count", 0) if commit_data else 0

    # PR и Issues (через поиск)
    pr_data = api_request(f"https://api.github.com/search/issues?q=author:{USERNAME}+type:pr")
    issue_data = api_request(f"https://api.github.com/search/issues?q=author:{USERNAME}+type:issue")
    
    return {
        "stars": total_stars,
        "commits": total_commits,
        "prs": pr_data.get("total_count", 0) if pr_data else 0,
        "issues": issue_data.get("total_count", 0) if issue_data else 0,
        "name": user.get("name") or USERNAME if user else USERNAME
    }

# ============================================================
# ГЕНЕРАЦИЯ КАРТИНКИ ЯЗЫКОВ
# ============================================================
def make_langs_svg(languages, theme="dark", width=550):
    if theme == "dark":
        title_color, text_color, pct_color = "#58A6FF", "#C9D1D9", "#8B949E"
    else:
        title_color, text_color, pct_color = "#0969DA", "#24292F", "#57606A"
    
    total_bytes = sum(languages.values()) or 1
    top = sorted(languages.items(), key=lambda x: -x[1])[:8]
    height = 45 + len(top) * 30 + 50
    
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    svg.append(f'<style>.title {{ font: 600 18px "Segoe UI", sans-serif; fill: {title_color}; }} .lang {{ font: 400 14px "Segoe UI", sans-serif; fill: {text_color}; }} .pct {{ font: 600 13px "Segoe UI", sans-serif; fill: {pct_color}; }}</style>')
    svg.append(f'<text x="25" y="45" class="title">Самые используемые языки</text>')
    
    y = 75
    for lang, b in top:
        pct = b / total_bytes * 100
        color = LANG_COLORS.get(lang, DEFAULT_COLOR)
        bar_w = int((width - 150) * pct / 100)
        svg.append(f'<text x="25" y="{y}" class="lang">{lang}</text>')
        svg.append(f'<text x="{width-25}" y="{y}" class="pct" text-anchor="end">{pct:.2f}%</text>')
        svg.append(f'<rect x="25" y="{y+8}" width="{bar_w}" height="8" rx="4" fill="{color}"/>')
        y += 30
    svg.append('</svg>')
    return "\n".join(svg)

# ============================================================
# ГЕНЕРАЦИЯ КАРТИНКИ СТАТИСТИКИ
# ============================================================
def make_stats_svg(stats, theme="dark", width=550):
    if theme == "dark":
        title_color, text_color, icon_color = "#58A6FF", "#C9D1D9", "#58A6FF"
    else:
        title_color, text_color, icon_color = "#0969DA", "#24292F", "#0969DA"
        
    height = 195
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    
    # Стили
    svg.append(f'''
    <style>
        .title {{ font: 600 18px "Segoe UI", sans-serif; fill: {title_color}; }}
        .label {{ font: 600 14px "Segoe UI", sans-serif; fill: {text_color}; }}
        .value {{ font: 600 14px "Segoe UI", sans-serif; fill: {text_color}; }}
        .icon  {{ font: 16px sans-serif; fill: {icon_color}; }}
    </style>
    ''')
    
    # Заголовок
    svg.append(f'<text x="25" y="35" class="title">Статистика GitHub пользователя {stats["name"]}</text>')
    
    # Данные
    rows = [
        ("⭐", "Всего звёзд:", stats["stars"]),
        ("📦", "Всего коммитов:", stats["commits"]),
        ("🔀", "Всего запросов изменений:", stats["prs"]),
        ("🐛", "Всего вопросов:", stats["issues"]),
    ]
    
    y = 70
    for icon, label, val in rows:
        svg.append(f'<text x="25" y="{y}" class="icon">{icon}</text>')
        svg.append(f'<text x="55" y="{y}" class="label">{label}</text>')
        svg.append(f'<text x="{width-25}" y="{y}" class="value" text-anchor="end">{val}</text>')
        y += 30
        
    svg.append('</svg>')
    return "\n".join(svg)


# ============================================================
# ГЛАВНАЯ
# ============================================================
def main():
    if not TOKEN:
        print("❌ Нет GITHUB_TOKEN!")
        return

    # 1. Считаем языки
    print("🔍 Считаю языки...")
    repos = get_all_repos()
    languages = {}
    for repo in repos:
        langs = get_languages(repo["full_name"])
        for lang, b in langs.items():
            languages[lang] = languages.get(lang, 0) + b

    # 2. Получаем статистику
    print("📊 Собираю статистику...")
    stats = get_user_stats()

    # 3. Сохраняем
    os.makedirs("assets", exist_ok=True)
    for theme in ["dark", "light"]:
        # Языки
        with open(f"assets/top-langs-{theme}.svg", "w", encoding="utf-8") as f:
            f.write(make_langs_svg(languages, theme))
        # Статистика
        with open(f"assets/github-stats-{theme}.svg", "w", encoding="utf-8") as f:
            f.write(make_stats_svg(stats, theme))
            
    print("✅ Все картинки сохранены!")

if __name__ == "__main__":
    main()
