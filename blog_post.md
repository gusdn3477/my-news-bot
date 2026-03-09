# 🚀 매일 아침 8시, 나만의 AI 비서가 개발자/IT 뉴스를 요약해서 메일로 보내준다면? (feat. GitHub Actions + Gemini API)

바쁜 아침, 쏟아지는 뉴스 속에서 개발자에게 진짜 필요한 IT 동향과 경제 지표만 쏙쏙 골라 깊이 있게 읽을 수는 없을까요? 
오늘은 **Python, GitHub Actions, 그리고 무료로 쓸 수 있는 Google Gemini API**를 활용해서, **매일 아침 8시 정각에 최신 IT 동향(GeekNews 등)과 프론트엔드 생태계 소식을 상세히 요약하여 내 이메일로 자동 전송해 주는 시스템**을 구축해 보겠습니다.

단순한 3줄 요약이 아니라, **"📌 핵심 요약"**과 **"💡 실무자를 위한 주요 포인트"**로 구조화하여 퀄리티 높은 인사이트 리포트를 만들어 냅니다. 서버 비용은 당연히 **0원**입니다!

---

## 🛠️ 준비물
1. **GitHub 계정** (코드 저장 및 자동화 실행용)
2. **Google AI Studio 계정** (Gemini API 키 무료 발급용)
3. **Gmail 계정** (메일 발송용 앱 비밀번호 필요)

## 💡 시스템 구조
1. **Python 스크립트:** Google 뉴스 및 양질의 개발자 커뮤니티(GeekNews 등) RSS 피드에서 최신 기사 본문을 스크래핑합니다.
2. **Gemini API:** 수집한 기사 본문을 분석하여 핵심만 구조화하여 요약합니다.
3. **GitHub Actions:** 매일 지정된 시간에 스크립트를 실행하고, 리포트를 마크다운 파일로 저장한 뒤 이메일로 발송합니다.

---

## 💻 1단계: 파이썬 스크립트 작성 (`fetch_news.py`)

단순히 구글 뉴스만 가져오는 것이 아니라, **GeekNews RSS**를 추가하여 IT 트렌드 깊이를 더했고, 요약 프롬프트도 디테일하게 설정했습니다.

```python
import feedparser
import datetime
import os
import time
import requests
from bs4 import BeautifulSoup
from google import genai

# 양질의 IT 동향(GeekNews) 및 프론트엔드 관련 키워드 
TOPICS = {
    "📈 국내 및 세계 경제": "https://news.google.com/rss/search?q=경제+when:1d&hl=ko&gl=KR&ceid=KR:ko",
    "🤖 AI 기술 동향": "https://news.google.com/rss/search?q=인공지능+OR+AI+신기술+when:1d&hl=ko&gl=KR&ceid=KR:ko",
    "💻 GeekNews (IT/개발 동향)": "https://news.hada.io/rss",
    "🌐 프론트엔드/웹 생태계": "https://news.google.com/rss/search?q=프론트엔드+OR+웹개발+OR+React+OR+Next.js+when:1d&hl=ko&gl=KR&ceid=KR:ko"
}

API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None

def get_article_text(url):
    """URL에서 기사 본문 텍스트 추출"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')
        return ' '.join([p.get_text() for p in paragraphs])[:3000]
    except Exception:
        return ""

def summarize_with_gemini(title, text):
    """Gemini API를 사용하여 실무자 맞춤형 상세 요약"""
    if not client: return ""
    
    try:
        prompt = f"""다음 IT/경제 기사 내용을 바탕으로 실무자에게 유용한 인사이트가 담긴 상세한 요약을 작성해주세요.
        
        [요약 규칙]
        1. '📌 핵심 요약': 전체 내용을 1~2줄로 명확하게 요약해주세요.
        2. '💡 주요 포인트': 본문의 중요한 내용이나 개발자가 알아야 할 점을 3가지 이하의 글머리 기호(-)로 상세히 정리해주세요.
        
        제목: {title}
        내용: {text}"""
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        return "> ⚠️ 요약을 생성하지 못했습니다."

def fetch_news(topic_name, url, limit=3):
    feed = feedparser.parse(url)
    entries = feed.entries[:limit]
    news_items = []
    
    for entry in entries:
        clean_title = entry.title.rsplit(' - ', 1)[0]
        article_text = get_article_text(entry.link)
        
        summary = ""
        if client:
            summary = summarize_with_gemini(clean_title, article_text)
            time.sleep(4) # 무료 API Rate Limit 방지용 쿨타임
            
        news_items.append({"title": clean_title, "link": entry.link, "summary": summary})
    return news_items

def generate_markdown():
    kst_tz = datetime.timezone(datetime.timedelta(hours=9))
    today = datetime.datetime.now(kst_tz)
    date_str = today.strftime("%Y-%m-%d")
    
    md_content = f"# 🗞️ {date_str} 데일리 IT/경제 인사이트 리포트\n\n"
    
    for topic, url in TOPICS.items():
        md_content += f"## {topic}\n\n"
        news_items = fetch_news(topic, url)
        
        for item in news_items:
            md_content += f"### 🔗 [{item['title']}]({item['link']})\n\n"
            if item['summary']: md_content += f"{item['summary']}\n\n"
        md_content += "---\n\n"
            
    return md_content, date_str

if __name__ == "__main__":
    report_content, date_str = generate_markdown()
    os.makedirs("reports", exist_ok=True)
    with open(f"reports/{date_str}-news-report.md", "w", encoding="utf-8") as f:
        f.write(report_content)
```

