import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output
import calendar

# ═══════════════════════════════════════════════════════════
# 1.  SRO CODE → FULL NAME
# ═══════════════════════════════════════════════════════════
SRO_CODE_TO_NAME = {
    'AGR':'Agra','AGT':'Agartala','AHM':'Ahmedabad','AJM':'Ajmer','ALD':'Allahabad',
    'ALG':'Aligarh','AMB':'Ambala','ARG':'Aurangabad','AZM':'Azamgarh','BBS':'Baripada',
    'BDW':'Bankura','BHP':'Berhampur','BNG':'Bangalore','BNK':'Barddhaman','BRD':'Bhubaneswar',
    'BRL':'Bareilly','BVN':'Bhavnagar','CHD':'Chandigarh','CHN':'Chennai','CMB':'Coimbatore',
    'CSR':'Chinsura','CTC':'Cuttack','CUD':'Cuddalore','DBR':'Dibrugarh','DEL':'Delhi',
    'DRP':'Dharmapuri','FBD':'Faridabad','FZD':'Faizabad','GKP':'Gorakhpur','GTK':'Gangtok',
    'HSR':'Hisar','HWH':'Howrah','JDP':'Jodhpur','JLG':'Jalgaon','JMN':'Jamnagar',
    'JRT':'Jorhat','KLK':'Kolkata','KNL':'Karnal','MBD':'Moradabad','MDN':'Medinipur',
    'MMB':'Mumbai','MNG':'Mangalore','MRT':'Meerut','MSR':'Mysore','NND':'Nanded',
    'NSK':'Nashik','PDC':'Puducherry','RJK':'Rajkot','RTK':'Rohtak','SDN':'Surendranagar',
    'SLM':'Salem','SMG':'Shimoga','SRN':'Saharanpur','STP':'Sitapur','THN':'Thane',
    'TRC':'Tiruchirappalli','TZP':'Tezpur','UDP':'Udaipur','VLR':'Vellore','VNS':'Varanasi',
}

# ═══════════════════════════════════════════════════════════
# 2.  LOAD & CLEAN
# ═══════════════════════════════════════════════════════════
df = pd.read_excel('PLFS_FSU_Completion_History_Summary_Analyzed.xlsx')
df = df.dropna(subset=['FSU'])
df['FSU']       = df['FSU'].astype(str).str.strip()
df['Area Type'] = df['Area Type'].astype(str).str.strip().str.capitalize()
df['Zone']      = df['Zone'].astype(str).str.strip()
df['Ro']        = df['Ro'].astype(str).str.strip().replace(
                    {'Alllahabad':'Allahabad','Bhubeneswar':'Bhubaneswar',
                     'Burdwan':'Barddhaman','Calcutta':'Kolkata'})
df['Sro']       = df['Sro'].astype(str).str.strip()
df['Sro_Name']  = df['Sro'].map(SRO_CODE_TO_NAME).fillna(df['Sro'])

ALL_DATE_COLS = [
    'Sample Uploaded','Assigned to ENM',
    'First ENM to SUP','Latest ENM to SUP',
    'First Return ENM to SUP','Latest Return ENM to SUP',
    'First SUP to DS','Latest SUP to DS',
    'First Return SUP to DS','Latest Return SUP to DS',
    'First DS Acceptance','Latest DS Acceptance','Last Update'
]
for col in ALL_DATE_COLS:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

df = df.sort_values('Last Update').drop_duplicates(subset=['FSU'], keep='last')

# ── Main dashboard flags ────────────────────────────────────
FLAG_ONEGO = 'One-Go Completion'
FLAG_DQ    = 'Potential Data Quality Issue (ENM/SUP)'
FLAG_SUP   = 'Potential SUP Oversight (DS Rejected after SUP Approval)'
df['SUP_Stuck']    = ((df[FLAG_SUP]==1)&(df['FSU Final Status']=='RETURN TO SUPERVISOR BY DS')).astype(int)
df['SUP_Resolved'] = ((df[FLAG_SUP]==1)&(df['FSU Final Status']!='RETURN TO SUPERVISOR BY DS')).astype(int)

# ── Paradata holding-time metrics ──────────────────────────
# All times clamped to >=0 (negative means data entry anomaly)
def ht(a, b):
    d = (df[b] - df[a]).dt.days
    return d.where(d >= 0)   # NaN if negative

