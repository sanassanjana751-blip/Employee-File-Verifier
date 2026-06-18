import os
import streamlit as st
import pandas as pd
import glob

# Import configuration and scan utilities
import config
from utils import document_inventory

# Set Page Config
st.set_page_config(
    page_title="Employee File Verifier Dashboard",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Custom Styling & Theme (Glassmorphism & Gradients)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    font-family: 'Outfit', sans-serif;
    background-color: #0d0f14;
    color: #e2e8f0;
}

/* Custom cards styling */
.glass-card {
    background: rgba(30, 41, 59, 0.45);
    backdrop-filter: blur(12px);
    border-radius: 16px;
    padding: 24px;
    border: 1px solid rgba(255, 255, 255, 0.06);
    box-shadow: 0 10px 30px 0 rgba(0, 0, 0, 0.3);
    margin-bottom: 20px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.glass-card:hover {
    border-color: #0ea5e9;
    box-shadow: 0 10px 30px 0 rgba(14, 165, 233, 0.15);
    transform: translateY(-2px);
}

.metric-number {
    font-size: 2.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #38bdf8 0%, #a855f7 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 5px 0;
}

.metric-lbl {
    font-size: 0.85rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 600;
}

/* Hero Section Banner */
.hero-banner {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.7) 100%);
    border-radius: 20px;
    padding: 40px;
    border: 1px solid rgba(14, 165, 233, 0.2);
    box-shadow: 0 15px 40px 0 rgba(0, 0, 0, 0.4);
    margin-bottom: 30px;
    position: relative;
    overflow: hidden;
}

.hero-banner::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -50%;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(14, 165, 233, 0.15) 0%, transparent 70%);
    z-index: 0;
}

