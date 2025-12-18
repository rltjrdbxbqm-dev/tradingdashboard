# Historical Data 폴더

이 폴더에 `download_historical_data.py` 스크립트로 다운로드한 CSV 파일들을 복사하세요.

## 필요한 파일 목록

### TQQQ (1개 파일)
- tqqq_daily.csv

### Bitget - Binance Futures (3개 파일)
- bitget_btc_4h.csv
- bitget_eth_4h.csv
- bitget_sol_4h.csv

### Upbit (40개 파일 - 코인당 4H, 1D 각각)
- upbit_ada_4h.csv, upbit_ada_1d.csv
- upbit_ankr_4h.csv, upbit_ankr_1d.csv
- upbit_avax_4h.csv, upbit_avax_1d.csv
- upbit_axs_4h.csv, upbit_axs_1d.csv
- upbit_bch_4h.csv, upbit_bch_1d.csv
- upbit_btc_4h.csv, upbit_btc_1d.csv
- upbit_cro_4h.csv, upbit_cro_1d.csv
- upbit_doge_4h.csv, upbit_doge_1d.csv
- upbit_eth_4h.csv, upbit_eth_1d.csv
- upbit_hbar_4h.csv, upbit_hbar_1d.csv
- upbit_imx_4h.csv, upbit_imx_1d.csv
- upbit_mana_4h.csv, upbit_mana_1d.csv
- upbit_mvl_4h.csv, upbit_mvl_1d.csv
- upbit_sand_4h.csv, upbit_sand_1d.csv
- upbit_sol_4h.csv, upbit_sol_1d.csv
- upbit_theta_4h.csv, upbit_theta_1d.csv
- upbit_vet_4h.csv, upbit_vet_1d.csv
- upbit_waxp_4h.csv, upbit_waxp_1d.csv
- upbit_xlm_4h.csv, upbit_xlm_1d.csv
- upbit_xrp_4h.csv, upbit_xrp_1d.csv

## CSV 파일 형식

### TQQQ (일봉)
```
date,open,high,low,close,volume
2021-12-17,152.23,155.67,151.89,154.32,12345678
```

### Bitget/Upbit (4시간봉)
```
datetime,open,high,low,close,volume
2021-12-17 00:00:00,48123.45,48500.00,47800.00,48250.00,1234.56
```

### Upbit (일봉)
```
datetime,open,high,low,close,volume
2021-12-17 00:00:00,48123.45,48500.00,47800.00,48250.00,1234.56
```

## 데이터 다운로드 방법

1. PC에서 Python 환경 설정:
   ```bash
   pip install yfinance pandas requests
   ```

2. 다운로드 스크립트 실행:
   ```bash
   python download_historical_data.py
   ```

3. 생성된 `historical_data` 폴더의 모든 파일을 이 폴더로 복사

## 앱 동작 방식

1. 앱 최초 실행 시 assets의 CSV 파일을 내부 저장소로 복사
2. 이후 새 데이터는 API에서 가져와서 기존 CSV에 추가
3. 백테스트는 항상 CSV 데이터 기반으로 수행
