import feedparser
import datetime
import os
import time
import requests
from bs4 import BeautifulSoup
from google import genai

# 관심 있는 주제와 검색어 (GeekNews 추가 및 프론트엔드 키워드 강화)
TOPICS = {
    "📈 국내 및 세계 경제": "https://news.google.com/rss/search?q=경제+when:1d&hl=ko&gl=KR&ceid=KR:ko",
    "🤖 AI 기술 동향": "https://news.google.com/rss/search?q=인공지능+OR+AI+신기술+when:1d&hl=ko&gl=KR&ceid=KR:ko",
    "💻 GeekNews (IT/개발 동향)": "https://news.hada.io/rss",
    "🌐 프론트엔드/웹 생태계": "https://news.google.com/rss/search?q=프론트엔드+OR+웹개발+OR+React+OR+Next.js+when:1d&hl=ko&gl=KR&ceid=KR:ko"
}

API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None

def get_article_text(url):
    """URL에서 기사 본문 텍스트 추출 (가벼운 스크래핑)"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')
        text = ' '.join([p.get_text() for p in paragraphs])
        return text[:3000] # API에 넘길 텍스트 길이 제한
    except Exception:
        return ""

def summarize_with_gemini(title, text, max_retries=3):
    """Gemini API를 사용하여 구조화된 상세 요약 생성 (429 에러 시 자동 재시도 포함)"""
    if not client:
        return ""
    
    prompt = f"""다음 IT/경제 기사 내용을 바탕으로 실무자에게 유용한 인사이트가 담긴 상세한 요약을 작성해주세요.
    
    [요약 규칙]
    1. '📌 핵심 요약': 전체 내용을 1~2줄로 명확하게 요약해주세요.
    2. '💡 주요 포인트': 본문의 중요한 내용이나 개발자가 알아야 할 점을 3가지 이하의 글머리 기호(-)로 상세히 정리해주세요.
    
    제목: {title}
    내용: {text}"""
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            error_msg = str(e).replace('\n', ' ')
            if '429' in error_msg and attempt < max_retries - 1:
                print(f"⚠️ 429 에러 감지. 20초 대기 후 재시도 합니다... ({attempt + 1}/{max_retries})")
                time.sleep(20) # 429 에러 시 20초간 길게 대기 후 재시도
                continue
            
            print(f"Gemini API 오류: {error_msg}")
            return f"> ⚠️ 요약을 생성하지 못했습니다. (사유: {error_msg})"

def fetch_news(topic_name, url, limit=3):
    """최대 limit 갯수만큼 뉴스를 가져와 요약 진행"""
    feed = feedparser.parse(url)
    entries = feed.entries[:limit]
    news_items = []
    
    for entry in entries:
        # 구글 뉴스 뒤에 붙는 ' - 언론사명' 제거
        clean_title = entry.title.rsplit(' - ', 1)[0]
        link = entry.link
        
        # 기사 내용 스크래핑 및 요약
        article_text = get_article_text(link)
        summary = ""
        if client:
            summary = summarize_with_gemini(clean_title, article_text)
            time.sleep(10) # 무료 API Rate Limit(1분 15회) 방지를 위해 아주 넉넉한 10초 쿨타임
            
        news_items.append({
            "title": clean_title,
            "link": link,
            "summary": summary
        })
    return news_items

def generate_markdown():
    """요약된 뉴스들을 마크다운 포맷으로 변환"""
    kst_tz = datetime.timezone(datetime.timedelta(hours=9))
    today = datetime.datetime.now(kst_tz)
    date_str = today.strftime("%Y-%m-%d")
    
    # 이메일에서 더 보기 좋도록 헤더 디자인 수정
    md_content = f"# 🗞️ {date_str} 데일리 IT/경제 인사이트 리포트\n\n"
    
    if not API_KEY:
        md_content += "> ⚠️ **안내:** `GEMINI_API_KEY`가 설정되지 않아 AI 요약이 생략되고 기사 목록만 표시됩니다.\n\n"
    
    for topic, url in TOPICS.items():
        print(f"[{topic}] 뉴스 수집 및 요약 중...")
        md_content += f"## {topic}\n\n"
        news_items = fetch_news(topic, url, limit=3 if API_KEY else 5)
        
        if not news_items:
            md_content += "- 관련 최신 뉴스가 없습니다.\n\n"
        else:
            for item in news_items:
                md_content += f"### 🔗 [{item['title']}]({item['link']})\n\n"
                if item['summary']:
                    md_content += f"{item['summary']}\n\n"
                else:
                    md_content += "\n"
            md_content += "---\n\n"
            
    return md_content, date_str

if __name__ == "__main__":
    print("📰 맞춤형 최신 뉴스를 가져오는 중입니다...")
    report_content, date_str = generate_markdown()
    
    os.makedirs("reports", exist_ok=True)
    filename = f"reports/{date_str}-news-report.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"✅ 리포트 생성이 완료되었습니다: {filename}")