df['ENM_HT']        = ht('Assigned to ENM',        'First ENM to SUP')
df['SUP_HT_First']  = ht('First ENM to SUP',        'First SUP to DS')
df['SUP_HT_Refer']  = ht('Latest SUP to DS',        'First Return SUP to DS')
df['ENM_HT_Refer']  = ht('Latest ENM to SUP',       'First Return ENM to SUP')
df['SUP_HT_Clarif'] = ht('First Return SUP to DS',  'Latest Return SUP to DS')

HT_COLS = {
    'ENM_HT':       'ENM Holding (After Fieldwork)',
    'SUP_HT_First': 'SUP Holding (1st Submission)',
    'SUP_HT_Refer': 'SUP Holding (Refer Back by DS)',
    'ENM_HT_Refer': 'ENM Holding (Refer Back by SUP)',
    'SUP_HT_Clarif':'SUP Holding (After Clarification)',
}

# ── Paradata weekly submission columns ─────────────────────
df['Week_Label'] = df['First SUP to DS'].dt.strftime('%G-W%V')
df['Week_Num']   = df['First SUP to DS'].dt.isocalendar().week.astype('Int64')

# ── Span filter option builders ────────────────────────────
_span = df['Assigned to ENM'].dropna()
YEAR_OPTIONS  = [{'label':'All Years',  'value':'all'}] + \
                [{'label':str(y),'value':int(y)} for y in sorted(_span.dt.year.unique())]
MONTH_OPTIONS = [{'label':'All Months','value':'all'}] + \
                [{'label':calendar.month_name[m],'value':int(m)} for m in sorted(_span.dt.month.unique())]
WEEK_OPTIONS  = [{'label':'All Weeks', 'value':'all'}] + \
                [{'label':f'Week {w}','value':int(w)} for w in sorted(_span.dt.isocalendar().week.dropna().unique())]

def apply_span(fdf, year, month, week):
    s = fdf['Assigned to ENM']
    if year  not in (None,'all'): fdf = fdf[s.dt.year == int(year)];   s = fdf['Assigned to ENM']
    if month not in (None,'all'): fdf = fdf[s.dt.month == int(month)]; s = fdf['Assigned to ENM']
    if week  not in (None,'all'):
        iso_week = s.dt.isocalendar().week  # nullable UInt32; compare before casting
        fdf = fdf[iso_week.eq(int(week))]
    return fdf

print(f"✓ {len(df)} unique FSUs | SROs mapped: {df['Sro_Name'].nunique()}")

# ═══════════════════════════════════════════════════════════
# 3.  APP
# ═══════════════════════════════════════════════════════════
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

def make_dd(id_, opts, placeholder, multi=True):
    clean = sorted([v for v in set(opts) if str(v).lower() not in ('nan','','nat')])
    return dcc.Dropdown(id=id_,
        options=[{'label':str(v),'value':v} for v in clean],
        multi=multi, placeholder=placeholder, style={'fontSize':'12px'})

# ── Shared filter bar (reused across both tabs) ────────────
FILTER_BAR = html.Div([
    # Row 1
    html.Div([
        html.Div([
            html.Label(" Year:"),
            dcc.Dropdown(id='year-dd', options=YEAR_OPTIONS, value='all',
                         clearable=False, style={'fontSize':'12px'})
        ], style={'flex':1,'padding':'0 6px'}),
        html.Div([
            html.Label("Month:"),
            dcc.Dropdown(id='month-dd', options=MONTH_OPTIONS, value='all',
                         clearable=False, style={'fontSize':'12px'})
        ], style={'flex':1,'padding':'0 6px'}),
        html.Div([
            html.Label("Week:"),
            dcc.Dropdown(id='week-dd', options=WEEK_OPTIONS, value='all',
                         clearable=False, style={'fontSize':'12px'})
        ], style={'flex':1,'padding':'0 6px'}),
        html.Div([
            html.Label("Zone:"),
            make_dd('zone-dd', df['Zone'].dropna().unique(), "All Zones")
        ], style={'flex':1,'padding':'0 6px'}),
        html.Div([
            html.Label("Area Type:"),
            make_dd('area-dd', df['Area Type'].dropna().unique(), "All Area Types")
        ], style={'flex':1,'padding':'0 6px'}),
        html.Div([
            html.Label("FSU Final Status:"),
            make_dd('status-dd', df['FSU Final Status'].dropna().unique(), "All Statuses")
        ], style={'flex':2,'padding':'0 6px'}),
    ], style={'display':'flex','alignItems':'flex-end','marginBottom':'10px'}),
    # Row 2
    html.Div([
        html.Div([
            html.Label("RO:"),
            make_dd('ro-dd', df['Ro'].dropna().unique(), "All ROs")
        ], style={'flex':1,'padding':'0 6px'}),
        html.Div([
            html.Label("SRO:"),
            make_dd('sro-dd', df['Sro_Name'].dropna().unique(), "All SROs")
        ], style={'flex':4,'padding':'0 6px'}),
    ], style={'display':'flex','alignItems':'flex-end'}),
], style={'backgroundColor':'#fff','padding':'14px','borderRadius':'8px',
          'boxShadow':'0 2px 4px rgba(0,0,0,.1)','marginBottom':'16px'})

