import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import os
import requests
import time
import warnings

# 불필요한 FutureWarning 숨기기
warnings.simplefilter(action='ignore', category=FutureWarning)

# ════════════════════════════════════════════════════════════════════════════════
# 설정
# ════════════════════════════════════════════════════════════════════════════════

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

# Bitget 선물 코인 목록
BITGET_SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']

# 업비트 코인 목록
UPBIT_SYMBOLS = [
    'KRW-ADA', 'KRW-ANKR', 'KRW-AVAX', 'KRW-AXS', 'KRW-BCH',
    'KRW-BTC', 'KRW-CRO', 'KRW-DOGE', 'KRW-ETH', 'KRW-HBAR',
    'KRW-IMX', 'KRW-MANA', 'KRW-MVL', 'KRW-SAND', 'KRW-SOL',
    'KRW-THETA', 'KRW-VET', 'KRW-WAXP', 'KRW-XLM', 'KRW-XRP'
]

# ════════════════════════════════════════════════════════════════════════════════
# 유틸리티 함수
# ════════════════════════════════════════════════════════════════════════════════

def get_last_completed_candle_time(interval: str) -> datetime:
    """완료된 마지막 캔들 시간 계산 (UTC 기준)"""
    now = datetime.now(timezone.utc)
    
    if interval == '1d':
        # 일봉: 어제까지 완료
        last_complete = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    elif interval == '4h':
        # 4시간봉: 현재 시간 기준 마지막 완료된 캔들
        # 캔들 시작 시간: 0, 4, 8, 12, 16, 20시
        current_hour = now.hour
        last_candle_hour = (current_hour // 4) * 4
        last_complete = now.replace(hour=last_candle_hour, minute=0, second=0, microsecond=0) - timedelta(hours=4)
    else:
        last_complete = now - timedelta(hours=1)
    
    return last_complete


def load_existing_csv(filepath: str) -> pd.DataFrame:
    """기존 CSV 파일 로드"""
    if not os.path.exists(filepath):
        return None
    
    try:
        df = pd.read_csv(filepath)
        
        # datetime 컬럼 처리
        if 'date' in df.columns:
            df['datetime'] = pd.to_datetime(df['date'])
        elif 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
        
        df.set_index('datetime', inplace=True)
        # 중요: CSV 데이터는 Timezone 정보 없이 로드 (Naive)
        df.index = df.index.tz_localize(None)
        
        return df
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None


def save_csv(df: pd.DataFrame, filepath: str, date_col: str = 'datetime'):
    """CSV 파일 저장"""
    df_save = df.copy()
    df_save = df_save.reset_index()
    
    # 컬럼명 정리
    if 'index' in df_save.columns:
        df_save = df_save.rename(columns={'index': date_col})
    
    # 중복 제거 (datetime 기준)
    df_save = df_save.drop_duplicates(subset=[date_col], keep='last')
    df_save = df_save.sort_values(date_col)
    
    df_save.to_csv(filepath, index=False)
    print(f"✅ Saved {len(df_save)} rows to {filepath}")


def merge_and_dedupe(existing: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    """기존 데이터와 새 데이터 병합 및 중복 제거"""
    if existing is None or len(existing) == 0:
        return new
    if new is None or len(new) == 0:
        return existing
    
    combined = pd.concat([existing, new])
    combined = combined[~combined.index.duplicated(keep='last')]
    combined = combined.sort_index()
    
    return combined

# ════════════════════════════════════════════════════════════════════════════════
# TQQQ 데이터 업데이트 (yfinance)
# ════════════════════════════════════════════════════════════════════════════════

def update_tqqq():
    """TQQQ 일봉 데이터 업데이트"""
    print("\n📈 Updating TQQQ daily data...")
    
    filepath = os.path.join(DATA_DIR, 'tqqq_daily.csv')
    existing = load_existing_csv(filepath)
    
    # 마지막 완료된 캔들 시간 (UTC)
    last_complete = get_last_completed_candle_time('1d')
    # 비교를 위해 Timezone 정보 제거 (Naive)
    last_complete = last_complete.replace(tzinfo=None)
    
    # 시작 날짜 결정
    if existing is not None and len(existing) > 0:
        last_date = existing.index.max()
        start_date = last_date + timedelta(days=1)
        
        if start_date.date() > last_complete.date():
            print(f"  ℹ️ Already up to date (last: {last_date.date()})")
            return
    else:
        # 새로 시작: 3년 전부터
        start_date = last_complete - timedelta(days=365*3)
    
    try:
        import yfinance as yf
        
        end_date = last_complete + timedelta(days=1)
        # auto_adjust=False 추가하여 경고 해결 및 데이터 일관성 확보
        data = yf.download('TQQQ', start=start_date, end=end_date, progress=False, auto_adjust=False)
        
        if data.empty:
            print("  ⚠️ No new data available")
            return
        
        # 컬럼 정리
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        
        data.columns = [c.lower() for c in data.columns]
        data.index = data.index.tz_localize(None)
        data.index.name = 'datetime'
        
        # 필요한 컬럼만
        data = data[['open', 'high', 'low', 'close', 'volume']]
        
        # 병합
        combined = merge_and_dedupe(existing, data)
        
        # 저장
        save_csv(combined, filepath, date_col='date')
        print(f"  📊 TQQQ: {len(data)} new rows added")
        
    except Exception as e:
        print(f"  ❌ Error updating TQQQ: {e}")

# ════════════════════════════════════════════════════════════════════════════════
# Bitget (Binance Futures) 데이터 업데이트
# ════════════════════════════════════════════════════════════════════════════════

def fetch_binance_futures(symbol: str, interval: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
    """Binance Futures API에서 데이터 가져오기"""
    url = "https://fapi.binance.com/fapi/v1/klines"
    
    all_data = []
    # Timezone 정보가 있다면 timestamp로 변환 시 고려됨
    current_start = int(start_time.replace(tzinfo=timezone.utc).timestamp() * 1000)
    end_ts = int(end_time.replace(tzinfo=timezone.utc).timestamp() * 1000)
    
    while current_start < end_ts:
        params = {
            'symbol': symbol,
            'interval': interval,
            'startTime': current_start,
            'endTime': end_ts,
            'limit': 1000
        }
        
        response = requests.get(url, params=params, timeout=15)
        if response.status_code != 200:
            break
        
        data = response.json()
        if not data:
            break
        
        all_data.extend(data)
        current_start = data[-1][0] + 1
        
        time.sleep(0.1)  # Rate limit
    
    if not all_data:
        return None
    
    df = pd.DataFrame(all_data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades', 'taker_buy_base',
        'taker_buy_quote', 'ignore'
    ])
    
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('datetime', inplace=True)
    df.index = df.index.tz_localize(None) # Naive로 변환
    
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = df[col].astype(float)
    
    return df[['open', 'high', 'low', 'close', 'volume']]


def update_bitget():
    """Bitget (Binance Futures) 4H 데이터 업데이트"""
    print("\n🔶 Updating Bitget (Binance Futures) 4H data...")
    
    last_complete = get_last_completed_candle_time('4h')
    # [수정] 비교 에러 방지를 위해 Timezone 제거 (Naive로 통일)
    last_complete = last_complete.replace(tzinfo=None)
    
    for symbol in BITGET_SYMBOLS:
        name = symbol.replace('USDT', '').lower()
        filepath = os.path.join(DATA_DIR, f'bitget_{name}_4h.csv')
        
        existing = load_existing_csv(filepath)
        
        # 시작 시간 결정
        if existing is not None and len(existing) > 0:
            last_date = existing.index.max()
            start_time = last_date + timedelta(hours=4)
            
            # 여기서 offset-naive vs offset-aware 에러가 발생했었음 -> 이제 둘 다 Naive라 해결됨
            if start_time > last_complete:
                print(f"  ℹ️ {symbol}: Already up to date")
                continue
        else:
            # 새로 시작: 3년 전부터
            start_time = last_complete - timedelta(days=365*3)
        
        try:
            new_data = fetch_binance_futures(symbol, '4h', start_time, last_complete + timedelta(hours=4))
            
            if new_data is None or len(new_data) == 0:
                print(f"  ⚠️ {symbol}: No new data")
                continue
            
            # 완료된 캔들만 필터링
            new_data = new_data[new_data.index <= last_complete]
            
            if len(new_data) == 0:
                print(f"  ℹ️ {symbol}: No completed candles yet")
                continue
            
            # 병합
            combined = merge_and_dedupe(existing, new_data)
            
            # 저장
            save_csv(combined, filepath)
            print(f"  📊 {symbol}: {len(new_data)} new rows added")
            
        except Exception as e:
            print(f"  ❌ Error updating {symbol}: {e}")
        
        time.sleep(0.2)

# ════════════════════════════════════════════════════════════════════════════════
# 업비트 데이터 업데이트
# ════════════════════════════════════════════════════════════════════════════════

def fetch_upbit_ohlcv(market: str, interval: str, count: int = 200, to: str = None) -> pd.DataFrame:
    """업비트 API에서 OHLCV 데이터 가져오기"""
    if interval == '4h':
        url = "https://api.upbit.com/v1/candles/minutes/240"
    elif interval == '1d':
        url = "https://api.upbit.com/v1/candles/days"
    else:
        return None
    
    params = {'market': market, 'count': count}
    if to:
        params['to'] = to
    
    headers = {"accept": "application/json"}
    response = requests.get(url, params=params, headers=headers, timeout=15)
    
    if response.status_code != 200:
        return None
    
    data = response.json()
    if not data:
        return None
    
    df = pd.DataFrame(data)
    
    # 컬럼 매핑
    df = df.rename(columns={
        'candle_date_time_kst': 'datetime',
        'opening_price': 'open',
        'high_price': 'high',
        'low_price': 'low',
        'trade_price': 'close',
        'candle_acc_trade_volume': 'volume'
    })
    
    df['datetime'] = pd.to_datetime(df['datetime'])
    df.set_index('datetime', inplace=True)
    df = df.sort_index()
    
    return df[['open', 'high', 'low', 'close', 'volume']]


def fetch_upbit_full(market: str, interval: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
    """업비트에서 전체 기간 데이터 가져오기 (페이징)"""
    all_data = []
    to_time = end_time.strftime('%Y-%m-%dT%H:%M:%S')
    
    max_iterations = 50  # 최대 50번 호출 (약 10000개 데이터)
    
    for _ in range(max_iterations):
        df = fetch_upbit_ohlcv(market, interval, count=200, to=to_time)
        
        if df is None or len(df) == 0:
            break
        
        # 시작 시간 이전 데이터 제외
        df = df[df.index >= start_time]
        
        if len(df) == 0:
            break
        
        all_data.append(df)
        
        # 다음 페이지
        oldest = df.index.min()
        if oldest <= start_time:
            break
        
        to_time = (oldest - timedelta(seconds=1)).strftime('%Y-%m-%dT%H:%M:%S')
        time.sleep(0.1)
    
    if not all_data:
        return None
    
    combined = pd.concat(all_data)
    combined = combined[~combined.index.duplicated(keep='first')]
    combined = combined.sort_index()
    
    return combined


def update_upbit():
    """업비트 4H/1D 데이터 업데이트"""
    print("\n🟠 Updating Upbit data...")
    
    last_complete_4h = get_last_completed_candle_time('4h')
    last_complete_1d = get_last_completed_candle_time('1d')
    
    # [수정] Timezone 제거 (Naive로 통일하여 계산)
    last_complete_4h = last_complete_4h.replace(tzinfo=None)
    last_complete_1d = last_complete_1d.replace(tzinfo=None)
    
    # 한국 시간으로 변환 (값만 +9시간, Naive 유지)
    kst_offset = timedelta(hours=9)
    last_complete_4h_kst = last_complete_4h + kst_offset
    last_complete_1d_kst = last_complete_1d + kst_offset
    
    for market in UPBIT_SYMBOLS:
        symbol = market.replace('KRW-', '').lower()
        
        # 4H 데이터
        filepath_4h = os.path.join(DATA_DIR, f'upbit_{symbol}_4h.csv')
        existing_4h = load_existing_csv(filepath_4h)
        
        if existing_4h is not None and len(existing_4h) > 0:
            last_date = existing_4h.index.max()
            start_time = last_date + timedelta(hours=4)
        else:
            start_time = last_complete_4h_kst - timedelta(days=365*3)
        
        if start_time <= last_complete_4h_kst:
            try:
                new_data = fetch_upbit_full(market, '4h', start_time, last_complete_4h_kst + timedelta(hours=4))
                
                if new_data is not None and len(new_data) > 0:
                    # 완료된 캔들만
                    new_data = new_data[new_data.index <= last_complete_4h_kst]
                    
                    if len(new_data) > 0:
                        combined = merge_and_dedupe(existing_4h, new_data)
                        save_csv(combined, filepath_4h)
                        print(f"  📊 {market} 4H: {len(new_data)} new rows")
            except Exception as e:
                print(f"  ❌ Error {market} 4H: {e}")
        
        # 1D 데이터
        filepath_1d = os.path.join(DATA_DIR, f'upbit_{symbol}_1d.csv')
        existing_1d = load_existing_csv(filepath_1d)
        
        if existing_1d is not None and len(existing_1d) > 0:
            last_date = existing_1d.index.max()
            start_time = last_date + timedelta(days=1)
        else:
            start_time = last_complete_1d_kst - timedelta(days=365*3)
        
        if start_time <= last_complete_1d_kst:
            try:
                new_data = fetch_upbit_full(market, '1d', start_time, last_complete_1d_kst + timedelta(days=1))
                
                if new_data is not None and len(new_data) > 0:
                    # 완료된 캔들만
                    new_data = new_data[new_data.index <= last_complete_1d_kst]
                    
                    if len(new_data) > 0:
                        combined = merge_and_dedupe(existing_1d, new_data)
                        save_csv(combined, filepath_1d)
                        print(f"  📊 {market} 1D: {len(new_data)} new rows")
            except Exception as e:
                print(f"  ❌ Error {market} 1D: {e}")
        
        time.sleep(0.2)

# ════════════════════════════════════════════════════════════════════════════════
# 메인
# ════════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("📊 Trading Data Auto-Update")
    print(f"⏰ Current time (UTC): {datetime.now(timezone.utc)}")
    print("=" * 60)
    
    # 데이터 폴더 생성
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # 현재 시간 기준으로 어떤 데이터를 업데이트할지 결정
    now = datetime.now(timezone.utc)
    hour = now.hour
    
    # TQQQ: UTC 21시 (한국시간 화~토 06시) 전후에 실행
    if 20 <= hour <= 22 or hour <= 1:
        update_tqqq()
    
    # 4H 데이터: 항상 실행 (스케줄에서 시간 관리)
    update_bitget()
    update_upbit()
    
    print("\n" + "=" * 60)
    print("✅ Update completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
