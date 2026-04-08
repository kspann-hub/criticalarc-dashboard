import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.filters import apply_filters
from utils.cxalloy import load_project_data

# ─── Safe Get ─────────────────────────────────────────────────────────────────
def safe_get(sheets, key):
    val = sheets.get(key) if sheets else None
    return val if val is not None else pd.DataFrame()

# ─── Chart Helpers ────────────────────────────────────────────────────────────
def plotly_bar(df, x, y, title, color=None, color_map=None, orientation='v'):
    fig = px.bar(df, x=x, y=y, title=title, color=color,
                 color_discrete_map=color_map, orientation=orientation,
                 template="plotly_dark")
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Barlow, sans-serif', size=11, color='#8A8F98'),
        title_font=dict(size=12, color='#8A8F98', family='Barlow Condensed'),
        margin=dict(t=40, b=10, l=10, r=10),
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#8A8F98')),
        xaxis=dict(gridcolor='#3E4248', tickfont=dict(size=11, color='#8A8F98')),
        yaxis=dict(gridcolor='#3E4248', tickfont=dict(size=11, color='#8A8F98')),
    )
    return fig

def plotly_donut(labels, values, title, colors):
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.65,
        marker_colors=colors,
        marker=dict(line=dict(color='#2D3035', width=2)),
        textinfo='none',
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>'
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=12, color='#8A8F98', family='Barlow Condensed')),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Barlow, sans-serif', size=11, color='#8A8F98'),
        showlegend=True,
        legend=dict(
            bgcolor='rgba(0,0,0,0)',
            font=dict(size=11, color='#8A8F98', family='Barlow, sans-serif'),
            orientation='v', x=1.02, y=0.5
        ),
        margin=dict(t=40, b=10, l=10, r=150),
    )
    return fig

def plotly_hbar_pct(df, y_col, pct_col, title):
    fig = go.Figure(go.Bar(
        x=df[pct_col], y=df[y_col], orientation='h',
        marker=dict(
            color=df[pct_col],
            colorscale=[[0, '#E04040'], [0.5, '#F4B942'], [1, '#39B54A']],
            showscale=False
        ),
        text=df[pct_col].apply(lambda x: f"{x}%"),
        textposition='inside',
        textfont=dict(color='#F0F0F0', family='Barlow, sans-serif')
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=12, color='#8A8F98', family='Barlow Condensed')),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Barlow, sans-serif', size=11, color='#8A8F98'),
        margin=dict(t=40, b=10, l=10, r=10),
        xaxis=dict(gridcolor='#3E4248', range=[0, 105], tickfont=dict(color='#8A8F98')),
        yaxis=dict(gridcolor='#3E4248', tickfont=dict(size=10, color='#8A8F98')),
        height=400
    )
    return fig

# ─── KPI Card ─────────────────────────────────────────────────────────────────
def kpi_card(label, value, color_class="kpi-white", sub=""):
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value {color_class}">{value}</div>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)

def section(label):
    st.markdown(f'<div class="section-header">{label}</div>', unsafe_allow_html=True)

def format_assigned(row):
    name    = str(row.get('assigned_name', '')).strip()
    company = str(row.get('assigned_company', '')).strip()
    if name and company and name != company:
        return f"{name} ({company})"
    return company if company else name

