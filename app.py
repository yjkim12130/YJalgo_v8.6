"""
YJ-Quant Dashboard v8.7c — 드레인 A/B 비교 (Beta + Alpha 모두)
═══════════════════════════════════════════════════════
Tab5: 8종 비교
  0.ETF Only | 1a.ETF+CMA(기존) | 1b.ETF+CMA(v2)
  2.TopN Only | 3.TopN+CMA
  4a.ETF→TopN(기존) | 4b.ETF→TopN(v2)
"""
import itertools, time
from datetime import date, timedelta
import numpy as np, pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="YJ-Quant", page_icon="📈", layout="wide", initial_sidebar_state="expanded")
TRADING_DAYS=252; LEV_COST=0.045; CMA_INTEREST=0.035
TODAY=date.today().isoformat(); CUR_YEAR=date.today().year; _D="plotly_dark"

ASSET_CLASSES={
    "S&P 500":{"sym":"^GSPC","vix":"^VIX","vf":15,"cur":"$","col":"#00d084"},
    "Nasdaq":{"sym":"^IXIC","vix":"^VXN","vf":20,"cur":"$","col":"#2196f3"},
    "금(Gold)":{"sym":"GC=F","vix":None,"vf":15,"cur":"$","col":"#ffd700"},
    "KOSPI":{"sym":"^KS11","vix":None,"vf":20,"cur":"₩","col":"#ff6b6b"},
    "Nikkei225":{"sym":"^N225","vix":None,"vf":20,"cur":"¥","col":"#ab47bc"},
    "Bitcoin":{"sym":"BTC-USD","vix":None,"vf":40,"cur":"$","col":"#ff9800"},
    "DAX":{"sym":"^GDAXI","vix":None,"vf":18,"cur":"€","col":"#00bcd4"},
    "상해종합":{"sym":"000001.SS","vix":None,"vf":20,"cur":"¥","col":"#e91e63"},
    "FTSE100":{"sym":"^FTSE","vix":None,"vf":18,"cur":"£","col":"#607d8b"},
    "CAC40":{"sym":"^FCHI","vix":None,"vf":18,"cur":"€","col":"#795548"},
}

TOP10={2000:['GE','INTC','MSFT','CSCO','XOM','WMT','C','ORCL','PFE','IBM'],2001:['GE','MSFT','XOM','C','WMT','PFE','INTC','JNJ','BP','AIG'],2002:['GE','MSFT','XOM','WMT','C','PFE','JNJ','INTC','AIG','IBM'],2003:['GE','MSFT','XOM','WMT','PFE','C','JNJ','INTC','AIG','IBM'],2004:['GE','XOM','MSFT','WMT','C','PFE','JNJ','INTC','AIG','IBM'],2005:['GE','XOM','MSFT','C','WMT','BP','PFE','JNJ','IBM','AIG'],2006:['XOM','GE','MSFT','C','BAC','WMT','PFE','JNJ','BP','AIG'],2007:['XOM','GE','MSFT','WMT','C','BP','BAC','JNJ','PFE','AIG'],2008:['XOM','GE','MSFT','WMT','JNJ','PG','CVX','T','IBM','JPM'],2009:['XOM','WMT','MSFT','JNJ','PG','IBM','CVX','JPM','GE','AAPL'],2010:['XOM','AAPL','MSFT','BRK-B','GE','WMT','GOOGL','CVX','IBM','PG'],2011:['XOM','AAPL','MSFT','IBM','CVX','JNJ','WMT','GE','PG','GOOGL'],2012:['AAPL','XOM','MSFT','WMT','IBM','GE','CVX','BRK-B','GOOGL','JNJ'],2013:['AAPL','XOM','MSFT','GOOGL','BRK-B','GE','JNJ','WMT','CVX','PG'],2014:['AAPL','XOM','MSFT','GOOGL','BRK-B','JNJ','GE','WMT','CVX','PG'],2015:['AAPL','GOOGL','MSFT','BRK-B','XOM','AMZN','META','JNJ','GE','WMT'],2016:['AAPL','GOOGL','MSFT','BRK-B','AMZN','META','JNJ','XOM','JPM','WMT'],2017:['AAPL','GOOGL','MSFT','AMZN','BRK-B','META','JNJ','JPM','XOM','V'],2018:['AAPL','MSFT','AMZN','GOOGL','BRK-B','META','JNJ','JPM','V','WMT'],2019:['AAPL','MSFT','AMZN','GOOGL','BRK-B','META','JPM','JNJ','V','WMT'],2020:['AAPL','MSFT','AMZN','GOOGL','META','TSLA','BRK-B','V','JNJ','WMT'],2021:['AAPL','MSFT','GOOGL','AMZN','TSLA','META','NVDA','BRK-B','JPM','JNJ'],2022:['AAPL','MSFT','GOOGL','AMZN','BRK-B','TSLA','UNH','JNJ','V','NVDA'],2023:['AAPL','MSFT','AMZN','NVDA','GOOGL','META','TSLA','BRK-B','LLY','V'],2024:['MSFT','AAPL','NVDA','GOOGL','AMZN','META','BRK-B','LLY','TSLA','AVGO'],2025:['NVDA','AAPL','MSFT','GOOGL','AMZN','META','TSLA','AVGO','LLY','BRK-B'],2026:['NVDA','AAPL','MSFT','GOOGL','AMZN','META','TSLA','AVGO','LLY','BRK-B']}

# ═══════════════════════ AI ═══════════════════════
def _ai_box(title,bullets,accent="#00d084"):
    items="".join(f"<li style='margin:5px 0'>{b}</li>" for b in bullets)
    st.markdown(f"""<div style="background:rgba(0,208,132,0.07);border-left:4px solid {accent};padding:14px 18px;border-radius:8px;margin:16px 0;font-size:0.91em;line-height:1.6"><span style="color:{accent};font-weight:700">🤖 AI — {title}</span><ul style="margin:10px 0 0 0;padding-left:20px">{items}</ul></div>""",unsafe_allow_html=True)

def _ai1(sp,rp):return [f"기간{rp}|{len(sp)}개",f"저평가:<b>{sp.idxmin()}</b>({sp.min():+.1f}%)",f"고평가:<b>{sp.idxmax()}</b>({sp.max():+.1f}%)"]
def _ai2(reg,mn,vn,cn,rn,dn,p):
    lv={"Bull":p.get("lev_bull",2),"Bear":p.get("lev_bear",1),"Panic":p.get("lev_panic",1.5)}.get(reg,1)
    b=[f"<b>{reg}</b>|레버{lv}배"]
    if reg=="Panic":b.append(f"Bear이탈: CCI>0 AND RSI>{p.get('rsi_bear',50)}")
    else:b.append(f"Panic전환: VIX≥{p.get('vix_panic',30)} AND MDD≤{p.get('mdd_panic',-0.15)*100:.0f}%")
    return b
def _ai3(m,rs,an):return [f"연{m.get('annual_return',0):.1f}%|MDD{m.get('mdd',0):.1f}%|Sharpe{m.get('sharpe',0):.3f}|Calmar{m.get('calmar',0):.4f}",f"최종{m.get('final_value',0)/1e8:.2f}억|P매집{rs.get('P총(만)',0):.0f}만"]
def _ai5(results):
    rows=[(n,r['metrics'].get('annual_return',0),r['metrics'].get('mdd',0),r['metrics'].get('calmar',0)) for n,r in results.items() if r and r.get('metrics')]
    if not rows:return ["없음"]
    br=max(rows,key=lambda x:x[1]);bc=max(rows,key=lambda x:x[3])
    b=[f"최고수익: <b>{br[0]}</b>({br[1]:.1f}%)",f"최고Calmar: <b>{bc[0]}</b>({bc[3]:.4f})"]
    # 1a vs 1b
    v1=next(((x[1],x[2]) for x in rows if "1a" in x[0]),None);v2=next(((x[1],x[2]) for x in rows if "1b" in x[0]),None)
    if v1 and v2:b.append(f"ETF드레인: 기존{v1[0]:.1f}%/MDD{v1[1]:.1f}% vs v2 {v2[0]:.1f}%/MDD{v2[1]:.1f}%")
    # 4a vs 4b
    a1=next(((x[1],x[2]) for x in rows if "4a" in x[0]),None);a2=next(((x[1],x[2]) for x in rows if "4b" in x[0]),None)
    if a1 and a2:b.append(f"ETF→TopN드레인: 기존{a1[0]:.1f}%/MDD{a1[1]:.1f}% vs v2 {a2[0]:.1f}%/MDD{a2[1]:.1f}%")
    return b
