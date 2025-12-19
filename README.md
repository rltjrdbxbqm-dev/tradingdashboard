# 📊 트레이딩 전략 포트폴리오 대시보드 v4.0

GitHub Actions를 통한 **자동 데이터 업데이트** 기능이 포함된 백테스트 대시보드입니다.

## ✨ 주요 기능

- ✅ **자동 데이터 업데이트**: GitHub Actions가 정해진 시간에 자동으로 데이터 수집
- ✅ **완료된 캔들만 저장**: 진행 중인 캔들은 저장하지 않아 데이터 정확성 보장
- ✅ **중복 방지**: 자동 중복 제거 로직
- ✅ **데이터 상태 모니터링**: 대시보드에서 각 파일 상태 확인 가능
- ✅ **유연한 기간 선택**: 1개월, 6개월, 1년, YTD, 전체, 또는 직접 설정

---

## 🔄 자동 업데이트 스케줄

| 데이터 | 주기 | 시간 (한국 기준) |
|--------|------|------------------|
| TQQQ (일봉) | 화~토 1회 | 06:00 |
| Bitget (4H봉) | 매일 6회 | 01:30, 05:30, 09:30, 13:30, 17:30, 21:30 |
| 업비트 (4H봉, 1D봉) | 매일 6회 | 01:30, 05:30, 09:30, 13:30, 17:30, 21:30 |

### 데이터 저장 로직

```
현재 시간: 14:30
├── 4H봉: 12:00 캔들까지 완료 (09:00~12:59 데이터)
│          16:00 캔들은 아직 진행 중 → 저장 안 함
│
└── 일봉: 어제까지 완료
          오늘 캔들은 진행 중 → 저장 안 함
```

**→ 새로고침해도 잘못된 데이터가 쌓이지 않습니다!**

---

## 📁 폴더 구조

```
trading-dashboard/
├── app.py                          # Streamlit 대시보드
├── requirements.txt
├── README.md
├── .github/
│   └── workflows/
│       └── update_data.yml         # GitHub Actions 워크플로우
├── scripts/
│   └── update_data.py              # 데이터 업데이트 스크립트
└── data/                           # CSV 데이터 (자동 생성됨)
    ├── tqqq_daily.csv
    ├── bitget_btc_4h.csv
    ├── bitget_eth_4h.csv
    ├── bitget_sol_4h.csv
    ├── upbit_ada_4h.csv
    ├── upbit_ada_1d.csv
    └── ... (나머지 코인)
```

---

## 🚀 배포 방법

### Step 1: GitHub 저장소 생성

1. GitHub에서 새 저장소 생성 (Public)
2. 모든 파일 업로드

### Step 2: 초기 데이터 업로드 (선택)

기존에 수집한 CSV 파일이 있다면 `data/` 폴더에 업로드하세요.
없으면 GitHub Actions가 처음 실행될 때 자동으로 3년치 데이터를 수집합니다.

### Step 3: GitHub Actions 활성화

1. 저장소 → **Settings** → **Actions** → **General**
2. **Workflow permissions**: "Read and write permissions" 선택
3. **Allow GitHub Actions to create and approve pull requests** 체크
4. **Save**

### Step 4: 수동으로 첫 실행 (선택)

1. 저장소 → **Actions** 탭
2. **"Update Trading Data"** 워크플로우 선택
3. **"Run workflow"** 버튼 클릭

### Step 5: Streamlit Cloud 배포

1. https://share.streamlit.io 접속
2. **"New app"** → GitHub 저장소 선택
3. Main file: `app.py`
4. **"Deploy!"**

---

## 🔍 데이터 상태 확인 방법

### 대시보드에서 확인
사이드바 → **"📁 데이터 상태 확인"** 펼치기

표시 정보:
- ✅/❌ 파일 존재 여부
- 데이터 행 수
- 시작일 ~ 종료일
- 누락된 코인 목록

### GitHub에서 확인
1. 저장소 → **Actions** 탭
2. 최근 실행 기록 확인
3. 로그에서 업데이트 상세 내용 확인

---

## ⚙️ 전략 파라미터

### TQQQ Sniper (일봉)
| 지표 | 파라미터 |
|------|----------|
| Stochastic | period=166, K=57, D=19 |
| MA | 20, 45, 151, 212 |

### Bitget 선물 (4H봉)
| 코인 | MA | Stochastic | 레버리지 |
|------|-----|------------|----------|
| BTC | 248 | (46,37,4) | 4x |
| ETH | 152 | (58,23,18) | 4x |
| SOL | 64 | (51,20,16) | 2x |

### 업비트 현물 (MA: 4H, Stoch: 1D)
| 코인 | MA | Stochastic |
|------|-----|------------|
| ADA | 83 | (60,25,5) |
| BTC | 276 | (80,25,5) |
| ETH | 201 | (60,20,5) |
| XRP | 64 | (70,20,5) |
| ... | ... | ... |

---

## ❓ FAQ

### Q: 데이터가 안 쌓이면?
1. **Actions 탭** 확인 → 에러 로그 확인
2. **Settings → Actions** → 권한 확인
3. 수동으로 **"Run workflow"** 실행

### Q: 특정 코인만 데이터가 없으면?
업비트/바이낸스 API 일시적 오류일 수 있습니다.
다음 스케줄에 자동으로 재시도됩니다.

### Q: 3년 이전 데이터를 넣고 싶으면?
기존 CSV 파일을 `data/` 폴더에 직접 업로드하세요.
형식만 맞으면 자동으로 이어서 업데이트됩니다.

### Q: 수동으로 데이터 업데이트하고 싶으면?
1. **Actions** → **Update Trading Data** → **Run workflow**
2. 또는 로컬에서 `python scripts/update_data.py` 실행 후 push

---

## 📝 라이선스

MIT License

---

⚠️ **면책 조항**: 이 대시보드는 교육 목적으로만 제공됩니다. 실제 투자 결정은 본인의 판단과 책임 하에 이루어져야 합니다.