## ⚙️ 2단계: GitHub Actions로 완벽한 자동화 구축하기

내가 자고 있을 때도 서버가 알아서 돌아가도록 `.github/workflows/daily-news.yml` 파일을 만들어 줍니다.

**💡 핵심 꿀팁: 한국 시간(KST) 맞추기**
GitHub Actions의 스케줄러(cron)는 무조건 **UTC(협정 세계시)**를 기준으로 동작합니다. 한국 시간은 UTC보다 9시간 빠르므로, **한국 시간 아침 8시 = UTC 전날 밤 11시(23:00)** 로 설정해야 합니다!

```yaml
name: Daily News Report Automation

on:
  schedule:
    # KST 아침 8시 = UTC 23:00
    - cron: '0 23 * * *'
  workflow_dispatch:

jobs:
  build-and-commit:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
    - name: 📥 코드 가져오기
      uses: actions/checkout@v4

    - name: 🐍 파이썬 환경 설정
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
        cache: 'pip'

    - name: 📦 라이브러리 설치
      run: pip install feedparser requests beautifulsoup4 google-genai

    - name: 🚀 뉴스 스크립트 실행
      env:
        GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
      run: python fetch_news.py

    - name: 📅 오늘 날짜 환경변수 설정 (KST 기준)
      run: echo "TODAY=$(TZ=Asia/Seoul date +'%Y-%m-%d')" >> $GITHUB_ENV

    - name: 📧 개인 이메일로 리포트 전송
      uses: dawidd6/action-send-mail@v3
      with:
        server_address: smtp.gmail.com
        server_port: 465
        secure: true
        username: ${{ secrets.EMAIL_USERNAME }}
        password: ${{ secrets.EMAIL_PASSWORD }}
        subject: "🗞️ ${{ env.TODAY }} 데일리 IT/경제 인사이트 리포트"
        to: ${{ secrets.TO_EMAIL }}
        from: "AI 뉴스 비서"
        body: file://reports/${{ env.TODAY }}-news-report.md

    - name: 💾 새 리포트 커밋 및 푸시
      run: |
        git config --local user.email "github-actions[bot]@users.noreply.github.com"
        git config --local user.name "github-actions[bot]"
        git add reports/
        git commit -m "docs: 🗞️ ${{ env.TODAY }} 리포트 생성" || echo "No changes"
        git push
```

## 🔐 3단계: 보안 변수(Secrets) 설정하기

코드에 API 키를 직접 적는 건 금물! GitHub의 **Settings > Secrets and variables > Actions** 메뉴에서 4가지 환경변수를 등록해 줍니다.

1. `GEMINI_API_KEY`: Google AI Studio 무료 API 키
2. `EMAIL_USERNAME`: 발송용 Gmail 주소
3. `EMAIL_PASSWORD`: 구글 계정 설정에서 발급받은 '앱 비밀번호' (16자리)
4. `TO_EMAIL`: 요약 메일을 받아볼 내 이메일 주소 (네이버, 카카오 등)

---

## 🎉 마무리

이제 모든 준비가 끝났습니다! GitHub Actions 탭에서 `Run workflow` 버튼을 눌러보세요. 
잠시 후 메일함에 **📌 핵심 요약**과 **💡 실무자를 위한 주요 포인트**가 깔끔하게 정리된 고퀄리티 리포트가 도착할 것입니다.

---

### 💌 실제 메일 수신 예시 (미리보기)

이런 식으로 매일 아침 메일함에 나만의 뉴스레터가 도착합니다!

> **[🤖 AI 기술 동향]**
> ### 🔗 [OpenAI, 새로운 추론 모델 'o3' 전격 공개]
> 
> **📌 핵심 요약**
> OpenAI가 기존 모델 대비 추론 능력이 비약적으로 향상된 새로운 모델 'o3'를 발표했습니다.
> 
> **💡 주요 포인트**
> - 수학, 코딩 등 복잡한 논리적 사고가 필요한 작업에서 뛰어난 성능을 보입니다.
> - 기존 모델과 달리 답변을 내놓기 전 내부적으로 '생각하는 시간'을 가지는 것이 특징입니다.
> - 조만간 개발자를 위한 API도 공개될 예정이며, 코딩 어시스턴트 생태계에 큰 변화가 예상됩니다.

---

정보가 쏟아지는 시대, AI 비서가 정성껏 큐레이션하고 분석해 주는 나만의 인사이트로 아침을 상쾌하게 시작해 보세요!