# ── Tab 1: Main Dashboard ──────────────────────────────────
TAB_MAIN = html.Div([
    # KPI Cards
    html.Div([
        html.Div([html.H3("Total Unique FSUs"),   html.H2(id='kpi-total')],  className="kpi-card"),
        html.Div([html.H3("One-Go Completions"),  html.H2(id='kpi-onego')],  className="kpi-card"),
        html.Div([html.H3("Data Quality Issues"), html.H2(id='kpi-dq')],     className="kpi-card"),
        html.Div([
            html.H3("SUP Oversight — Stuck", style={'color':'#c0392b','fontSize':'13px'}),
            html.H2(id='kpi-stuck', style={'color':'#c0392b'}),
            html.P("Final Status = RETURN TO SUP BY DS",
                   style={'fontSize':'11px','color':'#888','margin':'0'})
        ], className="kpi-card"),
        html.Div([
            html.H3("SUP Oversight — Progressed", style={'color':'#e67e22','fontSize':'13px'}),
            html.H2(id='kpi-resolved', style={'color':'#e67e22'}),
            html.P("DS rejected, later resubmitted",
                   style={'fontSize':'11px','color':'#888','margin':'0'})
        ], className="kpi-card"),
    ], className="kpi-container", style={'marginBottom':'16px'}),

    html.Div([dcc.Graph(id='status-chart')],   className="chart-row"),
    html.Div([dcc.Graph(id='flags-chart')],    className="chart-row"),
    html.Div([
        html.H3("SUP Oversight Split", style={'textAlign':'center','color':'#1a2e4a','margin':'0 0 4px'}),
        html.P("'Currently Stuck' = Final Status still RETURN TO SUPERVISOR BY DS. "
               "'Progressed' = DS rejected but FSU later moved on.",
               style={'fontSize':'13px','color':'#555','margin':'0 0 8px'}),
        dcc.Graph(id='sup-split-chart'),
    ], className="chart-row", style={'border':'2px solid #e74c3c'}),
    html.Div([dcc.Graph(id='resub-chart')],    className="chart-row"),
    html.Div([dcc.Graph(id='warnings-chart')], className="chart-row"),

    # FSU Lifecycle
    html.Div([
        html.H3("FSU Lifecycle Tracker", style={'textAlign':'center','color':'#333','margin':'0 0 8px'}),
        make_dd('fsu-dd', df['FSU'].unique(), "Select FSU ID…", multi=False),
        dcc.Graph(id='fsu-lifecycle'),
    ], className="chart-row", style={'border':'2px solid #007bff','marginTop':'16px'}),
])

