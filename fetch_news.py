import feedparser
import datetime
import os

# 관심 있는 주제와 검색어, 검색 기간(최근 1일 = when:1d) 설정
TOPICS = {
    "국내 경제": "https://news.google.com/rss/search?q=국내+경제+when:1d&hl=ko&gl=KR&ceid=KR:ko",
    "세계 경제": "https://news.google.com/rss/search?q=세계+경제+when:1d&hl=ko&gl=KR&ceid=KR:ko",
    "AI 기술 동향": "https://news.google.com/rss/search?q=인공지능+OR+AI+신기술+when:1d&hl=ko&gl=KR&ceid=KR:ko",
    "프론트엔드 최신 소식": "https://news.google.com/rss/search?q=프론트엔드+OR+웹개발+when:1d&hl=ko&gl=KR&ceid=KR:ko",
    "프론트엔드 채용 공고": "https://news.google.com/rss/search?q=프론트엔드+개발자+채용+when:1d&hl=ko&gl=KR&ceid=KR:ko"
}

def fetch_news(topic_name, url, limit=5):
    """RSS URL에서 뉴스를 파싱해 최대 limit 갯수만큼 리스트로 반환"""
    feed = feedparser.parse(url)
    entries = feed.entries[:limit]
    news_items = []
    
    for entry in entries:
        news_items.append({
            "title": entry.title,
            "link": entry.link,
            "published": entry.published
        })
    return news_items

def generate_markdown():
    """뉴스들을 수집하고 마크다운 포맷의 문자열로 변환"""
    # KST 시간 기준 오늘 날짜 생성 (GitHub Actions(UTC)에서도 한국 날짜로 표기)
    kst_tz = datetime.timezone(datetime.timedelta(hours=9))
    today = datetime.datetime.now(kst_tz)
    date_str = today.strftime("%Y-%m-%d")
    
    md_content = f"# 📰 {date_str} 데일리 맞춤형 뉴스 리포트\n\n"
    
    for topic, url in TOPICS.items():
        md_content += f"## {topic}\n\n"
        news_items = fetch_news(topic, url)
        
        if not news_items:
            md_content += "- 관련 최신 뉴스가 없습니다.\n\n"
        else:
            for item in news_items:
                # 불필요한 구글 뉴스 출처 문자열 분리 (옵션)
                clean_title = item['title'].rsplit(' - ', 1)[0]
                md_content += f"- [{clean_title}]({item['link']})\n"
            md_content += "\n"
            
    return md_content, date_str

if __name__ == "__main__":
    print("📰 맞춤형 최신 뉴스를 가져오는 중입니다...")
    report_content, date_str = generate_markdown()
    
    os.makedirs("reports", exist_ok=True)
    filename = f"reports/{date_str}-news-report.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"✅ 리포트 생성이 완료되었습니다: {filename}")