.hero-title {
    font-size: 2.5rem;
    font-weight: 800;
    background: linear-gradient(to right, #38bdf8, #818cf8, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 10px;
    z-index: 1;
    position: relative;
}

.hero-sub {
    font-size: 1.1rem;
    color: #94a3b8;
    margin-bottom: 0px;
    z-index: 1;
    position: relative;
}
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR: CONTROLS & REPORT SELECTOR -----------------
with st.sidebar:
    st.markdown("<h2 style='text-align:center; font-weight:800; background:linear-gradient(to right, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>⚙️ Operation Terminal</h2>", unsafe_allow_html=True)
    st.write("---")

    # Section 1: Scan Directory Trigger
    st.markdown("### 🔍 Scan Local Directory")
    st.caption("Scan a folder containing employee documents to generate a new checklist report.")
    
    scan_path_input = st.text_input("Enter Folder Path to Scan:", placeholder="e.g., C:\\HR\\Teaching_Staff")
    
    if st.button("🚀 Run Inventory Scan", use_container_width=True):
        if not scan_path_input.strip():
            st.warning("Please enter a valid directory path.")
        elif not os.path.isdir(scan_path_input.strip()):
            st.error("Directory not found. Verify the local path.")
        else:
            with st.spinner("Scanning directory and generating checklist..."):
                try:
                    cfg = config.load_config()
                    aliases = cfg.get("document_aliases", document_inventory.DEFAULT_DOCUMENT_ALIASES)
                    
                    csv_path, emp_count, file_count = document_inventory.run_inventory(
                        scan_path_input.strip(),
                        config.OUTPUT_DIR,
                        aliases=aliases
                    )
                    st.success(f"Successfully processed {emp_count} employees!")
                    
                    # Store newly created report filename in session state to auto-select it
                    st.session_state["selected_report"] = os.path.basename(csv_path)
                    st.rerun()
                except Exception as e:
                    st.error(f"Scan failed: {e}")

    st.write("---")

    # Section 2: Report Selector
    st.markdown("### 📑 Load Checklist Report")
    st.caption("Select a previously generated CSV inventory report to visualize.")

    # List all CSV reports in config.OUTPUT_DIR and filter for valid checklist format
    csv_pattern = os.path.join(config.OUTPUT_DIR, "*.csv")
    csv_files = glob.glob(csv_pattern)
    csv_files.sort(key=os.path.getmtime, reverse=True)
    
    csv_names = []
    for f in csv_files:
        try:
            # Read only headers to verify column compatibility
            headers = pd.read_csv(f, nrows=0).columns
            if "Employee Name" in headers and "Missing Docs" in headers:
                csv_names.append(os.path.basename(f))
        except Exception:
            pass

    if not csv_names:
        st.info("No reports found in output folder. Scan a directory above to start.")
        selected_report = None
    else:
        # Fallback to first (newest) report or use session_state selection
        default_idx = 0
        if "selected_report" in st.session_state and st.session_state["selected_report"] in csv_names:
            default_idx = csv_names.index(st.session_state["selected_report"])
            
        selected_report = st.selectbox(
            "Select CSV Report File:",
            csv_names,
            index=default_idx
        )
        st.session_state["selected_report"] = selected_report

        if st.button("🔄 Refresh List", use_container_width=True):
            st.rerun()

# ----------------- MAIN PANEL: HEADER -----------------
st.markdown("""
<div class="hero-banner">
    <div class="hero-title">Employee File Verifier Portal</div>
    <div class="hero-sub">Visualize local document checklists, inspect employee compliance, and analyze missing files.</div>
</div>
""", unsafe_allow_html=True)

# Return early if no report is loaded
if not selected_report:
    st.warning("⚠️ No inventory checklist report loaded. Please enter a directory path in the sidebar and scan it to create a report.")
    st.stop()

# ----------------- LOAD & CALCULATE STATISTICS -----------------
report_path = os.path.join(config.OUTPUT_DIR, selected_report)
try:
    df = pd.read_csv(report_path)
except Exception as e:
    st.error(f"Error reading report {selected_report}: {e}")
    st.stop()

# Column Validation
if "Employee Name" not in df.columns or "Missing Docs" not in df.columns:
    st.error("Invalid CSV report format. The selected CSV must contain 'Employee Name' and 'Missing Docs' columns.")
    st.stop()

# Calculate stats
total_employees = len(df)

# Compliance check: "Missing Docs" is empty or nan
is_compliant = df["Missing Docs"].isna() | (df["Missing Docs"].astype(str).str.strip() == "")
compliant_count = is_compliant.sum()
non_compliant_count = total_employees - compliant_count
compliance_percentage = (compliant_count / total_employees * 100) if total_employees > 0 else 0.0

# ----------------- STATS ROW (Metrics) -----------------
m_col1, m_col2, m_col3, m_col4 = st.columns(4)

with m_col1:
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-lbl">Total Employees</div>
        <div class="metric-number">{total_employees}</div>
    </div>
    """, unsafe_allow_html=True)

with m_col2:
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-lbl" style="color: #4ade80">Fully Compliant</div>
        <div class="metric-number" style="background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{compliant_count}</div>
    </div>
    """, unsafe_allow_html=True)