# ── Tab 2: Para Data Analysis ──────────────────────────────
TAB_PARA = html.Div([

    # Para KPI row
    html.Div([
        html.Div([html.H3("FSUs with\nHolding Data"), html.H2(id='p-kpi-total')], className="kpi-card"),
        html.Div([html.H3("Avg ENM\nHolding (days)"), html.H2(id='p-kpi-enm',   style={'color':'#2980b9'})], className="kpi-card"),
        html.Div([html.H3("Avg SUP\n1st Submission"), html.H2(id='p-kpi-sup1',  style={'color':'#27ae60'})], className="kpi-card"),
        html.Div([html.H3("Avg SUP\nRefer Back"),     html.H2(id='p-kpi-sup2',  style={'color':'#e67e22'})], className="kpi-card"),
        html.Div([html.H3("Avg ENM\nRefer Back"),     html.H2(id='p-kpi-enm2',  style={'color':'#8e44ad'})], className="kpi-card"),
        html.Div([html.H3("Avg SUP\nAfter Clarif."),  html.H2(id='p-kpi-sup3',  style={'color':'#c0392b'})], className="kpi-card"),
    ], className="kpi-container", style={'marginBottom':'16px'}),

    # Chart 1: ENM Holding time bar (SRO-wise, sorted)
    html.Div([
        html.H3("① ENM Holding Time after Fieldwork Completion (SRO-wise)",
                style={'color':'#1a2e4a','margin':'0 0 4px'}),
        html.P("Guideline: ENM should submit within 1 day of completing all ESU schedules.",
               style={'fontSize':'12px','color':'#e74c3c','margin':'0 0 8px'}),
        dcc.Graph(id='p-enm-ht'),
    ], className="chart-row"),

    # Chart 2: SUP First Holding time bar (SRO-wise, sorted)
    html.Div([
        html.H3("② SUP Holding Time — First Submission SUP→DS (SRO-wise)",
                style={'color':'#1a2e4a','margin':'0 0 4px'}),
        html.P("Guideline: Supervisor should submit within 3 days of receiving from Enumerator.",
               style={'fontSize':'12px','color':'#e74c3c','margin':'0 0 8px'}),
        dcc.Graph(id='p-sup-ht'),
    ], className="chart-row"),

    # Chart 3: All 5 holding parameters grouped (SRO-wise)
    html.Div([
        html.H3("③ RO/SRO-wise Holding Status at All Levels",
                style={'color':'#1a2e4a','margin':'0 0 4px'}),
        html.P("Comparison of all 5 holding parameters per SRO.",
               style={'fontSize':'12px','color':'#555','margin':'0 0 8px'}),
        dcc.Graph(id='p-all-ht'),
    ], className="chart-row"),

    # Chart 4: Ranking table
    html.Div([
        html.H3("④ SRO Ranking — Based on Total Holding Time",
                style={'color':'#1a2e4a','margin':'0 0 4px'}),
        html.P("Rank 1 = least total holding time (best performance). "
               "Score = sum of all 5 average holding parameters.",
               style={'fontSize':'12px','color':'#555','margin':'0 0 8px'}),
        dcc.Graph(id='p-ranking-chart'),
    ], className="chart-row"),

    # Chart 5: Weekly FSU Submission flow
    html.Div([
        html.H3("⑤ Weekly FSU Submission Flow (SRO-wise)",
                style={'color':'#1a2e4a','margin':'0 0 4px'}),
        html.P("Submissions should be evenly distributed throughout the month. "
               "Heavy last-week skew increases DS burden and risks data quality.",
               style={'fontSize':'12px','color':'#e74c3c','margin':'0 0 8px'}),
        dcc.Graph(id='p-weekly-flow'),
    ], className="chart-row"),

    # Chart 6: Weekly submission heatmap
    html.Div([
        html.H3("⑥ Submission Skew Heatmap — Week × SRO",
                style={'color':'#1a2e4a','margin':'0 0 4px'}),
        html.P("Darker = more FSUs submitted that week. Ideal = uniform shade across all weeks.",
               style={'fontSize':'12px','color':'#555','margin':'0 0 8px'}),
        dcc.Graph(id='p-heatmap'),
    ], className="chart-row"),

    # Chart 7: Inspection / Visit type
    html.Div([
        html.H3("⑦ First Visit (FV) vs Repeat Visit (RV) Distribution (SRO-wise)",
                style={'color':'#1a2e4a','margin':'0 0 4px'}),
        html.P("Based on Max Visit Number: 1 = FV, >1 = RV.",
               style={'fontSize':'12px','color':'#555','margin':'0 0 8px'}),
        dcc.Graph(id='p-visit-chart'),
    ], className="chart-row"),
])

# ── Root layout ────────────────────────────────────────────
app.layout = html.Div([
    html.Div([
        html.H1("PLFS Field Operations Dashboard",
                style={'color':'#1a2e4a','margin':'0','display':'inline-block'}),
        html.Span(" — Real-time Para Data Analysis",
                  style={'color':'#7f8c8d','fontSize':'16px','marginLeft':'10px'}),
    ], style={'marginBottom':'12px'}),

    FILTER_BAR,

    dcc.Tabs(id='main-tabs', value='tab-main', children=[
        dcc.Tab(label='Field Operations Overview', value='tab-main',
                style={'fontWeight':'bold'}, selected_style={'fontWeight':'bold','borderTop':'3px solid #007bff'}),
        dcc.Tab(label='Para Data Analysis', value='tab-para',
                style={'fontWeight':'bold'}, selected_style={'fontWeight':'bold','borderTop':'3px solid #e74c3c'}),
    ], style={'marginBottom':'16px'}),

    # Both tab panels always in DOM; visibility toggled via clientside callback
    html.Div(TAB_MAIN, id='panel-main', style={'display':'block'}),
    html.Div(TAB_PARA, id='panel-para', style={'display':'none'}),
    html.Div(id='_css', children=html.Div(), style={'display':'none'}),

], style={'fontFamily':'Arial,sans-serif','padding':'20px','backgroundColor':'#f4f6f8'})

