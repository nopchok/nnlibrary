name = 'nnlibrary'

class Indicators:
    @staticmethod
    def addAllTechnicalIndicators(df):
        
        df = df.copy()
        
        assert all([a == b for a, b in zip(df.columns, ['open', 'high', 'low', 'close', 'volume'])]), "Columns must be open, high, low, close, volume"
        
        df = ta.add_all_ta_features(df, open="open", high="high", low="low", close="close", volume="volume")
        
        df['ao'] = pandas_ta.ao(df['high'], df['low'], fast=5, slow=34)
        df['apo'] = pandas_ta.apo(df['close'], fast=12, slow=26)
        df['bop'] = pandas_ta.bop(df['open'], df['high'], df['low'], df['close'])
        df['cg'] = pandas_ta.cg(df['close'], length=10)
        df['fwma'] = pandas_ta.fwma(df['close'], length=10)
        df['kurtosis'] = pandas_ta.kurtosis(df['close'], length=30)
        
        return df

class Tools:
    @staticmethod
    def timeframe_resampler_candle(self, dt):
        if len(dt)!=0:
            if dt.name=='open': return dt.values[0]
            elif dt.name=='high': return dt.max()
            elif dt.name=='low': return dt.min()
            elif dt.name=='close': return dt.values[-1]
            elif dt.name=='volume': return dt.sum()
        else:
            return np.nan

    @staticmethod
    def timeframe_resampler(df, timeframe='1D'):
        #Columns Check
        assert 'time' in df.columns, '\'time\' column is required.'
        assert 'open' in df.columns, '\'open\' column is required.'
        assert 'high' in df.columns, '\'high\' column is required.'
        assert 'low' in df.columns, '\'low\' column is required.'
        assert 'close' in df.columns, '\'close\' column is required.'
        #Processing
        dfp = df.copy()
        dfp['time'] = pd.to_datetime(dfp.time)
        dfp.set_index('time', inplace=True)
        dfr = dfp.resample(timeframe).apply(self.timeframe_resampler_candle).dropna()
        dfr['time'] = dfr.index
        dfr = dfr[df.columns]
        dfr.reset_index(drop=True, inplace=True)

        return dfr
        
class Backtest:
    @staticmethod
    def trade_simulation(df,digit=1,pip_profit=1,commission=0):
    
        assert 'signal' in df.columns, 'Signal column is required.'

        df['value_grp'] = (df.signal != df.signal.shift(1)).astype('int').cumsum()
        df['open_time'] = df.time
        df['close_time'] =  df.time.shift(-1)
        df['open_price'] = df.close
        df['close_price'] = df.close.shift(-1)
        #Remove last signal.
        df = df[df['value_grp']!=df.iloc[-1].value_grp]
        
        #Create trading result
        df_trade = pd.DataFrame({
            'type' : df.groupby('value_grp').signal.first(),
            'open_time':df.groupby('value_grp').open_time.first(),
            'open_price' : df.groupby('value_grp').close.first(),
            'close_time' : df.groupby('value_grp').close_time.last(),
            'close_price' : df.groupby('value_grp').close_price.last(),
            'length' : df.groupby('value_grp').size(),
        })
        df_trade['pnl'] = (df_trade.close_price-df_trade.open_price)*df_trade.type*10**digit*pip_profit-commission
        df_trade = df_trade[df_trade.type!=0]
        df_trade['equity'] = df_trade.pnl.cumsum()
        
        df_trade.reset_index(drop=True, inplace=True)
        
        return df_trade
    
    @staticmethod
    def stock_trade_simulation(df, shares=1, commission=0.5, vat=7.0):

        assert 'time' in df.columns, '\'time\' column is required.'
        assert 'open' in df.columns, '\'open\' column is required.'
        assert 'high' in df.columns, '\'high\' column is required.'
        assert 'low' in df.columns, '\'low\' column is required.'
        assert 'close' in df.columns, '\'close\' column is required.'
        assert 'signal' in df.columns, '\'signal\' column is required.'

        df = df.copy()
        
        df['value_grp'] = (df.signal != df.signal.shift(1)).astype('int').cumsum()
        df['open_time'] = df.time
        df['close_time'] =  df.time.shift(-1)
        df['open_price'] = df.close
        df['close_price'] = df.close.shift(-1)
        #Remove last signal.
        df = df[df['value_grp']!=df.iloc[-1].value_grp]

        #Create trading result
        df_trade = pd.DataFrame({
            'type' : df.groupby('value_grp').signal.first(),
            'open_time':df.groupby('value_grp').open_time.first(),
            'open_price' : df.groupby('value_grp').close.first(),
            'close_time' : df.groupby('value_grp').close_time.last(),
            'close_price' : df.groupby('value_grp').close_price.last(),
            'length' : df.groupby('value_grp').size(),
        })
        df_trade['shares'] = shares
        df_trade['profit'] = (df_trade.close_price - df_trade.open_price) * shares
        df_trade['commission'] = round((df_trade.open_price * shares * (commission / 100)) * (vat / 100), 2)
        df_trade['pnl'] = df_trade.profit - df_trade.commission
        df_trade = df_trade[df_trade.type==1]
        df_trade['equity'] = df_trade.pnl.cumsum()

        df_trade.reset_index(drop=True, inplace=True)

        return df_trade
        
class AsianPnL:
    """
    Supported mode: home, away, over, under
    Single Asian logic
    """

    # ---------- Core Logic ----------
    @staticmethod
    def __asian_result__(value, line, odd):
        base = value - line

        win = odd - 1
        win2 = win / 2

        if base > 0.25:
            return win
        elif base == 0.25:
            return win2
        elif base == -0.25:
            return -0.5
        elif base < -0.25:
            return -1
        
        return 0

    # ---------- Row Level ----------
    @staticmethod
    def __calc_row_pnl__(row, signal='home'):
        ghf, gaf = row['ghf'], row['gaf']
        totalf = ghf + gaf

        gh, ga = row['gh'], row['ga']

        if signal == 'over':
            v, l, o = totalf, row['goalline'], row['oddo']

        elif signal == 'under':
            v, l, o = -totalf, -row['goalline'], row['oddu']

        elif signal == 'home':
            v, l, o = (ghf - gh) - (gaf - ga), -row['handicap'], row['oddh']

        else:  # away
            v, l, o = (gaf - ga) - (ghf - gh), row['handicap'], row['odda']

        return AsianPnL.__asian_result__(v, l, o)


    # ---------- DataFrame API ----------
    @staticmethod
    def calc_pnl(df, signal='home'):
        assert signal in ['home', 'away', 'over', 'under'], 'Signal must be home, away, over, under'
        
        required = ['ghf', 'gaf', 'gh', 'ga', 'handicap', 'oddh', 'odda', 'goalline', 'oddo', 'oddu']
        # check column
        assert all(col in df.columns for col in required), f"DF must contain columns {required}"

        out = df.copy()
        out['pnl'] = out.apply(lambda r: AsianPnL.__calc_row_pnl__(r, signal), axis=1)
        out['cum_pnl'] = out['pnl'].cumsum()
        return out
        