with m_col3:
    missing_color = "#f87171" if non_compliant_count > 0 else "#4ade80"
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-lbl" style="color: {missing_color}">Missing Documents</div>
        <div class="metric-number" style="background: linear-gradient(135deg, {missing_color} 0%, #fb923c 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{non_compliant_count}</div>
    </div>
    """, unsafe_allow_html=True)

with m_col4:
    rate_color = "#38bdf8"
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-lbl">Compliance Rate</div>
        <div class="metric-number" style="background: linear-gradient(135deg, {rate_color} 0%, #818cf8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{compliance_percentage:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

# ----------------- TABS SYSTEM -----------------
tabs = st.tabs(["🔍 Checklist Matrix", "📊 Missing Docs Analytics", "👤 Employee Inspector"])

# ================= TAB 1: CHECKLIST MATRIX =================
with tabs[0]:
    st.markdown("### 🕵️ Interactive Checklist Search & Filter")
    st.caption(f"Currently viewing report: `{selected_report}` (Loaded from local disk)")
    
    # Filter controls
    s_col1, s_col2 = st.columns([3, 1])
    with s_col1:
        search_query = st.text_input("🔍 Search employee by name:", "").strip()
    with s_col2:
        compliance_filter = st.selectbox(
            "Filter by Compliance:",
            ["All Employees", "Fully Compliant", "Missing Documents"]
        )

    # Filter operations
    filtered_df = df.copy()

    # Search filter
    if search_query:
        filtered_df = filtered_df[filtered_df["Employee Name"].str.contains(search_query, case=False, na=False)]

    # Compliance status filter
    if compliance_filter == "Fully Compliant":
        filtered_df = filtered_df[filtered_df["Missing Docs"].isna() | (filtered_df["Missing Docs"].astype(str).str.strip() == "")]
    elif compliance_filter == "Missing Documents":
        filtered_df = filtered_df[~(filtered_df["Missing Docs"].isna() | (filtered_df["Missing Docs"].astype(str).str.strip() == ""))]

    if filtered_df.empty:
        st.info("No employee records match the filter criteria.")
    else:
        # Style dataframe displaying Yes/No beautifully
        # Use pandas styler to highlight "Yes" green and "No" red
        def highlight_yes_no(val):
            if val == "Yes":
                return "color: #4ade80; font-weight: bold;"
            elif val == "No":
                return "color: #f87171; font-weight: bold;"
            return ""

        styled_df = filtered_df.style.map(highlight_yes_no, subset=[c for c in df.columns if c not in ["Employee Name", "Missing Docs"]])
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True
        )

# ================= TAB 2: ANALYTICS =================
with tabs[1]:
    st.markdown("### 📊 Document Missing Frequency Analysis")
    st.caption("Identifies which documents are most commonly missing across all listed employees to assist auditing.")

    # Get document columns
    doc_cols = [c for c in df.columns if c not in ["Employee Name", "Missing Docs"]]
    
    # Calculate missing count per document type
    missing_stats = []
    for col in doc_cols:
        no_count = (df[col] == "No").sum()
        yes_count = (df[col] == "Yes").sum()
        missing_stats.append({
            "Document Type": col,
            "Missing (No)": no_count,
            "Submitted (Yes)": yes_count
        })

    if not missing_stats:
        st.info("No document types available for analysis.")
    else:
        stats_df = pd.DataFrame(missing_stats)
        
        # Display missing documents bar chart
        st.subheader("Count of Missing Documents by Type")
        chart_data = stats_df.set_index("Document Type")[["Missing (No)"]]
        st.bar_chart(chart_data, color="#f87171", use_container_width=True)

        # Summary Table
        st.write("---")
        st.subheader("Detailed Document Submissions Summary")
        st.dataframe(
            stats_df,
            column_config={
                "Document Type": "Document Name",
                "Missing (No)": st.column_config.NumberColumn("Missing Count", help="Number of employees missing this document"),
                "Submitted (Yes)": st.column_config.NumberColumn("Submitted Count", help="Number of employees who have submitted this document")
            },
            use_container_width=True,
            hide_index=True
        )

# ================= TAB 3: EMPLOYEE INSPECTOR =================
with tabs[2]:
    st.markdown("### 👤 Employee Folder Details Inspector")
    st.caption("Inspect document submission checklist and check missing documents for an individual employee.")

    employee_list = sorted(df["Employee Name"].dropna().unique())
    if not employee_list:
        st.info("No employees found in the report.")
    else:
        selected_emp = st.selectbox("Select Employee to Inspect:", employee_list)
        
        # Get details for selected employee
        emp_row = df[df["Employee Name"] == selected_emp].iloc[0]
        
        # Draw clean UI Card
        st.markdown(f"#### 📁 Folder Audit for: **{selected_emp}**")
        
        col_chk, col_alert = st.columns(2)
        
        with col_chk:
            st.markdown("##### Document Submission Status")
            for doc in doc_cols:
                status = emp_row[doc]
                if status == "Yes":
                    st.write(f"🟢 **Submitted**: {doc}")
                else:
                    st.write(f"🔴 **Missing**: {doc}")
                    
        with col_alert:
            st.markdown("##### Compliance Status Summary")
            missing_val = emp_row["Missing Docs"]
            
            if pd.isna(missing_val) or str(missing_val).strip() == "":
                st.success("🎉 **Fully Compliant**: This employee has submitted all required core documents.")
            else:
                st.error("⚠️ **Action Required**: Missing documents must be gathered.")
                st.write(f"**Missing Items:** `{missing_val}`")
