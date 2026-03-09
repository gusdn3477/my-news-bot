import feedparser
import datetime
import os
import time
import requests
from bs4 import BeautifulSoup
from google import genai

# 관심 있는 주제와 검색어
TOPICS = {
    "국내 경제": "https://news.google.com/rss/search?q=국내+경제+when:1d&hl=ko&gl=KR&ceid=KR:ko",
    "세계 경제": "https://news.google.com/rss/search?q=세계+경제+when:1d&hl=ko&gl=KR&ceid=KR:ko",
    "AI 기술 동향": "https://news.google.com/rss/search?q=인공지능+OR+AI+신기술+when:1d&hl=ko&gl=KR&ceid=KR:ko",
    "프론트엔드 최신 소식": "https://news.google.com/rss/search?q=프론트엔드+OR+웹개발+when:1d&hl=ko&gl=KR&ceid=KR:ko",
    "프론트엔드 채용 공고": "https://news.google.com/rss/search?q=프론트엔드+개발자+채용+when:1d&hl=ko&gl=KR&ceid=KR:ko"
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

def summarize_with_gemini(title, text, is_job=False):
    """Gemini API를 사용하여 요약 또는 채용공고 분석"""
    if not client:
        return ""
    
    try:
        if is_job:
            prompt = f"다음은 프론트엔드 개발자 채용 공고의 제목과 내용 일부입니다. 현재 연차 3년 6개월(미들급) 개발자가 지원하기 적합한 포지션인지 분석해주세요. 적합하다면 '✅ **추천**', 아니라면 '⚠️ **보류**'로 시작하고, 그 이유를 1~2줄로 간결하게 설명해주세요.\n제목: {title}\n내용: {text}"
        else:
            prompt = f"다음 뉴스 기사의 핵심 내용을 3줄로 요약해주세요. 각 줄은 마크다운 글머리 기호(-)로 시작하세요. 내용이 부족하면 제목을 바탕으로 유추해서라도 자연스럽게 요약해주세요.\n제목: {title}\n내용: {text}"
            
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f"Gemini API 오류: {e}")
        return "> ⚠️ 요약을 생성하지 못했습니다."

def fetch_news(topic_name, url, limit=3):
    """최대 limit 갯수만큼 뉴스를 가져와 요약 진행"""
    feed = feedparser.parse(url)
    entries = feed.entries[:limit]
    news_items = []
    
    is_job = (topic_name == "프론트엔드 채용 공고")
    
    for entry in entries:
        clean_title = entry.title.rsplit(' - ', 1)[0]
        link = entry.link
        
        # 기사 내용 스크래핑 및 요약
        article_text = get_article_text(link)
        summary = ""
        if client:
            summary = summarize_with_gemini(clean_title, article_text, is_job)
            time.sleep(4) # 무료 티어 1분당 15회 제한 방지를 위해 4초 대기
            
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
    
    md_content = f"# 📰 {date_str} 데일리 맞춤형 AI 뉴스 리포트\n\n"
    
    if not API_KEY:
        md_content += "> ⚠️ **안내:** `GEMINI_API_KEY`가 설정되지 않아 AI 요약이 생략되고 기사 목록만 표시됩니다.\n\n"
    
    for topic, url in TOPICS.items():
        print(f"[{topic}] 뉴스 수집 및 요약 중...")
        md_content += f"## {topic}\n\n"
        # API가 있으면 3개씩 꼼꼼히 요약, 없으면 5개씩 제목만 나열
        news_items = fetch_news(topic, url, limit=3 if API_KEY else 5)
        
        if not news_items:
            md_content += "- 관련 최신 뉴스가 없습니다.\n\n"
        else:
            for item in news_items:
                md_content += f"### [{item['title']}]({item['link']})\n"
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