def _ai7(sim,yrs,m):
    cv=sim['current_val'];p50=sim['percentiles']['p50'];an=((p50/cv)**(1/yrs)-1)*100 if cv>0 else 0
    return [f"{m}{yrs}년|연환산<b>{an:.1f}%</b>",f"2배확률:<b>{sim['target_probs'].get('100%',0)}%</b>"]

# ═══════════════════════ 데이터 ═══════════════════════
_dl_errors=[]
def _yf(syms,start,end,retries=3):
    if isinstance(syms,str):syms=[syms]
    for a in range(retries):
        try:
            r=yf.download(syms,start=start,end=end,progress=False,timeout=30)
            if not r.empty:return r
        except Exception as e:_dl_errors.append(f"[{','.join(syms[:3])}]{type(e).__name__}");time.sleep(2*(a+1))
    if len(syms)>1:
        fr={}
        for s in syms:
            for _ in range(2):
                try:
                    d=yf.download(s,start=start,end=end,progress=False,timeout=20)
                    if not d.empty:fr[s]=d["Close"];break
                except:time.sleep(2)
        if fr:return pd.DataFrame(fr)
    return pd.DataFrame()
def _close(raw):return raw["Close"].ffill() if isinstance(raw.columns,pd.MultiIndex) else raw.ffill()

@st.cache_data(ttl=3600,show_spinner=False)
def fetch_asset(name,start):
    ac=ASSET_CLASSES[name];ps=ac["sym"];vs=ac["vix"];vf=ac["vf"]
    raw=_yf([ps]+([vs] if vs else []),start,TODAY)
    if raw.empty:return pd.DataFrame()
    c=_close(raw);df=pd.DataFrame(index=c.index)
    if ps in c.columns:df["Price"]=c[ps]
    elif len(c.columns)==1:df["Price"]=c.iloc[:,0]
    else:return pd.DataFrame()
    df["VIX"]=c[vs] if vs and vs in c.columns else df["Price"].pct_change().rolling(20).std()*np.sqrt(252)*100
    df=df.ffill();df["VIX"]=df["VIX"].fillna(vf);df["Daily_Ret"]=df["Price"].pct_change();return df.dropna(subset=["Price"])

@st.cache_data(ttl=3600,show_spinner="📡 자산군...")
def fetch_all_assets(start):
    syms={n:a["sym"] for n,a in ASSET_CLASSES.items()};raw=_yf(list(syms.values()),start,TODAY)
    if raw.empty:return pd.DataFrame()
    c=_close(raw);df=pd.DataFrame(index=c.index)
    for n,s in syms.items():
        if s in c.columns:df[n]=c[s]
    return df.ffill().bfill()

@st.cache_data(ttl=86400,show_spinner="📡 종목...")
def fetch_stocks(start):
    all_t=list({t for ts in TOP10.values() for t in ts});raw=_yf(["SPY"]+all_t,start,TODAY)
    if raw.empty:return pd.DataFrame(),pd.Series(dtype=float)
    c=_close(raw);return c,c.get("SPY",pd.Series(dtype=float))

# ═══════════════════════ 지표 ═══════════════════════
def add_ind(data):
    df=data.copy();p=df["Price"];df["MA_200"]=p.rolling(200).mean();df["Disp"]=(p-df["MA_200"])/df["MA_200"]*100
    sma=p.rolling(200).mean();mad=p.rolling(200).apply(lambda x:np.abs(x-x.mean()).mean(),raw=True);df["CCI"]=(p-sma)/(0.015*mad)
    d=p.diff();g=d.where(d>0,0.0).rolling(14).mean();l=(-d.where(d<0,0.0)).rolling(14).mean();df["RSI"]=100-(100/(1+g/l))
    df["MDD"]=(p/p.rolling(252,min_periods=1).max())-1.0;return df

# ═══════════════════════ 전략 엔진 ═══════════════════════
def _state(cur,vix,cci,rsi,mdd,disp,p):
    if vix>=p["vix_panic"] and mdd<=p["mdd_panic"]:return "Panic"
    if cur=="Panic":return "Bear" if (cci>0 and rsi>p["rsi_bear"]) else "Panic"
    if cur=="Bear":return "Bull" if (cci>p["cci_bull"] and rsi>p["rsi_bull"]) else "Bear"
    return "Bear" if (cci<p["cci_bear"] and disp<-3.0) else "Bull"

def _mstg(ma,ms):
    if ma>=ms[0]:return f"1단계(≥{ms[0]*100:.0f}%)"
    elif ma>=ms[1]:return f"2단계(≥{ms[1]*100:.0f}%)"
    elif ma>=ms[2]:return f"3단계(≥{ms[2]*100:.0f}%)"
    return "미달"

# ── run_beta: 기존 ──
def run_beta(data,params,budget,inh=None,sim_start=None,sim_end=None):
    df=add_ind(data);df=df.dropna(subset=["MA_200","MDD"]).copy()
    if sim_start:df=df[df.index>=pd.Timestamp(sim_start)]
    if sim_end:df=df[df.index<=pd.Timestamp(sim_end)]
    if df.empty:return _emp()
    ms=list(params["mdd_threshold_sets"]);ds=list(params["drain_sets"])
    dst=(budget*(params["stock_ratio"]/18))/TRADING_DAYS;dcs=(budget*((18-params["stock_ratio"])/18))/TRADING_DAYS
    if inh:ys=float(inh.get("yj_st",0));yc=float(inh.get("yj_cs",0));cur=inh.get("state","Bull");pc=int(inh.get("p_cnt",0));tp=float(inh.get("total_principal",0))
    else:ys=yc=0.0;cur="Bull";pc=0;tp=0.0
    recs,slogs,plogs=[],[],[];pt=0.0
    for dt,row in df.iterrows():
        dr=float(row.get("Daily_Ret",0) or 0);vx=float(row.get("VIX",15));cc=float(row.get("CCI",0));rs=float(row.get("RSI",50));md=float(row.get("MDD",0));dp=float(row.get("Disp",0))
        pv=cur;cur=_state(cur,vx,cc,rs,md,dp,params);lv={"Bull":params["lev_bull"],"Bear":params["lev_bear"],"Panic":params["lev_panic"]}[cur]
        if cur!=pv:slogs.append({"날짜":dt.date(),"변화":f"{pv}→{cur}","VIX":round(vx,1),"MDD%":round(md*100,1),"CCI":round(cc,1),"RSI":round(rs,1),"Disp%":round(dp,1),"레버리지":lv})
        tp+=budget/TRADING_DAYS
        if dr:ys*=1+dr*lv-max(0,lv-1)*(LEV_COST/TRADING_DAYS)
        yc*=1+CMA_INTEREST/TRADING_DAYS;ys+=dst;yc+=dcs
        if cur=="Panic" and pc%params["panic_period"]==0:
            m=abs(md);dr2=(ds[0] if m>=ms[0] else ds[1] if m>=ms[1] else ds[2] if m>=ms[2] else 0)
            if dr2>0:
                pb=min((yc*dr2)/params["periodic_denom"],yc);cma_b=yc;ys+=pb;yc-=pb;pt+=pb
                plogs.append({"날짜":dt.date(),"MDD%":round(md*100,1),"단계":_mstg(m,ms),"매수(만)":round(pb/1e4,1),"CMA전(만)":round(cma_b/1e4,1),"CMA후(만)":round(yc/1e4,1),"누적(만)":round(pt/1e4,1),"VIX":round(vx,1)})
        pc=pc+1 if cur=="Panic" else 0
        recs.append({"time":dt,"yj_val":ys+yc,"yj_st":ys,"yj_cs":yc,"state":cur,"leverage":lv,"total_principal":tp})
    if not recs:return _emp()
    eq=pd.DataFrame(recs).set_index("time");sc=eq["state"].value_counts()
    return {"equity_curve":eq,"dca_curve":_dca(df,budget),"metrics":_met(eq),"state_logs":slogs,"panic_logs":plogs,"panic_episodes":[],"regime_stats":{"Bull":int(sc.get("Bull",0)),"Bear":int(sc.get("Bear",0)),"Panic":int(sc.get("Panic",0)),"전환":len(slogs),"P매수":len(plogs),"P총(만)":round(pt/1e4,1)},"final_state":{"yj_st":ys,"yj_cs":yc,"state":cur,"p_cnt":pc,"total_principal":tp}}