app.clientside_callback(
    """function(){
        var s=document.createElement('style');
        s.innerHTML=`
          .kpi-container{display:flex;justify-content:space-around;flex-wrap:wrap;gap:8px}
          .kpi-card{background:#fff;border-radius:8px;padding:14px;
                    box-shadow:0 2px 4px rgba(0,0,0,.1);text-align:center;min-width:130px;flex:1}
          .kpi-card h3{margin:0 0 4px;color:#555;font-size:12px;line-height:1.3}
          .kpi-card h2{margin:0;color:#2c3e50;font-size:1.8rem}
          .chart-row{background:#fff;margin-top:16px;padding:14px;border-radius:8px;
                     box-shadow:0 2px 4px rgba(0,0,0,.1)}
        `;
        document.head.appendChild(s);return'';}""",
    Output('_css','children'), Input('_css','id')
)

# ── Tab switcher (clientside: show/hide, never unmount) ───
app.clientside_callback(
    """
    function(tab) {
        var main = document.getElementById('panel-main');
        var para = document.getElementById('panel-para');
        if (!main || !para) return window.dash_clientside.no_update;
        main.style.display = (tab === 'tab-main') ? 'block' : 'none';
        para.style.display = (tab === 'tab-para')  ? 'block' : 'none';
        return window.dash_clientside.no_update;
    }
    """,
    Output('panel-main', 'style'),
    Input('main-tabs', 'value')
)

# ═══════════════════════════════════════════════════════════
# 4.  SHARED FILTER HELPER
# ═══════════════════════════════════════════════════════════
FILTER_INPUTS = [
    Input('year-dd','value'), Input('month-dd','value'), Input('week-dd','value'),
    Input('zone-dd','value'), Input('area-dd','value'),  Input('status-dd','value'),
    Input('ro-dd','value'),   Input('sro-dd','value'),
]

def filter_df(year, month, week, zones, areas, statuses, ros, sros):
    fdf = df.copy()
    fdf = apply_span(fdf, year, month, week)
    if zones:    fdf = fdf[fdf['Zone'].isin(zones)]
    if areas:    fdf = fdf[fdf['Area Type'].isin(areas)]
    if statuses: fdf = fdf[fdf['FSU Final Status'].isin(statuses)]
    if ros:      fdf = fdf[fdf['Ro'].isin(ros)]
    if sros:     fdf = fdf[fdf['Sro_Name'].isin(sros)]
    return fdf

COLORS = {'Rural':'#2196F3','Urban':'#FF9800'}
HT_COLORS = ['#2980b9','#27ae60','#e67e22','#8e44ad','#c0392b']

