"""
================================================================================
📊 트레이딩 전략 포트폴리오 대시보드 v4.0
================================================================================
- CSV 파일 기반 백테스트
- GitHub Actions 자동 업데이트 지원
- 데이터 상태 모니터링
- 유연한 기간 선택
================================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import warnings
warnings.filterwarnings('ignore')

# ════════════════════════════════════════════════════════════════════════════════
# 📌 페이지 설정
# ════════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="트레이딩 포트폴리오 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ════════════════════════════════════════════════════════════════════════════════
# 📌 전략 설정
# ════════════════════════════════════════════════════════════════════════════════

TQQQ_CONFIG = {
    'stoch_period': 166,
    'stoch_k': 57,
    'stoch_d': 19,
    'ma_periods': [20, 45, 151, 212]
}

BITGET_CONFIG = {
    'BTCUSDT': {'ma_period': 248, 'stoch': (46, 37, 4), 'leverage_up': 4},
    'ETHUSDT': {'ma_period': 152, 'stoch': (58, 23, 18), 'leverage_up': 4},
    'SOLUSDT': {'ma_period': 64, 'stoch': (51, 20, 16), 'leverage_up': 2},
}

UPBIT_CONFIG = {
    'KRW-ADA': {'ma': 83, 'stoch': (60, 25, 5)},
    'KRW-ANKR': {'ma': 253, 'stoch': (70, 25, 5)},
    'KRW-AVAX': {'ma': 99, 'stoch': (120, 20, 5)},
    'KRW-AXS': {'ma': 276, 'stoch': (50, 20, 5)},
    'KRW-BCH': {'ma': 99, 'stoch': (50, 30, 5)},
    'KRW-BTC': {'ma': 276, 'stoch': (80, 25, 5)},
    'KRW-CRO': {'ma': 253, 'stoch': (120, 45, 5)},
    'KRW-DOGE': {'ma': 213, 'stoch': (50, 30, 5)},
    'KRW-ETH': {'ma': 201, 'stoch': (60, 20, 5)},
    'KRW-HBAR': {'ma': 180, 'stoch': (50, 35, 5)},
    'KRW-IMX': {'ma': 137, 'stoch': (50, 20, 5)},
    'KRW-MANA': {'ma': 190, 'stoch': (150, 35, 5)},
    'KRW-MVL': {'ma': 163, 'stoch': (50, 50, 5)},
    'KRW-SAND': {'ma': 52, 'stoch': (60, 20, 5)},
    'KRW-SOL': {'ma': 254, 'stoch': (50, 30, 5)},
    'KRW-THETA': {'ma': 145, 'stoch': (120, 30, 5)},
    'KRW-VET': {'ma': 172, 'stoch': (50, 30, 5)},
    'KRW-WAXP': {'ma': 271, 'stoch': (50, 30, 5)},
    'KRW-XLM': {'ma': 115, 'stoch': (50, 25, 5)},
    'KRW-XRP': {'ma': 64, 'stoch': (70, 20, 5)},
}

# ════════════════════════════════════════════════════════════════════════════════
# 📌 데이터 로드 함수
# ════════════════════════════════════════════════════════════════════════════════

def get_data_path():
    """데이터 폴더 경로"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, 'data')


@st.cache_data(ttl=300, show_spinner=False)
def load_csv_data(filename: str) -> pd.DataFrame:
    """CSV 파일 로드"""
    try:
        filepath = os.path.join(get_data_path(), filename)
        if not os.path.exists(filepath):
            return None
        
        df = pd.read_csv(filepath)
        
        if 'date' in df.columns:
            df['datetime'] = pd.to_datetime(df['date'])
        elif 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
        
        df.set_index('datetime', inplace=True)
        df.index = df.index.tz_localize(None)
        df.columns = [c.lower() for c in df.columns]
        
        return df
    except Exception as e:
        return None