# ── run_beta_v2: 단계 트리거 + 균등분할 ──
def run_beta_v2(data,params,budget,inh=None,sim_start=None,sim_end=None):
    df=add_ind(data);df=df.dropna(subset=["MA_200","MDD"]).copy()
    if sim_start:df=df[df.index>=pd.Timestamp(sim_start)]
    if sim_end:df=df[df.index<=pd.Timestamp(sim_end)]
    if df.empty:return _emp()
    ms=list(params["mdd_threshold_sets"]);ds=list(params["drain_sets"]);denom=params["periodic_denom"]
    dst=(budget*(params["stock_ratio"]/18))/TRADING_DAYS;dcs=(budget*((18-params["stock_ratio"])/18))/TRADING_DAYS
    if inh:ys=float(inh.get("yj_st",0));yc=float(inh.get("yj_cs",0));cur=inh.get("state","Bull");pc=int(inh.get("p_cnt",0));tp=float(inh.get("total_principal",0))
    else:ys=yc=0.0;cur="Bull";pc=0;tp=0.0
    recs,slogs,plogs=[],[],[];pt=0.0;triggered=set();bpp=0.0;rem=0
    for dt,row in df.iterrows():
        dr=float(row.get("Daily_Ret",0) or 0);vx=float(row.get("VIX",15));cc=float(row.get("CCI",0));rs=float(row.get("RSI",50));md=float(row.get("MDD",0));dp=float(row.get("Disp",0))
        pv=cur;cur=_state(cur,vx,cc,rs,md,dp,params);lv={"Bull":params["lev_bull"],"Bear":params["lev_bear"],"Panic":params["lev_panic"]}[cur]
        if cur!=pv:slogs.append({"날짜":dt.date(),"변화":f"{pv}→{cur}","VIX":round(vx,1),"MDD%":round(md*100,1),"CCI":round(cc,1),"RSI":round(rs,1),"Disp%":round(dp,1),"레버리지":lv})
        tp+=budget/TRADING_DAYS
        if dr:ys*=1+dr*lv-max(0,lv-1)*(LEV_COST/TRADING_DAYS)
        yc*=1+CMA_INTEREST/TRADING_DAYS;ys+=dst;yc+=dcs
        if cur=="Panic":
            m=abs(md);ns=None
            if m>=ms[0] and 1 not in triggered:ns=1;dr2=ds[0]
            elif m>=ms[1] and 2 not in triggered:ns=2;dr2=ds[1]
            elif m>=ms[2] and 3 not in triggered:ns=3;dr2=ds[2]
            if ns is not None:bpp=yc*dr2/max(denom,1);rem=denom;triggered.add(ns)
            if rem>0 and pc%params["panic_period"]==0:
                pb=min(bpp,yc)
                if pb>0:cma_b=yc;ys+=pb;yc-=pb;pt+=pb;rem-=1;plogs.append({"날짜":dt.date(),"MDD%":round(md*100,1),"단계":_mstg(m,ms),"매수(만)":round(pb/1e4,1),"CMA전(만)":round(cma_b/1e4,1),"CMA후(만)":round(yc/1e4,1),"누적(만)":round(pt/1e4,1),"남은":rem,"VIX":round(vx,1)})
        else:triggered.clear();bpp=0.0;rem=0
        pc=pc+1 if cur=="Panic" else 0
        recs.append({"time":dt,"yj_val":ys+yc,"yj_st":ys,"yj_cs":yc,"state":cur,"leverage":lv,"total_principal":tp})
    if not recs:return _emp()
    eq=pd.DataFrame(recs).set_index("time");sc=eq["state"].value_counts()
    return {"equity_curve":eq,"dca_curve":_dca(df,budget),"metrics":_met(eq),"state_logs":slogs,"panic_logs":plogs,"panic_episodes":[],"regime_stats":{"Bull":int(sc.get("Bull",0)),"Bear":int(sc.get("Bear",0)),"Panic":int(sc.get("Panic",0)),"전환":len(slogs),"P매수":len(plogs),"P총(만)":round(pt/1e4,1)},"final_state":{"yj_st":ys,"yj_cs":yc,"state":cur,"p_cnt":pc,"total_principal":tp}}

# ── run_alpha: 기존 ──
def run_alpha(data,sc2,spy,params,budget,alpha_dca_ratio=0.0,inh=None,sim_start=None,sim_end=None):
    df=add_ind(data);df=df.dropna(subset=["MA_200","MDD"]).copy()
    if sim_start:df=df[df.index>=pd.Timestamp(sim_start)]
    if sim_end:df=df[df.index<=pd.Timestamp(sim_end)]
    if df.empty:return _emp()
    sr=sc2.pct_change().fillna(0);msets=list(params["mdd_threshold_sets"]);dsets=list(params["drain_sets"]);tn=params.get("top_n",10)
    dt_total=budget/TRADING_DAYS;d_stock=dt_total*(params["stock_ratio"]/18);d_rem=dt_total*((18-params["stock_ratio"])/18)
    d_adca=d_rem*alpha_dca_ratio;d_cma=d_rem*(1-alpha_dca_ratio)
    if inh:ys=float(inh.get("yj_st",0));yc=float(inh.get("yj_cs",0));ya=float(inh.get("yj_alpha",0));cur=inh.get("state","Bull");pc=int(inh.get("p_cnt",0));tp=float(inh.get("total_principal",0))
    else:ys=yc=ya=0.0;cur="Bull";pc=0;tp=0.0
    recs,plogs=[],[];pt=0.0;adca_total=0.0
    for dt2,row in df.iterrows():
        dr=float(row.get("Daily_Ret",0) or 0);vx=float(row.get("VIX",15));cc=float(row.get("CCI",0));rs=float(row.get("RSI",50));md=float(row.get("MDD",0));dp=float(row.get("Disp",0));yr=dt2.year
        cur=_state(cur,vx,cc,rs,md,dp,params)
        if ya>0 and dt2 in sr.index:
            tks=TOP10.get(yr-1,TOP10[max(TOP10)])[:tn];av=[t for t in tks if t in sr.columns]
            if av:ya*=(1+float(sr.loc[dt2,av].mean()))
        lv=1.0 if cur=="Panic" else {"Bull":params["lev_bull"],"Bear":params["lev_bear"]}[cur]
        tp+=dt_total
        if dr:ys*=1+dr*lv-max(0,lv-1)*(LEV_COST/TRADING_DAYS)
        yc*=1+CMA_INTEREST/TRADING_DAYS;ys+=d_stock;ya+=d_adca;yc+=d_cma;adca_total+=d_adca
        if cur=="Panic" and pc%params["panic_period"]==0:
            m=abs(md);dr2=(dsets[0] if m>=msets[0] else dsets[1] if m>=msets[1] else dsets[2] if m>=msets[2] else 0)
            if dr2>0 and yc>0:
                ba=min((yc*dr2)/params["periodic_denom"],yc);ya+=ba;yc-=ba;pt+=ba
                plogs.append({"날짜":dt2.date(),"MDD%":round(md*100,1),"단계":_mstg(m,msets),"매수(만)":round(ba/1e4,1),"CMA전(만)":round((yc+ba)/1e4,1),"CMA후(만)":round(yc/1e4,1),"누적(만)":round(pt/1e4,1)})
        pc=pc+1 if cur=="Panic" else 0
        recs.append({"time":dt2,"yj_val":ys+ya+yc,"yj_st":ys,"yj_alpha":ya,"yj_cs":yc,"state":cur,"leverage":lv,"total_principal":tp})
    if not recs:return _emp()
    eq=pd.DataFrame(recs).set_index("time")
    return {"equity_curve":eq,"dca_curve":_dca(df,budget),"metrics":_met(eq),"panic_logs":plogs,"state_logs":[],"regime_stats":{"alpha_dca_ratio":alpha_dca_ratio,"적립TopN(만)":round(adca_total/1e4,1),"Panic매수(만)":round(pt/1e4,1)},"final_state":{"yj_st":ys,"yj_cs":yc,"yj_alpha":ya,"state":cur,"p_cnt":pc,"total_principal":tp}}

