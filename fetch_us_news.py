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
    """Gemini Pro API를 사용하여 수집된 모든 뉴스의 의미를 심층 분석하여 마크다운 리포트 생성"""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "⚠️ GEMINI_API_KEY가 설정되지 않아 분석할 수 없습니다."
        
    try:
        client = genai.Client(api_key=api_key)
        
        prompt = "다음은 최근 1시간 동안 수집된 미국 주요 뉴스(종합, 정치, 경제)입니다.\n\n"
        for i, news in enumerate(news_list, 1):
            prompt += f"{i}. [{news['topic']}] {news['title']} (링크: {news['link']})\n"
            
        prompt += """
당신은 미국의 정치, 경제, 사회 동향을 날카롭게 짚어내는 수석 애널리스트입니다.
위 뉴스 기사들을 종합적으로 분석하여, 단순히 사실이나 기사 제목을 나열하는 것을 넘어서 **"현재 미국의 가장 중요한 흐름과 그것이 앞으로 미칠 파장(의미)"**에 집중해 심층 리포트를 작성해 주세요.
단순히 하단에 링크 목록을 따로 나열하지 말고, 분석 내용의 문맥 속에 자연스럽게 관련 기사 내용을 녹여내며 하이퍼링크 형식으로 출처를 달아주세요.
독자가 이 리포트 하나만 읽고도 지금 미국의 큰 그림을 이해할 수 있도록 통찰력 있고 전문적인 어조(한국어)로 작성해 주세요.
출력 형식은 마크다운으로 깔끔하게 정리해 주세요.
"""
        
        # 우선 3.0 Pro 모델로 시도하고, 지원하지 않아 오류 발생 시 2.5 Pro로 안전하게 대체(Fallback)
        try:
            response = client.models.generate_content(
                model='gemini-3.0-pro',
                contents=prompt,
            )
        except Exception as e:
            print(f"⚠️ gemini-3.0-pro 호출 실패 ({e}). gemini-2.5-pro 모델로 대체하여 분석합니다.")
            response = client.models.generate_content(
                model='gemini-2.5-pro',
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
    
    md_content = f"# 🗞️ {date_str} {time_str} 미국 실시간 심층 의미 분석 리포트\n\n"
    md_content += f"> {time_str} 기준 최근 1시간 동안의 미국 주요 뉴스를 바탕으로, 겉으로 드러난 현상 너머의 핵심적인 흐름과 의미를 Gemini Pro 모델이 애널리스트의 관점에서 심층 평가했습니다.\n\n"
    
    all_news_for_analysis = []
    
    for topic, url in TOPICS.items():
        print(f"[{topic}] 뉴스 수집 중...")
        news_items, _ = fetch_news(url, limit=3) 
        
        if news_items:
            for item in news_items:
                all_news_for_analysis.append({
                    "topic": topic, 
                    "title": item['title'], 
                    "link": item['link']
                })
            
    # 수집된 뉴스를 한 번에 Pro 모델로 분석하여 전체 내용을 구성
    print("🧠 Gemini Pro 모델로 심층 의미 평가 진행 중...")
    if all_news_for_analysis:
        analysis_result = analyze_all_news(all_news_for_analysis)
        md_content += f"{analysis_result}\n\n"
    else:
        md_content += "## 💡 분석 알림\n\n최근 1시간 동안 수집된 주요 뉴스가 없어 분석을 생략합니다.\n\n"
        
    return md_content, date_str, time_str.replace(":", "")

if __name__ == "__main__":
    print("📰 미국 실시간 뉴스 및 심층 분석을 가져오는 중입니다...")
    report_content, date_str, time_str = generate_markdown()
    
    os.makedirs("reports/us_news", exist_ok=True)
    filename = f"reports/us_news/{date_str}-{time_str}-us-news-report.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"✅ 리포트 생성이 완료되었습니다: {filename}")