# ─── Main Render ──────────────────────────────────────────────────────────────
def render(config: dict, filters: dict, all_sheets: dict = None):
    if all_sheets is None:
        with st.spinner("Loading data..."):
            try:
                all_sheets = load_project_data(config["project_id"])
            except Exception as e:
                st.error(f"Error loading data: {e}")
                return

    issues_raw     = safe_get(all_sheets, 'Issues')
    checklists_raw = safe_get(all_sheets, 'Checklists')
    tests_raw      = safe_get(all_sheets, 'Tests')

    issues     = apply_filters(issues_raw, filters)
    checklists = apply_filters(checklists_raw, filters)
    tests      = apply_filters(tests_raw, filters)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Issue Tracking",
        "✅ Checklist (PFC)",
        "🧪 Functional Tests",
        "🛗 Vertical Conveyance"
    ])

    # ══════════════════════════════════════════════════════════════
    # TAB 1 — ISSUE TRACKING
    # ══════════════════════════════════════════════════════════════
    with tab1:
        if issues.empty:
            st.info("No issue data available.")
        else:
            open_issues  = issues[issues['status'] != 'Closed']
            aging_60     = open_issues[open_issues['aging_category'] == '>60 Days']
            aging_45     = open_issues[open_issues['aging_category'] == '45-60 Days']
            in_progress  = open_issues[open_issues['status'] == 'In Progress']
            high_priority = open_issues[open_issues['priority'].str.contains('High', na=False)]

            section("Key Metrics")
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                kpi_card("Total Open Issues", len(open_issues),
                         "kpi-red" if len(open_issues) > 10 else "kpi-yellow", "non-closed")
            with c2: kpi_card("Aging > 60 Days", len(aging_60), "kpi-red", "flagged red")
            with c3: kpi_card("Aging 45–60 Days", len(aging_45), "kpi-yellow", "warning zone")
            with c4: kpi_card("In Progress", len(in_progress), "kpi-blue", "actively worked")
            with c5: kpi_card("High Priority", len(high_priority), "kpi-red", "open & high")

            section("Issue Breakdown")
            col_l, col_r = st.columns(2)

            with col_l:
                if 'priority' in issues.columns:
                    priority_counts = issues['priority'].value_counts().reset_index()
                    priority_counts.columns = ['Priority', 'Count']
                    colors = {
                        'High (Will Impact Performance)': '#E04040',
                        'Moderate (May Impact Performance)': '#F4B942',
                        "Low (Won't Impact Performance)": '#39B54A'
                    }
                    color_list = [colors.get(p, '#8A8F98') for p in priority_counts['Priority']]
                    st.plotly_chart(plotly_donut(priority_counts['Priority'],
                                                 priority_counts['Count'],
                                                 "All Issues by Priority", color_list),
                                    use_container_width=True)

            with col_r:
                if 'status' in issues.columns:
                    status_counts = issues['status'].value_counts().reset_index()
                    status_counts.columns = ['Status', 'Count']
                    status_colors = {
                        'Open': '#E04040', 'In Progress': '#4A90D9',
                        'Pending Review': '#F4B942', 'Closed': '#39B54A',
                    }
                    st.plotly_chart(plotly_bar(status_counts, 'Status', 'Count',
                                               'All Issues by Status', color='Status',
                                               color_map=status_colors),
                                    use_container_width=True)

            section("Issues by Division")
            if 'discipline' in issues.columns:
                disc_counts = (issues.groupby('discipline')
                               .size().reset_index(name='Count')
                               .sort_values('Count', ascending=True).tail(15))
                fig = plotly_bar(disc_counts, 'Count', 'discipline',
                                 'All Issues per Division', orientation='h')
                fig.update_layout(height=400, yaxis_title="", xaxis_title="Issue Count")
                st.plotly_chart(fig, use_container_width=True)

            section("Issues by Contractor")
            if 'assigned_company' in issues.columns:
                contractor_counts = (issues.groupby('assigned_company')
                                     .size().reset_index(name='Count')
                                     .sort_values('Count', ascending=False).head(15))
                fig = plotly_bar(contractor_counts, 'assigned_company', 'Count',
                                 'All Issues per Contractor', color='Count')
                fig.update_layout(xaxis_tickangle=-35)
                st.plotly_chart(fig, use_container_width=True)

            section("Aging Issues Detail")
            aging_issues = issues[issues['aging_category'].isin(
                ['>60 Days', '45-60 Days'])].copy()
            if not aging_issues.empty:
                aging_issues['Aging'] = aging_issues['aging_category'].apply(
                    lambda c: '🔴 >60 Days' if c == '>60 Days' else '🟡 45-60 Days'
                )
                aging_issues['Assigned To'] = aging_issues.apply(format_assigned, axis=1)
                display_cols = [c for c in ['name', 'Aging', 'days_open', 'priority',
                                            'discipline', 'Assigned To', 'status',
                                            'description'] if c in aging_issues.columns]
                st.dataframe(aging_issues[display_cols].rename(columns={
                    'name': 'Issue #', 'days_open': 'Days Open', 'priority': 'Priority',
                    'discipline': 'Division', 'status': 'Status', 'description': 'Description'
                }), use_container_width=True, hide_index=True)
            else:
                st.success("✅ No aging issues with current filters.")

            with st.expander("📄 View All Issues"):
                all_issues_display = issues.copy()
                all_issues_display['Assigned To'] = all_issues_display.apply(
                    format_assigned, axis=1)
                view_cols = [c for c in ['name', 'priority', 'status', 'discipline',
                                         'Assigned To', 'days_open', 'date_created',
                                         'description'] if c in all_issues_display.columns]
                st.dataframe(
                    all_issues_display[view_cols].rename(columns={
                        'name': 'Issue #', 'priority': 'Priority', 'status': 'Status',
                        'discipline': 'Division', 'days_open': 'Days Open',
                        'date_created': 'Date Created', 'description': 'Description'
                    }), use_container_width=True, hide_index=True)

    # ══════════════════════════════════════════════════════════════
    # TAB 2 — CHECKLIST (PFC)
    # ══════════════════════════════════════════════════════════════
    with tab2:
        if checklists.empty:
            st.info("No checklist data available.")
        else:
            total_cl = len(checklists)
            verified_statuses = ['Checklist Complete', 'Verified',
                                  'Verified - Not Included in Sampling']
            completed    = checklists[checklists['status'].isin(verified_statuses)].shape[0]
            in_prog_cl   = checklists[checklists['status'] == 'In Progress'].shape[0]
            assigned_cl  = checklists[checklists['status'] == 'Assigned'].shape[0]
            completion_pct = f"{completed/total_cl*100:.1f}%" if total_cl > 0 else "0%"

            section("Checklist Summary")
            c1, c2, c3, c4 = st.columns(4)
            with c1: kpi_card("Total Checklists", total_cl, "kpi-white")
            with c2: kpi_card("Completed / Verified", completed, "kpi-green", completion_pct)
            with c3: kpi_card("In Progress", in_prog_cl, "kpi-blue")
            with c4: kpi_card("Assigned (Not Started)", assigned_cl, "kpi-yellow")

            col_l, col_r = st.columns(2)
            with col_l:
                status_counts = checklists['status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Count']
                status_colors = {
                    'Verified': '#39B54A',
                    'Checklist Complete': '#5DD96A',
                    'Verified - Not Included in Sampling': '#8AE895',
                    'In Progress': '#4A90D9',
                    'Assigned': '#F4B942',
                    'Script In Development': '#6E7FD4'
                }
                color_list = [status_colors.get(s, '#8A8F98') for s in status_counts['Status']]
                fig = go.Figure(go.Pie(
                    labels=status_counts['Status'], values=status_counts['Count'],
                    hole=0.65, marker_colors=color_list,
                    marker=dict(line=dict(color='#2D3035', width=2)),
                    textinfo='none',
                    hovertemplate='<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>'
                ))
                fig.update_layout(
                    title=dict(text="Checklists by Status",
                               font=dict(size=12, color='#8A8F98', family='Barlow Condensed')),
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Barlow, sans-serif', size=11, color='#8A8F98'),
                    showlegend=True,
                    legend=dict(bgcolor='rgba(0,0,0,0)',
                                font=dict(size=11, color='#8A8F98', family='Barlow, sans-serif'),
                                orientation='v', x=1.02, y=0.5),
                    margin=dict(t=40, b=10, l=10, r=150),
                )
                st.plotly_chart(fig, use_container_width=True)

            with col_r:
                if 'discipline' in checklists.columns:
                    disc_cl    = checklists.groupby(['discipline', 'status']).size().reset_index(name='Count')
                    disc_total = disc_cl.groupby('discipline')['Count'].sum().reset_index()
                    disc_done  = (disc_cl[disc_cl['status'].isin(verified_statuses)]
                                  .groupby('discipline')['Count'].sum().reset_index())
                    disc_done.columns = ['discipline', 'Completed']
                    disc_pct = disc_total.merge(disc_done, on='discipline', how='left').fillna(0)
                    disc_pct['Completion %'] = (
                        disc_pct['Completed'] / disc_pct['Count'] * 100).round(1)
                    disc_pct = disc_pct.sort_values('Completion %', ascending=True).tail(12)
                    st.plotly_chart(plotly_hbar_pct(disc_pct, 'discipline', 'Completion %',
                                                    'Checklist Completion % by Division'),
                                    use_container_width=True)

            section("Completion by Contractor")
            if 'assigned_company' in checklists.columns:
                contractor_cl = checklists.groupby('assigned_company').agg(
                    Total=('status', 'count'),
                    Completed=('status', lambda x: x.isin(verified_statuses).sum())
                ).reset_index()
                contractor_cl['Completion %'] = (
                    contractor_cl['Completed'] / contractor_cl['Total'] * 100).round(1)
                st.dataframe(
                    contractor_cl.rename(columns={'assigned_company': 'Contractor'}),
                    use_container_width=True, hide_index=True)

            if 'type_name' in checklists.columns:
                section("By Checklist Type")
                type_counts = checklists['type_name'].value_counts().reset_index()
                type_counts.columns = ['Type', 'Count']
                st.plotly_chart(plotly_bar(type_counts, 'Type', 'Count', 'Checklists by Type'),
                                use_container_width=True)

    # ══════════════════════════════════════════════════════════════
    # TAB 3 — FUNCTIONAL TESTS
    # ══════════════════════════════════════════════════════════════
    with tab3:
        if tests.empty:
            st.info("No test data available.")
        else:
            total_tests   = len(tests)
            passed        = tests[tests['status'] == 'Passed'].shape[0]
            in_prog_tests = tests[tests['status'] == 'In Progress'].shape[0]
            assigned_tests = tests[tests['status'] == 'Assigned'].shape[0]
            deferred      = tests[tests['status'] == 'Deferred to 1B'].shape[0]
            pass_rate     = f"{passed/total_tests*100:.1f}%" if total_tests > 0 else "0%"

            section("Test Summary")
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1: kpi_card("Total Tests", total_tests, "kpi-white")
            with c2:
                pct   = passed/total_tests*100 if total_tests > 0 else 0
                color = "kpi-green" if pct >= 90 else "kpi-yellow" if pct >= 70 else "kpi-red"
                kpi_card("Passed", passed, color, pass_rate)
            with c3: kpi_card("In Progress", in_prog_tests, "kpi-blue")
            with c4: kpi_card("Assigned", assigned_tests, "kpi-yellow")
            with c5: kpi_card("Deferred", deferred, "kpi-white")

            col_l, col_r = st.columns(2)
            with col_l:
                status_counts = tests['status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Count']
                status_colors = {
                    'Passed': '#39B54A',
                    'Partially Passed (Test to be Repeated)': '#F4B942',
                    'In Progress': '#4A90D9',
                    'Assigned': '#8A8F98',
                    'Deferred to 1B': '#6E7FD4',
                    'Voided': '#3E4248'
                }
                color_list = [status_colors.get(s, '#8A8F98') for s in status_counts['Status']]
                st.plotly_chart(plotly_donut(status_counts['Status'], status_counts['Count'],
                                             "Tests by Status", color_list),
                                use_container_width=True)

            with col_r:
                if 'discipline' in tests.columns:
                    disc_tests = tests.groupby('discipline').agg(
                        Total=('status', 'count'),
                        Passed=('status', lambda x: (x == 'Passed').sum())
                    ).reset_index()
                    disc_tests['Pass Rate %'] = (
                        disc_tests['Passed'] / disc_tests['Total'] * 100).round(1)
                    disc_tests = disc_tests.sort_values('Pass Rate %', ascending=True).tail(12)
                    st.plotly_chart(plotly_hbar_pct(disc_tests, 'discipline', 'Pass Rate %',
                                                    'Pass Rate % by Division'),
                                    use_container_width=True)

            if 'asset_type' in tests.columns:
                section("Pass Rate by Equipment Type")
                asset_tests = tests.groupby('asset_type').agg(
                    Total=('status', 'count'),
                    Passed=('status', lambda x: (x == 'Passed').sum())
                ).reset_index()
                asset_tests['Pass Rate %'] = (
                    asset_tests['Passed'] / asset_tests['Total'] * 100).round(1)
                st.dataframe(asset_tests.rename(columns={'asset_type': 'Asset Type'}),
                             use_container_width=True, hide_index=True)

            with st.expander("📄 View All Tests"):
                view_cols = [c for c in ['number', 'name', 'status', 'discipline',
                                         'assigned_name', 'asset_name', 'asset_type',
                                         'attempt_count'] if c in tests.columns]
                st.dataframe(tests[view_cols], use_container_width=True, hide_index=True)

    # ══════════════════════════════════════════════════════════════
    # TAB 4 — VERTICAL CONVEYANCE
    # ══════════════════════════════════════════════════════════════
    with tab4:
        if issues_raw.empty:
            st.info("No Vertical Conveyance issues found.")
        else:
            vc_issues = issues_raw[
                issues_raw['discipline'].str.contains('14|Conveying', na=False, case=False)
            ].copy()
            vc_issues = apply_filters(vc_issues, filters)

            if vc_issues.empty:
                st.info("No Vertical Conveyance issues found.")
            else:
                vc_open = vc_issues[vc_issues['status'] != 'Closed']

                section("Vertical Conveyance — Issue Summary")
                c1, c2, c3, c4 = st.columns(4)
                with c1: kpi_card("Total VC Issues", len(vc_issues), "kpi-white")
                with c2: kpi_card("Open", len(vc_issues[vc_issues['status'] == 'Open']), "kpi-red")
                with c3: kpi_card("In Progress", len(vc_issues[vc_issues['status'] == 'In Progress']), "kpi-blue")
                with c4: kpi_card("Closed", len(vc_issues[vc_issues['status'] == 'Closed']), "kpi-green")

                col_l, col_r = st.columns(2)
                with col_l:
                    if not vc_open.empty:
                        priority_vc = vc_open['priority'].value_counts().reset_index()
                        priority_vc.columns = ['Priority', 'Count']
                        colors = {
                            'High (Will Impact Performance)': '#E04040',
                            'Moderate (May Impact Performance)': '#F4B942',
                            "Low (Won't Impact Performance)": '#39B54A'
                        }
                        color_list = [colors.get(p, '#8A8F98') for p in priority_vc['Priority']]
                        st.plotly_chart(plotly_donut(priority_vc['Priority'], priority_vc['Count'],
                                                     "Open VC Issues by Priority", color_list),
                                        use_container_width=True)

                with col_r:
                    status_vc = vc_issues['status'].value_counts().reset_index()
                    status_vc.columns = ['Status', 'Count']
                    status_colors = {
                        'Open': '#E04040', 'In Progress': '#4A90D9',
                        'Pending Review': '#F4B942', 'Closed': '#39B54A'
                    }
                    st.plotly_chart(plotly_bar(status_vc, 'Status', 'Count',
                                               'VC Issues by Status', color='Status',
                                               color_map=status_colors),
                                    use_container_width=True)

                section("Open Vertical Conveyance Issues")
                display_cols = [c for c in ['name', 'priority', 'status', 'days_open',
                                            'assigned_company', 'aging_category',
                                            'description'] if c in vc_open.columns]
                vc_display = vc_open[display_cols].copy()
                if 'aging_category' in vc_display.columns:
                    vc_display['aging_category'] = vc_display['aging_category'].apply(
                        lambda c: '🔴 >60 Days' if c == '>60 Days'
                        else '🟡 45-60 Days' if c == '45-60 Days' else '🟢 Under 45'
                    )
                st.dataframe(vc_display.rename(columns={
                    'name': 'Issue #', 'priority': 'Priority', 'status': 'Status',
                    'days_open': 'Days Open', 'assigned_company': 'Contractor',
                    'aging_category': 'Aging', 'description': 'Description'
                }), use_container_width=True, hide_index=True)