# ★ run_alpha_v2: 단계 트리거 + 균등분할 (Alpha용)
def run_alpha_v2(data,sc2,spy,params,budget,alpha_dca_ratio=0.0,inh=None,sim_start=None,sim_end=None):
    df=add_ind(data);df=df.dropna(subset=["MA_200","MDD"]).copy()
    if sim_start:df=df[df.index>=pd.Timestamp(sim_start)]
    if sim_end:df=df[df.index<=pd.Timestamp(sim_end)]
    if df.empty:return _emp()
    sr=sc2.pct_change().fillna(0);msets=list(params["mdd_threshold_sets"]);dsets=list(params["drain_sets"]);tn=params.get("top_n",10)
    denom=params["periodic_denom"]
    dt_total=budget/TRADING_DAYS;d_stock=dt_total*(params["stock_ratio"]/18);d_rem=dt_total*((18-params["stock_ratio"])/18)
    d_adca=d_rem*alpha_dca_ratio;d_cma=d_rem*(1-alpha_dca_ratio)
    if inh:ys=float(inh.get("yj_st",0));yc=float(inh.get("yj_cs",0));ya=float(inh.get("yj_alpha",0));cur=inh.get("state","Bull");pc=int(inh.get("p_cnt",0));tp=float(inh.get("total_principal",0))
    else:ys=yc=ya=0.0;cur="Bull";pc=0;tp=0.0
    recs,plogs=[],[];pt=0.0;adca_total=0.0;triggered=set();bpp=0.0;rem=0
    for dt2,row in df.iterrows():
        dr=float(row.get("Daily_Ret",0) or 0);vx=float(row.get("VIX",15));cc=float(row.get("CCI",0));rs=float(row.get("RSI",50));md=float(row.get("MDD",0));dp=float(row.get("Disp",0));yr=dt2.year
        cur=_state(cur,vx,cc,rs,md,dp,params)
        if ya>0 and dt2 in sr.index:
            tks=TOP10.get(yr-1,TOP10[max(TOP10)])[:tn];av=[t for t in tks if t in sr.columns]
            if av:ya*=(1+float(sr.loc[dt2,av].mean()))
        lv=1.0 if cur=="Panic" else {"Bull":params["lev_bull"],"Bear":params["lev_bear"]}[cur]
        tp+=dt_total
        if dr:ys*=1+dr*lv-max(0,lv-1)*(LEV_COST/TRADING_DAYS)
        yc*=1+CMA_INTEREST/TRADING_DAYS;ys+=d_stock;ya+=d_adca;yc+=d_cma;adca_total+=d_adca
        if cur=="Panic":
            m=abs(md);ns=None
            if m>=msets[0] and 1 not in triggered:ns=1;dr2=dsets[0]
            elif m>=msets[1] and 2 not in triggered:ns=2;dr2=dsets[1]
            elif m>=msets[2] and 3 not in triggered:ns=3;dr2=dsets[2]
            if ns is not None:bpp=yc*dr2/max(denom,1);rem=denom;triggered.add(ns)
            if rem>0 and pc%params["panic_period"]==0:
                pb=min(bpp,yc)
                if pb>0:ya+=pb;yc-=pb;pt+=pb;rem-=1;plogs.append({"날짜":dt2.date(),"MDD%":round(md*100,1),"단계":_mstg(m,msets),"매수(만)":round(pb/1e4,1),"CMA전(만)":round((yc+pb)/1e4,1),"CMA후(만)":round(yc/1e4,1),"누적(만)":round(pt/1e4,1),"남은":rem})
        else:triggered.clear();bpp=0.0;rem=0
        pc=pc+1 if cur=="Panic" else 0
        recs.append({"time":dt2,"yj_val":ys+ya+yc,"yj_st":ys,"yj_alpha":ya,"yj_cs":yc,"state":cur,"leverage":lv,"total_principal":tp})
    if not recs:return _emp()
    eq=pd.DataFrame(recs).set_index("time")
    return {"equity_curve":eq,"dca_curve":_dca(df,budget),"metrics":_met(eq),"panic_logs":plogs,"state_logs":[],"regime_stats":{"alpha_dca_ratio":alpha_dca_ratio,"적립TopN(만)":round(adca_total/1e4,1),"Panic매수(만)":round(pt/1e4,1)},"final_state":{"yj_st":ys,"yj_cs":yc,"yj_alpha":ya,"state":cur,"p_cnt":pc,"total_principal":tp}}

def _dca(df,b):
    d=b/TRADING_DAYS;sh=pr=0.0;rows=[]
    for dt,row in df.iterrows():p=row["Price"];sh+=d/p if p>0 else 0;pr+=d;rows.append({"time":dt,"portfolio_value":sh*p,"principal":pr})
    return pd.DataFrame(rows).set_index("time")
def _met(eq):
    if eq.empty:return {}
    fv=eq["yj_val"].iloc[-1];inv=eq["total_principal"].iloc[-1];tr=(fv/inv-1)*100 if inv>0 else 0
    pk=eq["yj_val"].cummax();mdd=((eq["yj_val"]/pk)-1).min();yrs=(eq.index[-1]-eq.index[0]).days/365.25
    ar=((fv/inv)**(1/max(yrs,0.01))-1) if inv>0 else 0;cal=ar/abs(mdd) if mdd!=0 else 0;dr=eq["yj_val"].pct_change().dropna();sh=dr.mean()/dr.std()*np.sqrt(TRADING_DAYS) if dr.std()>0 else 0
    return {"total_return":round(tr,2),"annual_return":round(ar*100,2),"mdd":round(mdd*100,2),"calmar":round(cal,4),"sharpe":round(sh,4),"final_value":round(fv,0)}
def _emp():return {"equity_curve":pd.DataFrame(),"dca_curve":pd.DataFrame(),"metrics":{},"state_logs":[],"panic_logs":[],"panic_episodes":[],"regime_stats":{},"final_state":{}}