def get_data_status(filename: str) -> dict:
    """데이터 파일 상태 확인"""
    filepath = os.path.join(get_data_path(), filename)
    
    if not os.path.exists(filepath):
        return {'exists': False, 'filename': filename}
    
    try:
        df = load_csv_data(filename)
        if df is None or len(df) == 0:
            return {'exists': False, 'filename': filename}
        
        return {
            'exists': True,
            'filename': filename,
            'rows': len(df),
            'start': df.index.min().strftime('%Y-%m-%d'),
            'end': df.index.max().strftime('%Y-%m-%d %H:%M'),
            'last_update': df.index.max()
        }
    except:
        return {'exists': False, 'filename': filename}

# ════════════════════════════════════════════════════════════════════════════════
# 📌 지표 계산 함수
# ════════════════════════════════════════════════════════════════════════════════

def calculate_stochastic(df: pd.DataFrame, period: int, k_smooth: int, d_period: int) -> pd.DataFrame:
    """스토캐스틱 계산"""
    df = df.copy()
    df['hh'] = df['high'].rolling(window=period, min_periods=period).max()
    df['ll'] = df['low'].rolling(window=period, min_periods=period).min()
    
    denom = df['hh'] - df['ll']
    denom = denom.replace(0, np.nan)
    
    df['k_raw'] = (df['close'] - df['ll']) / denom * 100
    df['stoch_k'] = df['k_raw'].rolling(window=k_smooth, min_periods=k_smooth).mean()
    df['stoch_d'] = df['stoch_k'].rolling(window=d_period, min_periods=d_period).mean()
    
    return df


def calculate_ma(series: pd.Series, period: int) -> pd.Series:
    """이동평균선 계산"""
    return series.rolling(window=period, min_periods=period).mean()

# ════════════════════════════════════════════════════════════════════════════════
# 📌 백테스트 함수
# ════════════════════════════════════════════════════════════════════════════════

def backtest_tqqq_strategy(data: pd.DataFrame) -> pd.DataFrame:
    """TQQQ 전략 백테스트"""
    if data is None or len(data) < 220:
        return None
    
    df = data.copy()
    df = calculate_stochastic(df, TQQQ_CONFIG['stoch_period'], TQQQ_CONFIG['stoch_k'], TQQQ_CONFIG['stoch_d'])
    
    for ma in TQQQ_CONFIG['ma_periods']:
        df[f'ma{ma}'] = calculate_ma(df['close'], ma)
    
    df = df.dropna()
    if len(df) < 50:
        return None
    
    positions = []
    for i in range(len(df)):
        row = df.iloc[i]
        is_bullish = row['stoch_k'] > row['stoch_d']
        ma_signals = {p: row['close'] > row[f'ma{p}'] for p in TQQQ_CONFIG['ma_periods']}
        
        if is_bullish:
            tqqq_ratio = sum(ma_signals.values()) * 0.25
        else:
            tqqq_ratio = (int(ma_signals[20]) + int(ma_signals[45])) * 0.5
        
        positions.append(tqqq_ratio)
    
    df['position'] = positions
    df['daily_return'] = df['close'].pct_change()
    df['strategy_return'] = df['position'].shift(1) * df['daily_return']
    df['strategy_return'] = df['strategy_return'].fillna(0)
    df['cumulative_return'] = (1 + df['strategy_return']).cumprod()
    
    return df


