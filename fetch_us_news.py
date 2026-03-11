import feedparser
import datetime
import os
from google import genai

# 미국 실시간 뉴스 (최근 1시간)
TOPICS = {
    "🇺🇸 미국 종합": "https://news.google.com/rss/search?q=US+news+when:1h&hl=en-US&gl=US&ceid=US:en",
    "🏛️ 미국 정치": "https://news.google.com/rss/search?q=US+politics+when:1h&hl=en-US&gl=US&ceid=US:en",
    "📈 미국 경제": "https://news.google.com/rss/search?q=US+economy+when:1h&hl=en-US&gl=US&ceid=US:en",
}

def fetch_news(url, limit=3):
    """뉴스를 가져오고 갯수를 반환"""
    feed = feedparser.parse(url)
    all_entries = feed.entries
    total_count = len(all_entries)
    
    entries = all_entries[:limit]
    news_items = []
    
    for entry in entries:
        clean_title = entry.title.rsplit(' - ', 1)[0]
        link = entry.link
        
        news_items.append({
            "title": clean_title,
            "link": link
        })
    return news_items, total_count

def analyze_all_news(news_list):
    """Gemini Pro API를 사용하여 수집된 모든 뉴스를 한 번에 종합 분석"""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "⚠️ GEMINI_API_KEY가 설정되지 않아 분석할 수 없습니다."
        
    try:
        client = genai.Client(api_key=api_key)
        
        prompt = "다음은 최근 1시간 동안 수집된 미국 주요 뉴스(종합, 정치, 경제)의 기사 제목들입니다:\n\n"
        for i, news in enumerate(news_list, 1):
            prompt += f"{i}. [{news['topic']}] {news['title']}\n"
            
        prompt += "\n위 뉴스 제목들을 종합적으로 고려하여, 현재 미국의 핵심적인 정치/경제/사회적 흐름과 이것이 가지는 의미를 한국어로 3~4줄 이내로 깊이 있게 분석해 줘."
        
        # 3.1 Pro 모델 사용 (하루 50회 제한 내에서 사용 가능하도록 1시간에 1번만 일괄 호출)
        response = client.models.generate_content(
            model='gemini-3.1-pro',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        return f"분석 중 오류 발생: {e}"

def generate_markdown():
    """뉴스 목록과 종합 분석 결과를 마크다운 포맷으로 변환"""
    kst_tz = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(kst_tz)
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:00")
    
    md_content = f"# 🗞️ {date_str} {time_str} 미국 실시간 뉴스 및 종합 분석 (Pro)\n\n"
    md_content += f"> {time_str} 기준 최근 1시간 동안의 미국 주요 뉴스를 수집하여 Gemini Pro 모델로 심층 분석한 리포트입니다.\n\n"
    
    all_news_for_analysis = []
    sections_content = ""
    
    for topic, url in TOPICS.items():
        print(f"[{topic}] 뉴스 수집 중...")
        # 분야별 뉴스 3개씩 수집
        news_items, total_count = fetch_news(url, limit=3) 
        
        sections_content += f"## {topic} (최근 1시간 총 {total_count}건)\n\n"
        
        if not news_items:
            sections_content += "- 관련 최신 뉴스가 없습니다.\n\n"
        else:
            for item in news_items:
                all_news_for_analysis.append({"topic": topic, "title": item['title']})
                sections_content += f"- [{item['title']}]({item['link']})\n"
            
            if total_count > len(news_items):
                sections_content += f"\n> *외 {total_count - len(news_items)}개의 뉴스가 더 있습니다.*\n\n"
            sections_content += "---\n\n"
            
    # 수집된 뉴스를 한 번에 Pro 모델로 분석
    print("🧠 Gemini Pro 모델로 종합 분석 중...")
    if all_news_for_analysis:
        analysis_result = analyze_all_news(all_news_for_analysis)
        md_content += "## 💡 Gemini Pro 심층 종합 분석\n\n"
        md_content += f"> {analysis_result.replace(chr(10), chr(10) + '> ')}\n\n---\n\n" # 줄바꿈마다 > 추가하여 인용구 처리
    else:
        md_content += "## 💡 분석 알림\n\n수집된 뉴스가 없어 분석을 생략합니다.\n\n---\n\n"
        
    # 각 분야별 뉴스 목록 추가
    md_content += sections_content
            
    return md_content, date_str, time_str.replace(":", "")

if __name__ == "__main__":
    print("📰 미국 실시간 뉴스 및 분석을 가져오는 중입니다...")
    report_content, date_str, time_str = generate_markdown()
    
    os.makedirs("reports/us_news", exist_ok=True)
    filename = f"reports/us_news/{date_str}-{time_str}-us-news-report.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"✅ 리포트 생성이 완료되었습니다: {filename}")