# ═══════════════════════════════════════════════════════════
# 5.  MAIN TAB CALLBACK
# ═══════════════════════════════════════════════════════════
@app.callback(
    [Output('kpi-total','children'), Output('kpi-onego','children'),
     Output('kpi-dq','children'),    Output('kpi-stuck','children'),
     Output('kpi-resolved','children'),
     Output('status-chart','figure'), Output('flags-chart','figure'),
     Output('sup-split-chart','figure'),
     Output('resub-chart','figure'),  Output('warnings-chart','figure'),
     Output('fsu-dd','options')],
    FILTER_INPUTS,
    prevent_initial_call=False
)
def update_main(year, month, week, zones, areas, statuses, ros, sros):
    fdf = filter_df(year, month, week, zones, areas, statuses, ros, sros)

    total    = len(fdf)
    one_go   = int(fdf[FLAG_ONEGO].sum()) if FLAG_ONEGO in fdf.columns else 0
    dq       = int(fdf[FLAG_DQ].sum())    if FLAG_DQ    in fdf.columns else 0
    stuck    = int(fdf['SUP_Stuck'].sum())
    resolved = int(fdf['SUP_Resolved'].sum())
    fsu_opts = [{'label':str(f),'value':f} for f in sorted(fdf['FSU'].unique())]

    # Status chart
    sc = fdf.groupby(['FSU Final Status','Area Type']).size().reset_index(name='FSU Count')
    fig1 = px.bar(sc, x='FSU Final Status', y='FSU Count', color='Area Type',
                  barmode='group', title='Unique FSUs by Final Status',
                  color_discrete_map=COLORS, text='FSU Count', height=480)
    fig1.update_traces(textposition='outside')
    fig1.update_layout(xaxis_tickangle=-30, margin=dict(t=40,b=10))

    # Flags chart
    lmap = {FLAG_ONEGO:'One-Go Completion',FLAG_DQ:'Data Quality Issue',FLAG_SUP:'SUP Oversight (all)'}
    rows = []
    for flag in [FLAG_ONEGO,FLAG_DQ,FLAG_SUP]:
        if flag in fdf.columns:
            g = fdf[fdf[flag]==1].groupby('Area Type').size().reset_index(name='Unique FSU Count')
            g['Flag'] = lmap[flag]; rows.append(g)
    if rows:
        fd = pd.concat(rows, ignore_index=True)
        fig2 = px.bar(fd, x='Flag', y='Unique FSU Count', color='Area Type',
                      barmode='group', title='Unique FSUs by Issue Flag',
                      color_discrete_map=COLORS, text='Unique FSU Count', height=420)
        fig2.update_traces(textposition='outside')
    else:
        fig2 = go.Figure().update_layout(title="No flag data")

    # SUP split chart
    split_rows = []
    for col, lbl in [('SUP_Stuck','Currently Stuck\n(RETURN TO SUP BY DS)'),
                     ('SUP_Resolved','Progressed After\nDS Rejection')]:
        g = fdf[fdf[col]==1].groupby('Area Type').size().reset_index(name='Unique FSU Count')
        g['Sub-Group']=lbl; split_rows.append(g)
    sp = pd.concat(split_rows, ignore_index=True)
    fig3 = px.bar(sp, x='Sub-Group', y='Unique FSU Count', color='Area Type',
                  barmode='group', title='SUP Oversight: Stuck vs Progressed',
                  color_discrete_map=COLORS, text='Unique FSU Count', height=420)
    fig3.update_traces(textposition='outside')

    # Resubmissions
    sc4='No of repeat submissions to SUP'; dc4='No of repeat submissions to DS'
    if sc4 in fdf.columns and dc4 in fdf.columns:
        as_ = fdf.groupby(['Ro','Area Type'])[sc4].mean().reset_index(name='Avg to SUP')
        ad  = fdf.groupby(['Ro','Area Type'])[dc4].mean().reset_index(name='Avg to DS')
        fig4 = make_subplots(rows=1,cols=2,subplot_titles=('Avg Repeat Sub to SUP','Avg Repeat Sub to DS'))
        seen=set()
        for area in as_['Area Type'].unique():
            show=area not in seen; seen.add(area)
            ss=as_[as_['Area Type']==area]; sd=ad[ad['Area Type']==area]
            fig4.add_trace(go.Bar(x=ss['Ro'],y=ss['Avg to SUP'],name=area,
                                  marker_color=COLORS.get(area,'grey'),
                                  legendgroup=area,showlegend=show),row=1,col=1)
            fig4.add_trace(go.Bar(x=sd['Ro'],y=sd['Avg to DS'],name=area,
                                  marker_color=COLORS.get(area,'grey'),
                                  legendgroup=area,showlegend=False),row=1,col=2)
        fig4.update_layout(height=480,barmode='group',
                           title_text='Average Repeat Submissions by RO')
    else:
        fig4 = go.Figure().update_layout(title="Resubmissions data not available")

    # Warnings
    if 'No of Warnings' in fdf.columns:
        wd = fdf[fdf['No of Warnings'].notna()].copy()
        fig5 = px.box(wd, x='Area Type', y='No of Warnings', color='Zone',
                      title=f'Warnings Distribution ({len(wd)} of {total} FSUs)',
                      height=480, points='outliers')
    else:
        fig5 = go.Figure().update_layout(title="Warnings data not available")

    return (str(total),str(one_go),str(dq),str(stuck),str(resolved),
            fig1,fig2,fig3,fig4,fig5,fsu_opts)

# ── FSU Lifecycle ───────────────────────────────────────────
@app.callback(Output('fsu-lifecycle','figure'), Input('fsu-dd','value'))
def lifecycle(fsu):
    if not fsu:
        return go.Figure().update_layout(title="Select an FSU ID to view its timeline.")
    life = df[df['FSU']==fsu].melt(
        id_vars=['FSU'],
        value_vars=[c for c in ALL_DATE_COLS if c in df.columns],
        var_name='Stage',value_name='Date'
    ).dropna(subset=['Date']).sort_values('Date')
    if life.empty:
        return go.Figure().update_layout(title=f"No date data for FSU {fsu}")
    fig = px.line(life,x='Date',y='Stage',markers=True,title=f'Timeline — FSU: {fsu}')
    fig.update_traces(marker=dict(size=12,color='#ff7f0e'),line=dict(color='#1f77b4',width=3))
    fig.update_layout(yaxis={'categoryorder':'array','categoryarray':ALL_DATE_COLS[::-1]},
                      height=420,margin=dict(l=20,r=20,t=50,b=20))
    return fig