def backtest_bitget_strategy(btc_data, eth_data, sol_data) -> pd.DataFrame:
    """Bitget 선물 전략 백테스트"""
    results = {}
    data_dict = {'BTCUSDT': btc_data, 'ETHUSDT': eth_data, 'SOLUSDT': sol_data}
    
    for symbol, config in BITGET_CONFIG.items():
        data = data_dict.get(symbol)
        if data is None or len(data) < config['ma_period'] + 50:
            continue
        
        df = data.copy()
        df['ma'] = calculate_ma(df['close'], config['ma_period'])
        k_period, k_smooth, d_period = config['stoch']
        df = calculate_stochastic(df, k_period, k_smooth, d_period)
        df = df.dropna()
        
        if len(df) < 50:
            continue
        
        df['signal'] = (df['open'] > df['ma']) & (df['stoch_k'] > df['stoch_d'])
        df['position'] = df['signal'].astype(float) * config['leverage_up']
        df['return'] = df['close'].pct_change()
        df['strategy_return'] = df['position'].shift(1) * df['return']
        df['strategy_return'] = df['strategy_return'].clip(lower=-0.99).fillna(0)
        
        results[symbol.replace('USDT', '')] = df['strategy_return']
    
    if not results:
        return None
    
    combined = pd.DataFrame(results).fillna(0)
    combined['portfolio_return'] = combined.mean(axis=1)
    combined['cumulative_return'] = (1 + combined['portfolio_return']).cumprod()
    
    return combined


def backtest_upbit_strategy(data_4h_dict: dict, data_1d_dict: dict) -> pd.DataFrame:
    """업비트 현물 전략 백테스트"""
    results = {}
    
    for ticker, config in UPBIT_CONFIG.items():
        symbol = ticker.replace('KRW-', '').lower()
        data_4h = data_4h_dict.get(symbol)
        data_1d = data_1d_dict.get(symbol)
        
        if data_4h is None or data_1d is None or len(data_4h) < config['ma'] + 10:
            continue
        
        df_4h = data_4h.copy()
        df_4h['ma'] = calculate_ma(df_4h['close'], config['ma'])
        
        df_1d = data_1d.copy()
        k_period, k_smooth, d_period = config['stoch']
        df_1d = calculate_stochastic(df_1d, k_period, k_smooth, d_period)
        
        df_4h['date'] = df_4h.index.date
        df_1d['date'] = df_1d.index.date
        
        stoch_daily = df_1d[['date', 'stoch_k', 'stoch_d']].drop_duplicates(subset='date', keep='last').set_index('date')
        df_4h['stoch_k'] = df_4h['date'].map(stoch_daily['stoch_k'])
        df_4h['stoch_d'] = df_4h['date'].map(stoch_daily['stoch_d'])
        df_4h = df_4h.dropna()
        
        if len(df_4h) < 50:
            continue
        
        df_4h['signal'] = (df_4h['open'] > df_4h['ma']) & (df_4h['stoch_k'] > df_4h['stoch_d'])
        df_4h['position'] = df_4h['signal'].astype(float)
        df_4h['return'] = df_4h['close'].pct_change()
        df_4h['strategy_return'] = df_4h['position'].shift(1) * df_4h['return']
        df_4h['strategy_return'] = df_4h['strategy_return'].fillna(0)
        
        results[symbol.upper()] = df_4h['strategy_return']
    
    if not results:
        return None
    
    combined = pd.DataFrame(results).fillna(0)
    combined['portfolio_return'] = combined.mean(axis=1)
    combined['cumulative_return'] = (1 + combined['portfolio_return']).cumprod()
    
    return combined

# ════════════════════════════════════════════════════════════════════════════════
# 📌 성과 지표 계산
# ════════════════════════════════════════════════════════════════════════════════

def calculate_metrics(returns: pd.Series, periods_per_year: int = 252) -> dict:
    """성과 지표 계산"""
    returns = returns.dropna()
    if len(returns) < 10:
        return {'total_return': 0, 'cagr': 0, 'volatility': 0, 'sharpe': 0, 'max_drawdown': 0, 'win_rate': 0}
    
    cumulative = (1 + returns).cumprod()
    total_return = cumulative.iloc[-1] - 1
    years = max(len(returns) / periods_per_year, 0.1)
    cagr = (cumulative.iloc[-1]) ** (1/years) - 1 if cumulative.iloc[-1] > 0 else 0
    volatility = returns.std() * np.sqrt(periods_per_year)
    sharpe = (cagr / volatility) if volatility > 0 else 0
    peak = cumulative.expanding().max()
    max_drawdown = ((cumulative - peak) / peak).min()
    win_rate = (returns > 0).mean()
    
    return {
        'total_return': total_return * 100,
        'cagr': cagr * 100,
        'volatility': volatility * 100,
        'sharpe': sharpe,
        'max_drawdown': max_drawdown * 100,
        'win_rate': win_rate * 100
    }