# ═══════════════════════ 그리드+WFV ═══════════════════════
def _combos(g):k,v=zip(*g.items());return [dict(zip(k,v2)) for v2 in itertools.product(*v)]
def run_grid(data,grid,base,budget,pfn=None,sim_start=None,sim_end=None):
    combos=_combos(grid);res=[];fc=0
    for i,c in enumerate(combos):
        try:r=run_beta(data,{**base,**c},budget,sim_start=sim_start,sim_end=sim_end);m=r["metrics"];res.append({**c,"calmar":m.get("calmar",-999),"annual_ret":m.get("annual_return",0),"mdd":m.get("mdd",0),"sharpe":m.get("sharpe",0),"total_ret":m.get("total_return",0),"final_val":m.get("final_value",0)})
        except:fc+=1
        if pfn and (i+1)%max(len(combos)//20,1)==0:pfn((i+1)/len(combos))
    if pfn:pfn(1.0)
    return sorted(res,key=lambda x:x["calmar"],reverse=True)
def run_wfv(data,base,budget,isy,oosy,grid,pfn=None,sim_start=None):
    sy=int(sim_start[:4]) if sim_start else data.index.year.min();yrs=sorted(y for y in data.index.year.unique() if y>=sy)
    if len(yrs)<isy+oosy:return {"error":"기간부족","windows":[],"combined_equity":pd.DataFrame(),"metrics":{},"p_value":None}
    combos=_combos(grid);tw=max((len(yrs)-isy)//oosy,1);wins=[];oeqs=[];inh2=None;i=step=0
    while i+isy<len(yrs):
        iy=yrs[i:i+isy];oy=yrs[i+isy:i+isy+oosy]
        if not oy:break
        bp,bc=-np.inf,{}
        for c in combos:
            try:r=run_beta(data,{**base,**c},budget,sim_start=f"{iy[0]}-01-01",sim_end=f"{iy[-1]}-12-31");cal=r["metrics"].get("calmar",-np.inf)
            except:continue
            if cal>bc:bc,bp=cal,c
        res=run_beta(data,{**base,**bp},budget,inh2,sim_start=f"{oy[0]}-01-01",sim_end=f"{oy[-1]}-12-31");inh2=res["final_state"]
        wins.append({"IS":f"{iy[0]}~{iy[-1]}","OOS":f"{oy[0]}","IS_Cal":round(bc,4),"OOS_Ret%":res["metrics"].get("annual_return",0),"OOS_MDD%":res["metrics"].get("mdd",0),"OOS_Cal":res["metrics"].get("calmar",0)})
        if not res["equity_curve"].empty:oeqs.append(res["equity_curve"])
        step+=1;
        if pfn:pfn(min(step/tw,1.0))
        i+=oosy
    if not oeqs:return {"windows":wins,"combined_equity":pd.DataFrame(),"metrics":{},"p_value":None}
    cb=pd.concat(oeqs).sort_index();cb=cb[~cb.index.duplicated(keep="last")]
    return {"windows":wins,"combined_equity":cb,"metrics":_met(cb),"p_value":None}

# ═══════════════════════ 몬테카를로 ═══════════════════════
def _pure_returns(eq,b):dc=b/TRADING_DAYS;vals=eq["yj_val"].values;pr=np.empty(len(vals)-1);[pr.__setitem__(i,(vals[i+1]-dc)/vals[i]-1 if vals[i]>0 else 0) for i in range(len(pr))];return pr[np.isfinite(pr)]
def mc_sim(eq,b,yrs,n=1000):
    dr=_pure_returns(eq,b);
    if len(dr)<60:return None
    cv=eq["yj_val"].iloc[-1];cp=eq["total_principal"].iloc[-1];nd=yrs*TRADING_DAYS;di=b/TRADING_DAYS;rng=np.random.default_rng(42);fv=np.zeros(n);paths=np.zeros((n,nd))
    for i in range(n):
        v=cv
        for d in range(nd):v=v*(1+rng.choice(dr))+di;paths[i,d]=v
        fv[i]=v
    return _bsr(fv,paths,nd,n,yrs,cv,cp+b*yrs)
def boot_sim(eq,b,yrs,n=1000,blk=21):
    dr=_pure_returns(eq,b);
    if len(dr)<blk*2:return None
    cv=eq["yj_val"].iloc[-1];cp=eq["total_principal"].iloc[-1];nd=yrs*TRADING_DAYS;di=b/TRADING_DAYS;nb=len(dr)-blk+1;rng=np.random.default_rng(123);fv=np.zeros(n);paths=np.zeros((n,nd))
    for i in range(n):
        v=cv;d=0
        while d<nd:
            st2=rng.integers(0,nb);bk=dr[st2:st2+blk]
            for r in bk:
                if d>=nd:break
                v=v*(1+r)+di;paths[i,d]=v;d+=1
        fv[i]=v
    return _bsr(fv,paths,nd,n,yrs,cv,cp+b*yrs)
def _bsr(fv,paths,nd,n,yrs,cv,ti):
    pp={f"p{p}":np.percentile(paths,p,axis=0) for p in [5,25,50,75,95]};tgts=[50,100,150,200,300,500]
    return {"n_sims":n,"years":yrs,"current_val":cv,"total_invested":ti,"percentiles":{f"p{p}":np.percentile(fv,p) for p in [5,10,25,50,75,90,95]},"ret_pcts":{f"p{p}_ret":(np.percentile(fv,p)/ti-1)*100 for p in [5,10,25,50,75,90,95]},"target_probs":{f"{t}%":round(float(np.mean(fv>=ti*(1+t/100)))*100,1) for t in tgts},"final_vals":fv,"path_pcts":pp,"n_days":nd}

# ═══════════════════════ 과열/저평가 (간결) ═══════════════════════
@st.cache_data(ttl=3600,show_spinner=False)
def analyze_oh(ticker):
    try:
        df=yf.download(ticker,period="2y",interval="1d",progress=False,timeout=20)
        if isinstance(df.columns,pd.MultiIndex):df.columns=df.columns.get_level_values(0)
        if df.empty or len(df)<200:return None
    except:return None
    p=df["Close"];df["MA50"]=p.rolling(50).mean();df["MA200"]=p.rolling(200).mean();d=p.diff();g=d.where(d>0,0.0).rolling(14).mean();l=(-d.where(d<0,0.0)).rolling(14).mean();df["RSI"]=100-(100/(1+g/(l+1e-9)))
    bb=p.rolling(20);df["BB_L"]=bb.mean()-2*bb.std();tr=np.maximum(df["High"]-df["Low"],np.maximum(abs(df["High"]-p.shift()),abs(df["Low"]-p.shift())));df["ATR"]=tr.rolling(14).mean();df["Peak"]=p.expanding().max();df["DD"]=(p-df["Peak"])/df["Peak"]
    la=df.dropna().iloc[-1];cp=float(la["Close"]);m5=float(la["MA50"]);m2=float(la["MA200"]);rsi=float(la["RSI"]);dd=float(la["DD"]);atr=float(la["ATR"]);bbl=float(la["BB_L"])
    bzh=m5*0.95;bzl=min(m2,bbl);slv=cp-2*atr;fsl=max(m2*0.95,slv) if cp>m2 else slv;sig="🟢매수" if (cp<=bzh or rsi<45) else ("🔴과열" if rsi>70 else "🟡관망")
    return {"ticker":ticker,"price":cp,"rsi":rsi,"dd":dd,"buy_zone":f"${bzl:.2f}~${bzh:.2f}","sl":fsl,"sl_pct":(fsl/cp-1)*100,"signal":sig,"vs_ma200":(cp/m2-1)*100}

@st.cache_data(ttl=3600,show_spinner=False)
def analyze_rv(tickers,period="12mo"):
    raw=_yf(tickers,f"{CUR_YEAR-2}-01-01",TODAY)
    if raw.empty:return None,None,None
    c=_close(raw).ffill().bfill();pm={"3mo":63,"6mo":126,"12mo":252,"24mo":504};c=c.tail(pm.get(period,252))
    norm=c.apply(lambda x:x/x.dropna().iloc[0] if not x.dropna().empty else x);ga=norm.mean(axis=1);sp=(norm.iloc[-1]-ga.iloc[-1])*100
    l1=pd.DataFrame({"가격":c.iloc[-1],"괴리율(%)":sp}).sort_values("괴리율(%)");l1["판정"]=l1["괴리율(%)"].apply(lambda x:"🟢저평가" if x<-5 else ("🔴고평가" if x>5 else "🟡보합"))
    fund=[]
    for t in tickers:
        try:
            tk=yf.Ticker(t);mc=tk.info.get("marketCap",np.nan);loi=np.nan;qs="N/A";trend="N/A"
            try:
                fin=tk.financials
                for met in ["Operating Income","Gross Profit","EBITDA"]:
                    if met in fin.index:oi=fin.loc[met].dropna();
                    if not oi.empty:loi=oi.iloc[0];break
                trend="📈" if loi>0 else "📉"
            except:pass
            poi=mc/loi if (not np.isnan(mc) and not np.isnan(loi) and loi>0) else np.nan
            fund.append({"티커":t,"P/OI":round(poi,1) if not np.isnan(poi) else "N/A","트렌드":trend,"OI":qs})
        except:fund.append({"티커":t,"P/OI":"N/A","트렌드":"N/A","OI":"N/A"})
    return l1,pd.DataFrame(fund).set_index("티커"),norm

# ═══════════════════════ 차트 ═══════════════════════
_SC={"Bull":"rgba(30,144,255,0.12)","Bear":"rgba(255,165,0,0.18)","Panic":"rgba(255,50,50,0.22)"}
def fig_eq(eq,dca,t):f=go.Figure();f.add_trace(go.Scatter(x=eq.index,y=eq["yj_val"]/1e8,name="YJ",line=dict(color="#00d084",width=2.5)));(not dca.empty) and f.add_trace(go.Scatter(x=dca.index,y=dca["portfolio_value"]/1e8,name="DCA",line=dict(color="#ff9800",dash="dot")));f.update_layout(title=t,yaxis_title="억원",template=_D,height=380);return f
def fig_dd(eq):d=((eq["yj_val"]/eq["yj_val"].cummax())-1)*100;f=go.Figure(go.Scatter(x=eq.index,y=d,fill="tozeroy",line=dict(color="#ff4444")));f.update_layout(title="DD(%)",template=_D,height=280);return f
def fig_yr(eq):yr=eq["yj_val"].resample("YE").last().pct_change().dropna()*100;f=go.Figure(go.Bar(x=[str(d.year) for d in yr.index],y=yr.values,marker_color=["#2ecc71" if v>=0 else "#e74c3c" for v in yr.values],text=[f"{v:.1f}%" for v in yr.values],textposition="outside"));f.update_layout(title="연도별(%)",template=_D,height=340);return f
def fig_regime(eq,price):
    f=go.Figure();f.add_trace(go.Scatter(x=price.index,y=price.values,name="지수",line=dict(color="white",width=1.5)));f.add_trace(go.Scatter(x=[None],y=[None],mode="markers",marker=dict(size=10,color="rgba(30,144,255,0.5)"),name="🟦Bull"));f.add_trace(go.Scatter(x=[None],y=[None],mode="markers",marker=dict(size=10,color="rgba(255,165,0,0.5)"),name="🟧Bear"));f.add_trace(go.Scatter(x=[None],y=[None],mode="markers",marker=dict(size=10,color="rgba(255,50,50,0.5)"),name="🟥Panic"))
    pv=None;sg=None
    for dt,row in eq.iterrows():
        s=row["state"]
        if s!=pv:
            if pv and sg is not None:f.add_vrect(x0=sg,x1=dt,fillcolor=_SC.get(pv,""),line_width=0,layer="below")
            sg,pv=dt,s
    if pv and sg is not None:f.add_vrect(x0=sg,x1=eq.index[-1],fillcolor=_SC.get(pv,""),line_width=0,layer="below")
    f.update_layout(title="지수&레짐",template=_D,height=380);return f
def fig_mc_p(sim,nm=""):pp=sim["path_pcts"];nd=sim["n_days"];x=list(range(0,nd,max(nd//200,1)));f=go.Figure();[(f.add_trace(go.Scatter(x=x,y=[pp[p][i]/1e8 for i in x],name=p,line=dict(color=c,dash=d,width=3 if p=="p50" else 1.5)))) for p,c,d in [("p5","rgba(255,68,68,0.5)","dot"),("p25","rgba(255,165,0,0.7)","dash"),("p50","#00d084","solid"),("p75","rgba(33,150,243,0.7)","dash"),("p95","rgba(171,71,188,0.5)","dot")]];f.update_layout(title=f"{nm} {sim['years']}년",template=_D,height=420);return f
def fig_mc_h(sim,nm=""):f=go.Figure(go.Histogram(x=sim["final_vals"]/1e8,nbinsx=50,marker_color="#00d084",opacity=0.75));f.add_vline(x=sim["total_invested"]/1e8,line_dash="dash",line_color="red");f.update_layout(title=f"{nm}분포",template=_D,height=350);return f

# ═══════════════════════ 사이드바 ═══════════════════════
def _pf(s):
    try:return [float(x.strip()) for x in s.split(",") if x.strip()]
    except:return []
def _pi(s):
    try:return [int(float(x.strip())) for x in s.split(",") if x.strip()]
    except:return []
def _pts(s):
    try:
        parts=s.split("|");result=[]
        for part in parts:
            part=part.strip().strip("()");nums=[float(x.strip()) for x in part.split(",") if x.strip()]
            if len(nums)==3:result.append(tuple(nums))
        return result if result else [(0.45,0.30,0.15)]
    except:return [(0.45,0.30,0.15)]

_PRESETS={"Nasdaq":{"p_vix":"25,30","p_mdd":"-0.12,-0.15,-0.18","p_cb":"50,80,100","p_cbr":"-60,-80,-100","p_rb":"50,70,90","p_rbr":"40,60,80","p_ms":"(0.55,0.35,0.15)","p_ds":"(1.0,0.6,0.4)"},"S&P 500":{"p_vix":"25","p_mdd":"-0.12,-0.15","p_cb":"50,80,100","p_cbr":"-50,-100","p_rb":"50,70,90","p_rbr":"40,60,80","p_ms":"(0.45,0.30,0.15)","p_ds":"(1.0,0.6,0.4)"}}
_DP=_PRESETS.get("Nasdaq")

with st.sidebar:
    st.title("📈 YJ-Quant v8.7c")
    asset_name=st.selectbox("🌍 자산",list(ASSET_CLASSES.keys()),index=1)
    _cp=_PRESETS.get(asset_name,_DP)
    if st.session_state.get("_pap")!=asset_name:
        for k,v in _cp.items():st.session_state[k]=v
        st.session_state["_pap"]=asset_name
    else:
        for k,v in _cp.items():
            if k not in st.session_state:st.session_state[k]=v
    cs2,ce2=st.columns(2);start_year=cs2.number_input("시작",2000,CUR_YEAR-1,2010);end_year=ce2.number_input("종료",start_year+1,CUR_YEAR,CUR_YEAR)
    annual_budget=st.number_input("연투자(원)",value=40_000_000,step=1_000_000,format="%d")
    g_lb=st.text_input("LevBull","2.0");g_lbr=st.text_input("LevBear","1.0");g_lp=st.text_input("LevPanic","1.5")
    g_sr=st.text_input("주식(/18)","15");g_pp=st.text_input("P주기","1,5");g_pd=st.text_input("분모","1,5")
    if st.button(f"⚙️{asset_name}초기화",key="bp"):
        for k,v in _cp.items():st.session_state[k]=v
        st.rerun()
    g_vix=st.text_input("VIX",key="p_vix");g_mdd=st.text_input("MDD",key="p_mdd");g_cb=st.text_input("CCIBull",key="p_cb");g_cbr=st.text_input("CCIBear",key="p_cbr")
    g_rb=st.text_input("RSIBull",key="p_rb");g_rbr=st.text_input("RSIBear",key="p_rbr");g_ms=st.text_input("MDD세트",key="p_ms");g_ds=st.text_input("드레인",key="p_ds")
    alpha_mode=st.radio("Alpha",["①TopN적립","②PanicOnly","③하이브리드"],index=1)
    if alpha_mode.startswith("③"):alpha_dca_ratio=st.slider("적립%",0.0,1.0,0.4,0.05)
    elif alpha_mode.startswith("①"):alpha_dca_ratio=1.0
    else:alpha_dca_ratio=0.0
    wc1,wc2=st.columns(2);wfv_is=wc1.number_input("IS",2,10,4);wfv_oos=wc2.number_input("OOS",1,5,1)

grid_params={"lev_bull":_pf(g_lb) or [2.0],"lev_bear":_pf(g_lbr) or [1.0],"lev_panic":_pf(g_lp) or [1.5],"stock_ratio":_pi(g_sr) or [15],"panic_period":_pi(g_pp) or [1],"periodic_denom":_pi(g_pd) or [1],"vix_panic":_pf(g_vix) or [25,30],"mdd_panic":_pf(g_mdd) or [-0.15],"cci_bull":_pf(g_cb) or [50,100],"cci_bear":_pf(g_cbr) or [-50,-100],"rsi_bull":_pf(g_rb) or [70],"rsi_bear":_pf(g_rbr) or [50],"mdd_threshold_sets":_pts(g_ms),"drain_sets":_pts(g_ds)}
n_combos=1
for v in grid_params.values():n_combos*=len(v)
st.sidebar.markdown(f"**그리드:{n_combos}**")
_BF={}

fetch_start=f"{start_year-3}-01-01";fetch_end=f"{end_year}-12-31" if end_year<CUR_YEAR else TODAY
with st.spinner(f"📡{asset_name}..."):market_df=fetch_asset(asset_name,fetch_start)
if market_df.empty:st.error("데이터실패");st.stop()
if end_year<CUR_YEAR:market_df=market_df[market_df.index<=pd.Timestamp(fetch_end)]
st.success(f"✅ **{asset_name}** {market_df.index[0].date()}~{market_df.index[-1].date()} ({len(market_df)}일)")

tab1,tab2,tab3,tab4,tab5,tab6,tab7=st.tabs(["🌍레이더","📈백테스트","🏠지침","🔄WFV","🆚8종비교","📡종목","🔮미래"])

# ══════════ Tab1 ══════════
with tab1:
    try:
        rp=st.selectbox("기간",["6mo","12mo","24mo","36mo","48mo","60mo"],index=1,key="rp");pd_map={"6mo":126,"12mo":252,"24mo":504,"36mo":756,"48mo":1008,"60mo":1260}
        if st.button("▶레이더",type="primary",key="br"):
            with st.spinner("..."):ap=fetch_all_assets(f"{CUR_YEAR-6}-01-01")
            if not ap.empty:st.session_state["radar"]=ap.tail(pd_map.get(rp,252))
        if "radar" in st.session_state:
            ap=st.session_state["radar"];norm=ap.apply(lambda x:x/x.dropna().iloc[0] if not x.dropna().empty else x);ga=norm.mean(axis=1);sp=(norm.iloc[-1]-ga.iloc[-1])*100
            f=go.Figure();[f.add_trace(go.Scatter(x=norm.index,y=norm[c],name=c,line=dict(color=ASSET_CLASSES.get(c,{}).get("col","#aaa"),width=2))) for c in norm.columns]
            f.add_trace(go.Scatter(x=ga.index,y=ga,name="평균",line=dict(color="yellow",dash="dash",width=3)));f.update_layout(template=_D,height=450);st.plotly_chart(f,use_container_width=True)
            ss=sp.sort_values();f2=go.Figure(go.Bar(x=ss.index,y=ss.values,marker_color=["#00d084" if v<-5 else "#ff4444" if v>5 else "#ffbb33" for v in ss],text=[f"{v:+.1f}%" for v in ss.values],textposition="outside"));f2.update_layout(template=_D,height=380);st.plotly_chart(f2,use_container_width=True)
            _ai_box("레이더",_ai1(sp,rp))
    except Exception as e:st.error(f"T1:{e}")

# ══════════ Tab2 ══════════
with tab2:
    try:
        sim_s=f"{start_year}-01-01"
        if st.button(f"▶{asset_name} 그리드",type="primary",key="bbt"):
            prog=st.progress(0);gr=run_grid(market_df,grid_params,_BF,annual_budget,lambda v:prog.progress(min(v,1.0)),sim_start=sim_s);prog.empty()
            if gr:
                best=gr[0];bp={**_BF,**{k:best[k] for k in grid_params.keys()}}
                for k in ["calmar","annual_ret","mdd","sharpe","total_ret","final_val"]:bp.pop(k,None)
                st.session_state["bt"]=run_beta(market_df,bp,annual_budget,sim_start=sim_s);st.session_state["best"]=best;st.session_state["gr"]=gr
        if "bt" in st.session_state:
            res=st.session_state["bt"];best=st.session_state.get("best",{})
            if not res["equity_curve"].empty:
                st.markdown("### 🏆1위");m=res["metrics"]
                mc=st.columns(6);mc[0].metric("총%",f"{m.get('total_return',0):.1f}%");mc[1].metric("연%",f"{m.get('annual_return',0):.1f}%");mc[2].metric("MDD",f"{m.get('mdd',0):.1f}%");mc[3].metric("Sh",f"{m.get('sharpe',0):.3f}");mc[4].metric("Cal",f"{m.get('calmar',0):.4f}");mc[5].metric("최종",f"{m.get('final_value',0)/1e8:.2f}억")
                with st.expander("📖Sharpe/Calmar"):st.markdown("- Sharpe≥1.0우수\n- Calmar≥0.3양호")
                st.plotly_chart(fig_eq(res["equity_curve"],res["dca_curve"],f"🏆{asset_name}"),use_container_width=True)
                st.plotly_chart(fig_regime(res["equity_curve"],market_df.loc[res["equity_curve"].index[0]:,"Price"]),use_container_width=True)
                st.plotly_chart(fig_dd(res["equity_curve"]),use_container_width=True);st.plotly_chart(fig_yr(res["equity_curve"]),use_container_width=True)
                if res.get("panic_logs"):
                    with st.expander(f"🔴Panic({len(res['panic_logs'])})"):st.dataframe(pd.DataFrame(res["panic_logs"]),use_container_width=True)
                _ai_box("백테스트",_ai3(m,res.get("regime_stats",{}),asset_name))
        else:st.info("▶ 시작하세요")
    except Exception as e:st.error(f"T2:{e}")

# ══════════ Tab3 ══════════
with tab3:
    try:
        if "bt" not in st.session_state or st.session_state["bt"]["equity_curve"].empty:st.warning("⚠️ 백테스트 먼저")
        else:
            best=st.session_state.get("best",{});pt2={k:best.get(k,(grid_params[k][0] if isinstance(grid_params[k],list) else grid_params[k])) for k in grid_params.keys()}
            en=add_ind(market_df);min_d=en.dropna(subset=["MA_200"]).index[0].date();max_d=en.index[-1].date()
            sel_date=st.date_input("📅기준일",value=max_d,min_value=min_d,max_value=max_d,key="gd");sel_ts=pd.Timestamp(sel_date)
            if sel_ts not in en.index:sel_ts=en.index[en.index.get_indexer([sel_ts],method="nearest")[0]]
            la=en.loc[sel_ts];vn=float(la.get("VIX",15));cn=float(la.get("CCI",0));rn=float(la.get("RSI",50));mn=float(la.get("MDD",0));dn=float(la.get("Disp",0))
            reg=_state("Bull",vn,cn,rn,mn,dn,pt2);cur_sym=ASSET_CLASSES[asset_name]["cur"]
            st.subheader(f"🏠{asset_name}|{sel_ts.date()}|{reg}")
            c1,c2,c3,c4,c5,c6=st.columns(6);c1.metric("종가",f"{cur_sym}{float(la.get('Price',0)):,.2f}");c2.metric("VIX",f"{vn:.1f}");c3.metric("CCI",f"{cn:.0f}");c4.metric("RSI",f"{rn:.0f}");c5.metric("MDD",f"{mn*100:.1f}%");c6.metric("Disp",f"{dn:.1f}")
            with st.expander("📊120일차트",expanded=True):
                cdf=en.loc[:sel_ts].tail(120)
                if not cdf.empty:
                    fig5=make_subplots(rows=3,cols=1,shared_xaxes=True,vertical_spacing=0.05,row_heights=[0.4,0.3,0.3],subplot_titles=["Price","CCI","RSI/VIX"])
                    fig5.add_trace(go.Scatter(x=cdf.index,y=cdf["Price"],name="Price",line=dict(color="white")),row=1,col=1)
                    if "MA_200" in cdf.columns:fig5.add_trace(go.Scatter(x=cdf.index,y=cdf["MA_200"],name="MA200",line=dict(color="#ff9800",dash="dot")),row=1,col=1)
                    fig5.add_trace(go.Scatter(x=cdf.index,y=cdf["CCI"],name="CCI",line=dict(color="#2196f3")),row=2,col=1)
                    fig5.add_trace(go.Scatter(x=cdf.index,y=cdf["RSI"],name="RSI",line=dict(color="#00d084")),row=3,col=1)
                    fig5.add_trace(go.Scatter(x=cdf.index,y=cdf["VIX"],name="VIX",line=dict(color="#ff4444",dash="dot")),row=3,col=1)
                    fig5.update_layout(template=_D,height=500);st.plotly_chart(fig5,use_container_width=True)
            _ai_box("지침",_ai2(reg,mn,vn,cn,rn,dn,pt2),accent="#2196f3")
    except Exception as e:st.error(f"T3:{e}")

# ══════════ Tab4 ══════════
with tab4:
    try:
        wfv_grid={k:(v[:2] if isinstance(v,list) and len(v)>2 else v) for k,v in grid_params.items()}
        if st.button("▶WFV",type="primary",key="bw"):
            prog=st.progress(0);wr=run_wfv(market_df,_BF,annual_budget,wfv_is,wfv_oos,wfv_grid,lambda v:prog.progress(min(v,1.0)),sim_start=f"{start_year}-01-01");prog.empty();st.session_state["wfv"]=wr
        if "wfv" in st.session_state:
            wr=st.session_state["wfv"]
            if wr.get("error"):st.warning(wr["error"])
            elif wr["combined_equity"].empty:st.warning("OOS없음")
            else:
                wm=wr["metrics"];wcs=st.columns(4);wcs[0].metric("연%",f"{wm.get('annual_return',0):.1f}%");wcs[1].metric("MDD",f"{wm.get('mdd',0):.1f}%");wcs[2].metric("Cal",f"{wm.get('calmar',0):.4f}");wcs[3].metric("Sh",f"{wm.get('sharpe',0):.4f}")
                st.plotly_chart(fig_eq(wr["combined_equity"],pd.DataFrame(),f"{asset_name}WFV"),use_container_width=True)
                if wr.get("windows"):
                    with st.expander(f"윈도우({len(wr['windows'])})"):st.dataframe(pd.DataFrame(wr["windows"]),use_container_width=True)
        else:st.info("▶WFV시작")
    except Exception as e:st.error(f"T4:{e}")

# ══════════ Tab5: 8종 비교 ★ ══════════
with tab5:
    try:
        st.subheader("🆚 8종 전략 비교 — 드레인 A/B (Beta + Alpha)")
        st.markdown("""| # | 전략 | 드레인 방식 |
|---|------|-----------|
| 0 | ETF Only | 없음 |
| **1a** | ETF+CMA(기존) | 매번 잔고% 재계산 |
| **1b** | ETF+CMA(v2) | 단계확정→균등분할 |
| 2 | TopN Only | 없음 |
| 3 | TopN+CMA | 기존 |
| **4a** | **ETF→TopN(기존)** | 매번 잔고% 재계산 |
| **4b** | **ETF→TopN(v2)** | 단계확정→균등분할 |""")
        cmp_topn=st.selectbox("TopN",[5,10,15],index=1,key="ctn")
        if st.button("▶ 8종 비교",type="primary",key="bc"):
            p_base={k:(v[0] if isinstance(v,list) else v) for k,v in grid_params.items()};p_base.update(_BF);M=p_base.get("stock_ratio",15)
            cmp_data=fetch_asset(asset_name,fetch_start)
            if end_year<CUR_YEAR:cmp_data=cmp_data[cmp_data.index<=pd.Timestamp(fetch_end)]
            sclose,spy=fetch_stocks(fetch_start)
            if end_year<CUR_YEAR:sclose=sclose[sclose.index<=pd.Timestamp(fetch_end)]
            ss=f"{start_year}-01-01";R={}
            if not cmp_data.empty:
                with st.spinner("0"):R["0.ETF Only"]=run_beta(cmp_data,{**p_base,"stock_ratio":18},annual_budget,sim_start=ss)
                with st.spinner("1a"):R["1a.ETF+CMA(기존)"]=run_beta(cmp_data,p_base,annual_budget,sim_start=ss)
                with st.spinner("1b"):R["1b.ETF+CMA(v2)"]=run_beta_v2(cmp_data,p_base,annual_budget,sim_start=ss)
                if not sclose.empty:
                    with st.spinner("2"):R["2.TopN Only"]=run_alpha(cmp_data,sclose,spy,{**p_base,"stock_ratio":0,"top_n":cmp_topn},annual_budget,alpha_dca_ratio=1.0,sim_start=ss)
                    with st.spinner("3"):R["3.TopN+CMA"]=run_alpha(cmp_data,sclose,spy,{**p_base,"stock_ratio":0,"top_n":cmp_topn},annual_budget,alpha_dca_ratio=M/18,sim_start=ss)
                    with st.spinner("4a"):R["4a.ETF→TopN(기존)"]=run_alpha(cmp_data,sclose,spy,{**p_base,"top_n":cmp_topn},annual_budget,alpha_dca_ratio=0.0,sim_start=ss)
                    with st.spinner("4b"):R["4b.ETF→TopN(v2)"]=run_alpha_v2(cmp_data,sclose,spy,{**p_base,"top_n":cmp_topn},annual_budget,alpha_dca_ratio=0.0,sim_start=ss)
                st.session_state["cmp"]=R
        if "cmp" in st.session_state:
            R=st.session_state["cmp"]
            cm={"0.ETF Only":"#00d084","1a.ETF+CMA(기존)":"#2196f3","1b.ETF+CMA(v2)":"#e91e63","2.TopN Only":"#ff9800","3.TopN+CMA":"#ff6b6b","4a.ETF→TopN(기존)":"#ab47bc","4b.ETF→TopN(v2)":"#00bcd4"}
            f=go.Figure()
            for n,r in R.items():
                if r and not r["equity_curve"].empty:eq=r["equity_curve"];f.add_trace(go.Scatter(x=eq.index,y=eq["yj_val"]/1e8,name=n,line=dict(color=cm.get(n,"#aaa"),width=2.5)))
            f.update_layout(title=f"{asset_name} 8종 — 1a/1b + 4a/4b 주목",template=_D,height=520);st.plotly_chart(f,use_container_width=True)
            rows=[]
            for n,r in R.items():
                m=r.get("metrics",{});rs=r.get("regime_stats",{})
                rows.append({"전략":n,"총%":m.get("total_return",0),"연%":m.get("annual_return",0),"MDD%":m.get("mdd",0),"Sharpe":m.get("sharpe",0),"Calmar":m.get("calmar",0),"최종(억)":round(m.get("final_value",0)/1e8,2),"P매수(만)":rs.get("P총(만)",rs.get("Panic매수(만)","-"))})
            st.dataframe(pd.DataFrame(rows),use_container_width=True)
            for n in ["1a.ETF+CMA(기존)","1b.ETF+CMA(v2)","4a.ETF→TopN(기존)","4b.ETF→TopN(v2)"]:
                r=R.get(n)
                if r and r.get("panic_logs"):
                    with st.expander(f"🔴{n} Panic({len(r['panic_logs'])})"):st.dataframe(pd.DataFrame(r["panic_logs"]),use_container_width=True)
            _ai_box("8종비교",_ai5(R),accent="#ab47bc")
        else:st.info("▶ 시작하세요")
    except Exception as e:st.error(f"T5:{e}")

# ══════════ Tab6 ══════════
with tab6:
    try:
        oh_in=st.text_input("종목",",".join(TOP10.get(CUR_YEAR,TOP10[max(TOP10)])[:8]),key="oh")
        if st.button("▶과열",type="primary",key="bo"):
            tks=[t.strip().upper() for t in oh_in.split(",") if t.strip()];ohr=[]
            for t in tks:
                r=analyze_oh(t)
                if r:ohr.append(r)
            st.session_state["ohr"]=ohr
        if "ohr" in st.session_state and st.session_state["ohr"]:
            ohr=st.session_state["ohr"];odf=pd.DataFrame(ohr);st.dataframe(odf,use_container_width=True)
        st.markdown("---")
        rv_in=st.text_input("비교","AAPL,MSFT,GOOGL,AMZN,NVDA,META,TSLA",key="rv");rv_p=st.selectbox("기간",["3mo","6mo","12mo","24mo"],index=2,key="rvp")
        if st.button("▶저평가",type="primary",key="brv"):
            tks=[t.strip().upper() for t in rv_in.split(",") if t.strip()]
            with st.spinner("..."):l1,fd,norm=analyze_rv(tks,rv_p)
            if l1 is not None:st.session_state["rv_l1"]=l1;st.session_state["rv_fd"]=fd
        if "rv_l1" in st.session_state:st.dataframe(st.session_state["rv_l1"],use_container_width=True)
        if "rv_fd" in st.session_state and st.session_state["rv_fd"] is not None:st.dataframe(st.session_state["rv_fd"],use_container_width=True)
    except Exception as e:st.error(f"T6:{e}")

# ══════════ Tab7 ══════════
with tab7:
    try:
        if "bt" not in st.session_state or st.session_state["bt"]["equity_curve"].empty:st.warning("백테스트먼저")
        else:
            fc=st.columns(3);sy=fc[0].selectbox("기간",[1,2,3,5,7,10],index=2);ns=fc[1].selectbox("횟수",[500,1000,2000],index=1);sm=fc[2].selectbox("방법",["몬테카를로","블록부트스트랩"])
            if st.button("▶시뮬",type="primary",key="bm"):
                with st.spinner("..."):sim=mc_sim(st.session_state["bt"]["equity_curve"],annual_budget,sy,ns) if sm=="몬테카를로" else boot_sim(st.session_state["bt"]["equity_curve"],annual_budget,sy,ns)
                if sim:st.session_state["sim"]=sim;st.session_state["sm"]=sm
            if "sim" in st.session_state:
                sim=st.session_state["sim"];mn2=st.session_state.get("sm","");cv=sim['current_val'];yrs=sim['years']
                prows=[{"p":f"{p}%","자산성장(%)":round((sim["percentiles"][f"p{p}"]/cv-1)*100,1),"연환산(%)":round(((sim["percentiles"][f"p{p}"]/cv)**(1/yrs)-1)*100 if cv>0 else 0,1),"최종(억)":round(sim["percentiles"][f"p{p}"]/1e8,2)} for p in [5,10,25,50,75,90,95]]
                st.dataframe(pd.DataFrame(prows),use_container_width=True)
                tp=sim["target_probs"];tpc=st.columns(len(tp))
                for i,(k,v) in enumerate(tp.items()):tpc[i].metric(k,f"{'🟢' if v>=50 else '🟡' if v>=20 else '🔴'}{v}%")
                st.plotly_chart(fig_mc_p(sim,mn2),use_container_width=True);st.plotly_chart(fig_mc_h(sim,mn2),use_container_width=True)
                _ai_box("미래",_ai7(sim,yrs,mn2),accent="#ffd700")
    except Exception as e:st.error(f"T7:{e}")