# ═══════════════════════════════════════════════════════════
# 6.  PARA DATA TAB CALLBACK
# ═══════════════════════════════════════════════════════════
@app.callback(
    [Output('p-kpi-total','children'), Output('p-kpi-enm','children'),
     Output('p-kpi-sup1','children'),  Output('p-kpi-sup2','children'),
     Output('p-kpi-enm2','children'),  Output('p-kpi-sup3','children'),
     Output('p-enm-ht','figure'),      Output('p-sup-ht','figure'),
     Output('p-all-ht','figure'),      Output('p-ranking-chart','figure'),
     Output('p-weekly-flow','figure'), Output('p-heatmap','figure'),
     Output('p-visit-chart','figure')],
    FILTER_INPUTS,
    prevent_initial_call=False
)
def update_para(year, month, week, zones, areas, statuses, ros, sros):
    fdf = filter_df(year, month, week, zones, areas, statuses, ros, sros)

    # ── Para KPIs ───────────────────────────────────────────
    ht_data = fdf[fdf['ENM_HT'].notna()]
    p_total = len(ht_data)
    def avg(col): return f"{ht_data[col].mean():.2f}" if p_total>0 and col in ht_data.columns else "—"

    # ── SRO-wise averages for all HT metrics ────────────────
    ht_cols_list = list(HT_COLS.keys())
    sro_ht = (fdf.groupby('Sro_Name')[ht_cols_list]
                 .mean()
                 .round(2)
                 .reset_index())
    sro_ht.columns = ['SRO'] + [HT_COLS[c] for c in ht_cols_list]
    sro_ht['Total Score'] = sro_ht[[HT_COLS[c] for c in ht_cols_list]].sum(axis=1).round(2)
    sro_ht = sro_ht.sort_values('Total Score')
    sro_ht['Rank'] = range(1, len(sro_ht)+1)

    enm_col  = HT_COLS['ENM_HT']
    sup1_col = HT_COLS['SUP_HT_First']

    # ── Chart 1: ENM Holding Time (sorted ascending) ────────
    s1 = sro_ht.sort_values(enm_col, na_position='last')
    fig_enm = go.Figure(go.Bar(
        x=s1['SRO'], y=s1[enm_col],
        marker_color=['#e74c3c' if v and v > 1 else '#27ae60'
                      for v in s1[enm_col]],
        text=s1[enm_col].round(2), textposition='outside'
    ))
    fig_enm.add_hline(y=1, line_dash='dash', line_color='red',
                      annotation_text='Guideline: 1 day', annotation_position='top left')
    fig_enm.update_layout(
        title='ENM Avg Holding Time after Fieldwork Completion (days, SRO-wise)',
        xaxis_tickangle=-45, yaxis_title='Days', height=500,
        xaxis_title='SRO', margin=dict(t=50,b=120)
    )

    # ── Chart 2: SUP First Holding Time ─────────────────────
    s2 = sro_ht.sort_values(sup1_col, na_position='last')
    fig_sup = go.Figure(go.Bar(
        x=s2['SRO'], y=s2[sup1_col],
        marker_color=['#e74c3c' if v and v > 3 else '#27ae60'
                      for v in s2[sup1_col]],
        text=s2[sup1_col].round(2), textposition='outside'
    ))
    fig_sup.add_hline(y=3, line_dash='dash', line_color='red',
                      annotation_text='Guideline: 3 days', annotation_position='top left')
    fig_sup.update_layout(
        title='SUP Avg Holding Time — First Submission SUP→DS (days, SRO-wise)',
        xaxis_tickangle=-45, yaxis_title='Days', height=500,
        xaxis_title='SRO', margin=dict(t=50,b=120)
    )

    # ── Chart 3: All 5 parameters grouped by SRO ────────────
    ht_long = sro_ht.sort_values('Total Score').melt(
        id_vars=['SRO'],
        value_vars=[HT_COLS[c] for c in ht_cols_list],
        var_name='Metric', value_name='Days'
    )
    fig_all = px.bar(
        ht_long, x='SRO', y='Days', color='Metric', barmode='group',
        title='All Holding Parameters by SRO',
        color_discrete_sequence=HT_COLORS,
        height=520
    )
    fig_all.update_layout(
        xaxis_tickangle=-45, legend=dict(orientation='h', y=1.12),
        margin=dict(t=80,b=120)
    )

    # ── Chart 4: Ranking bar (horizontal) ───────────────────
    rank_df = sro_ht.sort_values('Total Score')
    fig_rank = go.Figure(go.Bar(
        y=rank_df['SRO'], x=rank_df['Total Score'],
        orientation='h',
        text=[f"Rank {r} | {s:.2f} days"
              for r, s in zip(rank_df['Rank'], rank_df['Total Score'])],
        textposition='inside', insidetextanchor='start',
        marker=dict(
            color=rank_df['Total Score'],
            colorscale='RdYlGn',
            reversescale=True,
            showscale=True,
            colorbar=dict(title='Total Days')
        )
    ))
    fig_rank.update_layout(
        title='SRO Ranking — Total Holding Score (lower = better, Rank 1 = best)',
        xaxis_title='Total Avg Holding Time (all 5 levels, days)',
        yaxis=dict(autorange='reversed'),
        height=max(400, len(rank_df)*22 + 80),
        margin=dict(t=50,l=120,r=20,b=40)
    )

    # ── Chart 5: Weekly Submission Flow ─────────────────────
    has_sub = fdf[fdf['First SUP to DS'].notna()].copy()
    if len(has_sub) > 0:
        wk_grp = (has_sub.groupby(['Sro_Name','Week_Label'])
                         .size()
                         .reset_index(name='FSU Count')
                         .sort_values('Week_Label'))
        fig_wk = px.bar(
            wk_grp, x='Sro_Name', y='FSU Count', color='Week_Label',
            barmode='group',
            title='Weekly FSU Submission Flow per SRO (SUP→DS submission date)',
            color_discrete_sequence=px.colors.qualitative.Set2,
            height=500
        )
        fig_wk.update_layout(
            xaxis_tickangle=-45, legend_title='ISO Week',
            margin=dict(t=50,b=120)
        )
    else:
        fig_wk = go.Figure().update_layout(title="No submission data with current filters")

    # ── Chart 6: Heatmap ────────────────────────────────────
    if len(has_sub) > 0:
        pivot = (has_sub.groupby(['Sro_Name','Week_Label'])
                        .size()
                        .unstack(fill_value=0)
                        .sort_index())
        # compute % of own total to show skew
        pct = pivot.div(pivot.sum(axis=1), axis=0).multiply(100).round(1)
        fig_heat = px.imshow(
            pct,
            labels=dict(x='ISO Week', y='SRO', color='% of Total Submissions'),
            title='Submission Skew Heatmap — % of Monthly Submissions by Week',
            color_continuous_scale='RdYlGn',
            aspect='auto', height=max(400, len(pivot)*18+100)
        )
        fig_heat.update_layout(margin=dict(t=60,b=40,l=120))
        fig_heat.update_coloraxes(reversescale=True)
    else:
        fig_heat = go.Figure().update_layout(title="No submission data with current filters")

    # ── Chart 7: FV vs RV distribution ──────────────────────
    if 'Max Visit Number' in fdf.columns:
        fdf2 = fdf.copy()
        fdf2['Visit_Type'] = fdf2['Max Visit Number'].apply(
            lambda x: 'FV (Visit 1 only)' if str(x).strip()=='1.0' or str(x).strip()=='1' else 'RV (Multiple Visits)')
        visit_grp = fdf2.groupby(['Sro_Name','Visit_Type']).size().reset_index(name='FSU Count')
        fig_visit = px.bar(
            visit_grp, x='Sro_Name', y='FSU Count', color='Visit_Type',
            barmode='group',
            title='First Visit (FV) vs Repeat Visit (RV) by SRO',
            color_discrete_map={'FV (Visit 1 only)':'#27ae60','RV (Multiple Visits)':'#e74c3c'},
            text='FSU Count', height=480
        )
        fig_visit.update_traces(textposition='outside')
        fig_visit.update_layout(xaxis_tickangle=-45, margin=dict(t=50,b=120))
    else:
        fig_visit = go.Figure().update_layout(title="Visit data not available")

    return (
        str(p_total),
        avg('ENM_HT'), avg('SUP_HT_First'), avg('SUP_HT_Refer'),
        avg('ENM_HT_Refer'), avg('SUP_HT_Clarif'),
        fig_enm, fig_sup, fig_all, fig_rank, fig_wk, fig_heat, fig_visit
    )

if __name__ == '__main__':
    app.run(debug=False)