# ════════════════════════════════════════════════════════════════════════════════
# 📌 메인 UI
# ════════════════════════════════════════════════════════════════════════════════

def main():
    st.title("📊 트레이딩 전략 포트폴리오 대시보드")
    st.markdown("**CSV 데이터 기반 백테스트 + GitHub Actions 자동 업데이트**")
    
    # ════════════════════════════════════════════════════════════════════════════
    # 사이드바
    # ════════════════════════════════════════════════════════════════════════════
    
    st.sidebar.header("⚙️ 설정")
    
    # 기간 선택 (개선됨)
    period_option = st.sidebar.selectbox(
        "📅 분석 기간",
        ["최근 1개월", "최근 6개월", "최근 1년", "YTD (연초부터)", "전체 기간", "📆 기간 직접 설정"]
    )
    
    today = datetime.now().date()
    
    if period_option == "최근 1개월":
        start_date = today - timedelta(days=30)
        end_date = today
    elif period_option == "최근 6개월":
        start_date = today - timedelta(days=180)
        end_date = today
    elif period_option == "최근 1년":
        start_date = today - timedelta(days=365)
        end_date = today
    elif period_option == "YTD (연초부터)":
        start_date = datetime(today.year, 1, 1).date()
        end_date = today
    elif period_option == "전체 기간":
        start_date = today - timedelta(days=365*10)
        end_date = today
    else:  # 기간 직접 설정
        st.sidebar.markdown("##### 📆 기간 직접 설정")
        col1, col2 = st.sidebar.columns(2)
        start_date = col1.date_input("시작일", today - timedelta(days=365), key="start")
        end_date = col2.date_input("종료일", today, key="end")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("💰 포트폴리오 배분")
    col1, col2, col3 = st.sidebar.columns(3)
    tqqq_weight = col1.number_input("TQQQ", 0, 100, 33)
    bitget_weight = col2.number_input("Bitget", 0, 100, 33)
    upbit_weight = col3.number_input("업비트", 0, 100, 34)
    
    # ════════════════════════════════════════════════════════════════════════════
    # 데이터 로딩
    # ════════════════════════════════════════════════════════════════════════════
    
    data_path = get_data_path()
    
    if not os.path.exists(data_path):
        st.error(f"❌ data 폴더를 찾을 수 없습니다.")
        st.info("📁 GitHub Actions가 자동으로 데이터를 생성합니다. 잠시 기다려주세요.")
        return
    
    # 데이터 로드
    with st.spinner("📡 데이터 로딩 중..."):
        tqqq_data = load_csv_data('tqqq_daily.csv')
        btc_4h = load_csv_data('bitget_btc_4h.csv')
        eth_4h = load_csv_data('bitget_eth_4h.csv')
        sol_4h = load_csv_data('bitget_sol_4h.csv')
        
        upbit_4h_data = {}
        upbit_1d_data = {}
        for ticker in UPBIT_CONFIG.keys():
            symbol = ticker.replace('KRW-', '').lower()
            upbit_4h_data[symbol] = load_csv_data(f'upbit_{symbol}_4h.csv')
            upbit_1d_data[symbol] = load_csv_data(f'upbit_{symbol}_1d.csv')
    
    # ════════════════════════════════════════════════════════════════════════════
    # 📊 데이터 상태 표시
    # ════════════════════════════════════════════════════════════════════════════
    
    with st.sidebar.expander("📁 데이터 상태 확인", expanded=False):
        # TQQQ
        status = get_data_status('tqqq_daily.csv')
        if status['exists']:
            st.success(f"**TQQQ**: {status['rows']:,}행")
            st.caption(f"{status['start']} ~ {status['end']}")
        else:
            st.error("**TQQQ**: 없음")
        
        st.markdown("---")
        
        # Bitget
        st.markdown("**Bitget (4H)**")
        for symbol in ['btc', 'eth', 'sol']:
            status = get_data_status(f'bitget_{symbol}_4h.csv')
            if status['exists']:
                st.write(f"✅ {symbol.upper()}: {status['rows']:,}행")
            else:
                st.write(f"❌ {symbol.upper()}: 없음")
        
        st.markdown("---")
        
        # 업비트
        st.markdown("**업비트**")
        upbit_4h_count = sum(1 for s in UPBIT_CONFIG.keys() 
                            if get_data_status(f'upbit_{s.replace("KRW-", "").lower()}_4h.csv')['exists'])
        upbit_1d_count = sum(1 for s in UPBIT_CONFIG.keys() 
                            if get_data_status(f'upbit_{s.replace("KRW-", "").lower()}_1d.csv')['exists'])
        
        st.write(f"4H 데이터: {upbit_4h_count}/{len(UPBIT_CONFIG)} 코인")
        st.write(f"1D 데이터: {upbit_1d_count}/{len(UPBIT_CONFIG)} 코인")
        
        # 누락된 코인 표시
        missing_coins = []
        for ticker in UPBIT_CONFIG.keys():
            symbol = ticker.replace('KRW-', '').lower()
            if not get_data_status(f'upbit_{symbol}_4h.csv')['exists']:
                missing_coins.append(symbol.upper())
        
        if missing_coins:
            st.warning(f"누락: {', '.join(missing_coins[:5])}{'...' if len(missing_coins) > 5 else ''}")
    
    # ════════════════════════════════════════════════════════════════════════════
    # 백테스트 실행
    # ════════════════════════════════════════════════════════════════════════════
    
    with st.spinner("📈 전략 백테스트 중..."):
        tqqq_result = backtest_tqqq_strategy(tqqq_data)
        bitget_result = backtest_bitget_strategy(btc_4h, eth_4h, sol_4h)
        upbit_result = backtest_upbit_strategy(upbit_4h_data, upbit_1d_data)
    
    # 기간 필터링
    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date)
    
    def filter_and_rebase(df, return_col):
        if df is None or len(df) == 0:
            return None
        filtered = df[start_ts:end_ts].copy()
        if len(filtered) > 0:
            filtered['cumulative_return'] = (1 + filtered[return_col]).cumprod()
        return filtered
    
    tqqq_filtered = filter_and_rebase(tqqq_result, 'strategy_return')
    bitget_filtered = filter_and_rebase(bitget_result, 'portfolio_return')
    upbit_filtered = filter_and_rebase(upbit_result, 'portfolio_return')
    
    # ════════════════════════════════════════════════════════════════════════════
    # 📈 성과 요약
    # ════════════════════════════════════════════════════════════════════════════
    
    st.markdown("---")
    st.subheader("📈 전략별 성과 요약")
    st.caption(f"분석 기간: {start_date} ~ {end_date}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🇺🇸 TQQQ Sniper")
        if tqqq_filtered is not None and len(tqqq_filtered) > 0:
            metrics = calculate_metrics(tqqq_filtered['strategy_return'], 252)
            st.metric("누적 수익률", f"{metrics['total_return']:.1f}%")
            st.metric("CAGR", f"{metrics['cagr']:.1f}%")
            st.metric("최대 낙폭", f"{metrics['max_drawdown']:.1f}%")
            st.metric("샤프 비율", f"{metrics['sharpe']:.2f}")
        else:
            st.warning("데이터 없음")
    
    with col2:
        st.markdown("### 🔶 Bitget 선물")
        if bitget_filtered is not None and len(bitget_filtered) > 0:
            metrics = calculate_metrics(bitget_filtered['portfolio_return'], 252*6)
            st.metric("누적 수익률", f"{metrics['total_return']:.1f}%")
            st.metric("CAGR", f"{metrics['cagr']:.1f}%")
            st.metric("최대 낙폭", f"{metrics['max_drawdown']:.1f}%")
            st.metric("샤프 비율", f"{metrics['sharpe']:.2f}")
        else:
            st.warning("데이터 없음")
    
    with col3:
        st.markdown("### 🟠 업비트 현물")
        if upbit_filtered is not None and len(upbit_filtered) > 0:
            metrics = calculate_metrics(upbit_filtered['portfolio_return'], 252*6)
            st.metric("누적 수익률", f"{metrics['total_return']:.1f}%")
            st.metric("CAGR", f"{metrics['cagr']:.1f}%")
            st.metric("최대 낙폭", f"{metrics['max_drawdown']:.1f}%")
            st.metric("샤프 비율", f"{metrics['sharpe']:.2f}")
        else:
            st.warning("데이터 없음")
    
    # ════════════════════════════════════════════════════════════════════════════
    # 📊 누적 수익률 차트
    # ════════════════════════════════════════════════════════════════════════════
    
    st.markdown("---")
    st.subheader("📊 누적 수익률 비교")
    
    fig = go.Figure()
    
    if tqqq_filtered is not None and len(tqqq_filtered) > 0:
        fig.add_trace(go.Scatter(
            x=tqqq_filtered.index,
            y=(tqqq_filtered['cumulative_return'] - 1) * 100,
            name='TQQQ Sniper',
            line=dict(color='#2962FF', width=2)
        ))
    
    if bitget_filtered is not None and len(bitget_filtered) > 0:
        fig.add_trace(go.Scatter(
            x=bitget_filtered.index,
            y=(bitget_filtered['cumulative_return'] - 1) * 100,
            name='Bitget 선물',
            line=dict(color='#FF6D00', width=2)
        ))
    
    if upbit_filtered is not None and len(upbit_filtered) > 0:
        fig.add_trace(go.Scatter(
            x=upbit_filtered.index,
            y=(upbit_filtered['cumulative_return'] - 1) * 100,
            name='업비트 현물',
            line=dict(color='#00C853', width=2)
        ))
    
    fig.update_layout(
        title=f'전략별 누적 수익률 (%) - {start_date} ~ {end_date}',
        xaxis_title='날짜',
        yaxis_title='수익률 (%)',
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500,
        template='plotly_white'
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ════════════════════════════════════════════════════════════════════════════
    # 📋 전략별 상세
    # ════════════════════════════════════════════════════════════════════════════
    
    st.markdown("---")
    st.subheader("📋 전략별 상세 정보")
    
    tab1, tab2, tab3 = st.tabs(["🇺🇸 TQQQ Sniper", "🔶 Bitget 선물", "🟠 업비트 현물"])
    
    with tab1:
        st.markdown("""
        **전략 설명**: Stochastic(166,57,19) + MA(20,45,151,212)
        - Bullish (K>D): 4개 MA 각 25% 배분
        - Bearish (K<D): MA20+MA45 각 50% 배분
        """)
        
        if tqqq_filtered is not None and len(tqqq_filtered) > 0:
            current_pos = tqqq_filtered['position'].iloc[-1]
            st.metric("현재 TQQQ 비중", f"{current_pos*100:.0f}%")
            
            fig_pos = go.Figure()
            fig_pos.add_trace(go.Scatter(
                x=tqqq_filtered.index,
                y=tqqq_filtered['position'] * 100,
                fill='tozeroy',
                line=dict(color='#2962FF')
            ))
            fig_pos.update_layout(title='포지션 비중 변화', yaxis_title='비중 (%)', height=300, template='plotly_white')
            st.plotly_chart(fig_pos, use_container_width=True)
    
    with tab2:
        st.markdown("""
        **전략**: BTC(MA248), ETH(MA152), SOL(MA64) + 각 스토캐스틱
        - 진입: 시가 > MA AND K > D → 레버리지 진입
        """)
        
        if bitget_filtered is not None and len(bitget_filtered) > 0:
            cols = st.columns(3)
            for idx, name in enumerate(['BTC', 'ETH', 'SOL']):
                with cols[idx]:
                    if name in bitget_filtered.columns:
                        ret = (1 + bitget_filtered[name]).cumprod().iloc[-1] - 1
                        st.metric(f"{name}", f"{ret*100:.1f}%")
    
    with tab3:
        st.markdown(f"**전략**: {len(UPBIT_CONFIG)}개 알트코인, MA(4H) + Stoch(1D)")
        
        if upbit_filtered is not None and len(upbit_filtered) > 0:
            coin_returns = {}
            for col in upbit_filtered.columns:
                if col not in ['portfolio_return', 'cumulative_return']:
                    ret = (1 + upbit_filtered[col]).cumprod().iloc[-1] - 1
                    coin_returns[col] = ret * 100
            
            if coin_returns:
                df_coins = pd.DataFrame.from_dict(coin_returns, orient='index', columns=['수익률'])
                df_coins = df_coins.sort_values('수익률', ascending=False)
                
                fig_bar = go.Figure(go.Bar(
                    x=df_coins.index,
                    y=df_coins['수익률'],
                    marker_color=['#00C853' if v >= 0 else '#FF1744' for v in df_coins['수익률']]
                ))
                fig_bar.update_layout(title='코인별 수익률', yaxis_title='수익률 (%)', height=400, template='plotly_white')
                st.plotly_chart(fig_bar, use_container_width=True)
    
    # ════════════════════════════════════════════════════════════════════════════
    # 📅 월별 히트맵
    # ════════════════════════════════════════════════════════════════════════════
    
    st.markdown("---")
    st.subheader("📅 월별 수익률 히트맵")
    
    strategy_choice = st.selectbox("전략 선택", ["TQQQ Sniper", "Bitget 선물", "업비트 현물"])
    
    monthly = None
    if strategy_choice == "TQQQ Sniper" and tqqq_filtered is not None:
        monthly = tqqq_filtered['strategy_return'].resample('M').sum() * 100
    elif strategy_choice == "Bitget 선물" and bitget_filtered is not None:
        monthly = bitget_filtered['portfolio_return'].resample('M').sum() * 100
    elif strategy_choice == "업비트 현물" and upbit_filtered is not None:
        monthly = upbit_filtered['portfolio_return'].resample('M').sum() * 100
    
    if monthly is not None and len(monthly) > 0:
        monthly_df = pd.DataFrame({
            'Year': monthly.index.year,
            'Month': monthly.index.month,
            'Return': monthly.values
        })
        pivot = monthly_df.pivot(index='Year', columns='Month', values='Return')
        month_labels = ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월']
        
        fig_heatmap = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=[month_labels[i-1] for i in pivot.columns],
            y=pivot.index,
            colorscale='RdYlGn',
            zmid=0,
            text=[[f'{v:.1f}%' if not pd.isna(v) else '' for v in row] for row in pivot.values],
            texttemplate="%{text}",
            textfont={"size": 10}
        ))
        fig_heatmap.update_layout(title=f'{strategy_choice} 월별 수익률', height=350, template='plotly_white')
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # 푸터
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray; font-size: 12px;'>
    📊 트레이딩 포트폴리오 대시보드 v4.0 | GitHub Actions 자동 업데이트<br>
    ⚠️ 교육 목적으로만 사용. 투자 조언이 아닙니다.
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
