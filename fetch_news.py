import feedparser
import datetime
import os

# 정치, 경제, 사회, 문화 + 지역 뉴스(경기도, 성남, 수정구) 추가
TOPICS = {
    "🏛️ 정치": "https://news.google.com/rss/search?q=정치+when:1d&hl=ko&gl=KR&ceid=KR:ko",
    "📈 경제": "https://news.google.com/rss/search?q=경제+when:1d&hl=ko&gl=KR&ceid=KR:ko",
    "👥 사회": "https://news.google.com/rss/search?q=사회+when:1d&hl=ko&gl=KR&ceid=KR:ko",
    "🎨 문화": "https://news.google.com/rss/search?q=문화+when:1d&hl=ko&gl=KR&ceid=KR:ko",
    "📍 경기도": "https://news.google.com/rss/search?q=경기도+when:1d&hl=ko&gl=KR&ceid=KR:ko",
    "🏙️ 성남시": "https://news.google.com/rss/search?q=성남시+when:1d&hl=ko&gl=KR&ceid=KR:ko",
    "🏠 수정구": "https://news.google.com/rss/search?q=성남+수정구+when:1d&hl=ko&gl=KR&ceid=KR:ko"
}

def fetch_news(url, limit=10):
    """뉴스를 가져오고 갯수를 반환"""
    feed = feedparser.parse(url)
    all_entries = feed.entries
    total_count = len(all_entries)
    
    entries = all_entries[:limit]
    news_items = []
    
    for entry in entries:
        # 구글 뉴스 뒤에 붙는 ' - 언론사명' 제거
        clean_title = entry.title.rsplit(' - ', 1)[0]
        link = entry.link
        
        news_items.append({
            "title": clean_title,
            "link": link
        })
    return news_items, total_count

def generate_markdown():
    """뉴스 목록과 갯수를 마크다운 포맷으로 변환"""
    kst_tz = datetime.timezone(datetime.timedelta(hours=9))
    today = datetime.datetime.now(kst_tz)
    date_str = today.strftime("%Y-%m-%d")
    
    md_content = f"# 🗞️ {date_str} 데일리 종합 뉴스 리포트\n\n"
    md_content += "> 주요 분야 및 관심 지역의 실시간 뉴스 현황입니다.\n\n"
    
    for topic, url in TOPICS.items():
        print(f"[{topic}] 뉴스 수집 중...")
        news_items, total_count = fetch_news(url, limit=5)
        
        md_content += f"## {topic} (총 {total_count}건)\n\n"
        
        if not news_items:
            md_content += "- 관련 최신 뉴스가 없습니다.\n\n"
        else:
            for item in news_items:
                md_content += f"- [{item['title']}]({item['link']})\n"
            
            if total_count > len(news_items):
                md_content += f"\n> *외 {total_count - len(news_items)}개의 뉴스가 더 있습니다.*\n"
            md_content += "\n---\n\n"
            
    return md_content, date_str

if __name__ == "__main__":
    print("📰 맞춤형 뉴스를 가져오는 중입니다...")
    report_content, date_str = generate_markdown()
    
    os.makedirs("reports", exist_ok=True)
    filename = f"reports/{date_str}-news-report.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"✅ 리포트 생성이 완료되었습니다: {filename}")
