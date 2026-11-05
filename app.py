import io
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ==========================================
# 1. PAGE CONFIGURATION & METALLURGY THEME
# ==========================================
st.set_page_config(
    page_title="Metallurgy Diffusion Lab | Arrhenius Suite",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

R_GAS = 8.314

st.markdown(
    """
<style>
    .stApp { background-color: #121519; color: #E2E8F0; }
    section[data-testid="stSidebar"] {
        background-color: #1A1E24;
        border-right: 2px solid #FF6B00;
    }
    h1, h2, h3 {
        color: #FF8C00 !important;
        font-family: 'Segoe UI', Roboto, Helvetica, sans-serif;
        font-weight: 700;
    }
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #1E232A, #252B34);
        border: 1px solid #3A4250;
        border-left: 5px solid #FF6B00;
        padding: 15px; border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.4);
    }
    div[data-testid="stMetricValue"] {
        color: #FFA500 !important;
        font-family: 'Courier New', monospace;
        font-weight: bold;
    }
    .stButton > button {
        background: linear-gradient(90deg, #FF5100 0%, #FF8C00 100%);
        color: #FFFFFF; border: none; border-radius: 6px;
        font-weight: 600; transition: all 0.3s ease; width: 100%;
    }
    .stButton > button:hover {
        box-shadow: 0 0 12px rgba(255, 107, 0, 0.7);
        transform: translateY(-1px); color: #FFFFFF;
    }
    button[data-baseweb="tab"] { color: #A0AEC0 !important; font-weight: 600; }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #FF8C00 !important;
        border-bottom-color: #FF6B00 !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# 2. DATABASE
# ==========================================
def init_database():
    if "materials_db" not in st.session_state:
        default_data = [
            {"Label": "C in γ-Fe (FCC Austenite)", "Species": "C", "Host": "γ-Fe (FCC)", "Mechanism": "Interstitial", "D0_m2s": 2.3e-5, "Q_kJ_mol": 148.0},
            {"Label": "C in α-Fe (BCC Ferrite)", "Species": "C", "Host": "α-Fe (BCC)", "Mechanism": "Interstitial", "D0_m2s": 6.2e-7, "Q_kJ_mol": 80.0},
            {"Label": "N in α-Fe (BCC Ferrite)", "Species": "N", "Host": "α-Fe (BCC)", "Mechanism": "Interstitial", "D0_m2s": 5.0e-7, "Q_kJ_mol": 77.0},
            {"Label": "Fe in α-Fe (BCC Self-Diffusion)", "Species": "Fe", "Host": "α-Fe (BCC)", "Mechanism": "Substitutional", "D0_m2s": 2.8e-4, "Q_kJ_mol": 251.0},
            {"Label": "Fe in γ-Fe (FCC Self-Diffusion)", "Species": "Fe", "Host": "γ-Fe (FCC)", "Mechanism": "Substitutional", "D0_m2s": 5.0e-5, "Q_kJ_mol": 284.0},
            {"Label": "Cu in Al (FCC)", "Species": "Cu", "Host": "Al (FCC)", "Mechanism": "Substitutional", "D0_m2s": 6.5e-5, "Q_kJ_mol": 136.0},
            {"Label": "Mg in Al (FCC)", "Species": "Mg", "Host": "Al (FCC)", "Mechanism": "Substitutional", "D0_m2s": 1.2e-4, "Q_kJ_mol": 130.0},
            {"Label": "Zn in Cu (FCC Brass)", "Species": "Zn", "Host": "Cu (FCC)", "Mechanism": "Substitutional", "D0_m2s": 2.4e-5, "Q_kJ_mol": 189.0},
            {"Label": "Cu in Cu (FCC Self-Diffusion)", "Species": "Cu", "Host": "Cu (FCC)", "Mechanism": "Substitutional", "D0_m2s": 7.8e-5, "Q_kJ_mol": 211.0},
            {"Label": "Al in Al (FCC Self-Diffusion)", "Species": "Al", "Host": "Al (FCC)", "Mechanism": "Substitutional", "D0_m2s": 2.3e-4, "Q_kJ_mol": 144.0},
            {"Label": "Ni in γ-Fe (FCC)", "Species": "Ni", "Host": "γ-Fe (FCC)", "Mechanism": "Substitutional", "D0_m2s": 7.7e-5, "Q_kJ_mol": 280.0},
        ]
        st.session_state.materials_db = pd.DataFrame(default_data)


init_database()


# ==========================================
# 3. MATH HELPERS
# ==========================================
def to_kelvin(temp, unit):
    return temp + 273.15 if unit == "°C" else temp

def to_celsius(temp_k):
    return temp_k - 273.15

def calc_diffusion_coeff(d0, q_j_mol, temp_k):
    return d0 * np.exp(-q_j_mol / (R_GAS * temp_k))

def calc_inverse_temperature(d_target, d0, q_j_mol):
    return -q_j_mol / (R_GAS * np.log(d_target / d0))

def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Diffusion_Data")
    return output.getvalue()


# ==========================================
# 4. SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("## ⚙️ Materials Database")
    st.caption("Add a custom alloy/diffusion system to the active session database.")

    with st.expander("➕ Add New Diffusion System", expanded=False):
        with st.form("add_material_form"):
            sp_in = st.text_input("Diffusing Species (e.g., Cr)", value="Cr")
            host_in = st.text_input("Host Metal (e.g., α-Fe)", value="α-Fe (BCC)")
            mech_in = st.selectbox("Mechanism", ["Substitutional", "Interstitial"])
            d0_in = st.number_input("D₀ (m²/s)", value=2.5e-4, format="%.2e", step=1e-5)
            q_unit = st.radio("Activation Energy (Q) Unit", ["kJ/mol", "J/mol"], horizontal=True)
            q_in = st.number_input("Activation Energy (Q)", value=240.0, step=1.0)

            submitted = st.form_submit_button("Save to Database")
            if submitted:
                if d0_in <= 0 or q_in <= 0:
                    st.error("Physical Error: D₀ and Q must be positive (> 0)!")
                elif not sp_in.strip() or not host_in.strip():
                    st.error("Please enter valid names for Species and Host.")
                else:
                    q_kj = q_in if q_unit == "kJ/mol" else q_in / 1000.0
                    new_label = f"{sp_in.strip()} in {host_in.strip()}"
                    new_row = pd.DataFrame([{
                        "Label": new_label, "Species": sp_in.strip(),
                        "Host": host_in.strip(), "Mechanism": mech_in,
                        "D0_m2s": d0_in, "Q_kJ_mol": q_kj,
                    }])
                    st.session_state.materials_db = pd.concat(
                        [st.session_state.materials_db, new_row], ignore_index=True
                    )
                    st.success(f"Added '{new_label}' successfully!")

    st.markdown("---")
    st.markdown("### 📊 Global Unit Preferences")
    global_temp_unit = st.radio("Default Temperature Unit:", ["°C", "K"], horizontal=True)

    st.markdown("---")
    st.markdown("### 📥 Export Full Database")
    db_df = st.session_state.materials_db
    st.download_button(
        label="Download Database (CSV)",
        data=db_df.to_csv(index=False).encode("utf-8"),
        file_name="metallurgy_diffusion_database.csv",
        mime="text/csv",
    )
    st.download_button(
        label="Download Database (Excel)",
        data=convert_df_to_excel(db_df),
        file_name="metallurgy_diffusion_database.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# ==========================================
# 5. HEADER & TABS
# ==========================================
st.title("🔥 Solid-State Diffusion & Arrhenius Analytical Lab")
st.markdown("**Materials Science & Metallurgical Engineering Suite** | $D = D_0 \\exp\\left(-\\frac{Q}{RT}\\right)$")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🧮 Arrhenius & Plot",
    "⚖️ Multi-Alloy Comparison",
    "📏 Fick's 2nd Law (Depth)",
    "📈 Experimental Regression (Q & D₀)",
    "🗂️ Database Viewer",
])


# ------------------------------------------
# TAB 1
# ------------------------------------------
with tab1:
    col_in, col_out = st.columns([1, 1.3], gap="large")

    with col_in:
        st.subheader("1. Forward Calculation (Find D)")
        selected_label = st.selectbox(
            "Select Diffusion System:", st.session_state.materials_db["Label"]
        )
        mat_row = st.session_state.materials_db[
            st.session_state.materials_db["Label"] == selected_label
        ].iloc[0]

        d0_val = float(mat_row["D0_m2s"])
        q_kj_val = float(mat_row["Q_kJ_mol"])
        q_j_val = q_kj_val * 1000.0

        st.info(
            f"**Mechanism:** {mat_row['Mechanism']}  \n"
            f"**$D_0$:** `{d0_val:.2e} m²/s` | **$Q$:** `{q_kj_val:.1f} kJ/mol` (`{q_j_val:,.0f} J/mol`)"
        )

        # ---------- FIXED TEMPERATURE SECTION ----------
        if global_temp_unit == "°C":
            if "op_temp_c" not in st.session_state:
                st.session_state.op_temp_c = 900.0
            if "_temp_num_widget" not in st.session_state:
                st.session_state._temp_num_widget = 900.0
            if "_temp_sld_widget" not in st.session_state:
                st.session_state._temp_sld_widget = 900.0

            def _sync_from_number():
                st.session_state.op_temp_c = st.session_state._temp_num_widget
                st.session_state._temp_sld_widget = st.session_state._temp_num_widget

            def _sync_from_slider():
                st.session_state.op_temp_c = st.session_state._temp_sld_widget
                st.session_state._temp_num_widget = st.session_state._temp_sld_widget

            st.number_input(
                "Operating Temperature (°C):",
                step=10.0,
                key="_temp_num_widget",
                on_change=_sync_from_number,
                help="Must be above -273.15 °C",
            )
            st.slider(
                "Quick Adjust Temperature (°C):",
                100, 1500,
                key="_temp_sld_widget",
                on_change=_sync_from_slider,
            )
            temp_input = st.session_state.op_temp_c
            t_kelvin = to_kelvin(temp_input, "°C")
        else:
            if "op_temp_k" not in st.session_state:
                st.session_state.op_temp_k = 1173.15

            temp_input = st.number_input(
                "Operating Temperature (K):",
                value=st.session_state.op_temp_k,
                step=10.0,
                help="Must be > 0 K",
            )
            st.session_state.op_temp_k = temp_input
            t_kelvin = temp_input
        # ---------- END FIX ----------

        if t_kelvin <= 0:
            st.error("⚠️ Physical Error: Temperature cannot be at or below Absolute Zero (0 K / -273.15 °C)!")
            d_calculated = None
        else:
            d_calculated = calc_diffusion_coeff(d0_val, q_j_val, t_kelvin)
            m1, m2 = st.columns(2)
            m1.metric("Diffusion Coeff. D (m²/s)", f"{d_calculated:.3e}")
            m2.metric("Diffusion Coeff. D (cm²/s)", f"{d_calculated * 1e4:.3e}")
            st.caption(f"Calculated at **T = {t_kelvin:.2f} K** ({to_celsius(t_kelvin):.2f} °C)")

        st.markdown("---")
        st.subheader("2. Inverse Calculation (Find Required T)")
        d_target = st.number_input(
            "Target Diffusion Coefficient D (m²/s):",
            value=1.0e-11, format="%.2e", step=1e-12,
        )

        if d_target <= 0:
            st.error("⚠️ Target D must be strictly positive (> 0).")
        elif d_target >= d0_val:
            st.warning(f"⚠️ Target D ({d_target:.2e}) cannot exceed or equal D₀ ({d0_val:.2e} m²/s).")
        else:
            req_t_k = calc_inverse_temperature(d_target, d0_val, q_j_val)
            if req_t_k <= 0:
                st.error("⚠️ Target D requires a non-physical temperature (≤ 0 K).")
            else:
                req_t_c = to_celsius(req_t_k)
                im1, im2 = st.columns(2)
                im1.metric("Required Temp (°C)", f"{req_t_c:.1f} °C")
                im2.metric("Required Temp (K)", f"{req_t_k:.1f} K")

    with col_out:
        st.subheader("Interactive Arrhenius Diagram")
        if t_kelvin > 0:
            t_min_k = max(300.0, t_kelvin * 0.6)
            t_max_k = min(2500.0, t_kelvin * 1.4)
            t_range_k = np.linspace(t_min_k, t_max_k, 100)
            inv_t = 1000.0 / t_range_k
            d_vals = calc_diffusion_coeff(d0_val, q_j_val, t_range_k)
            ln_d = np.log(d_vals)
            slope = -q_j_val / R_GAS

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=inv_t, y=ln_d, mode="lines", name=selected_label,
                line=dict(color="#FF8C00", width=3),
                customdata=np.stack((t_range_k - 273.15, d_vals), axis=-1),
                hovertemplate="<b>1000/T:</b> %{x:.3f} K⁻¹<br><b>Temp:</b> %{customdata[0]:.1f} °C<br><b>ln(D):</b> %{y:.2f}<br><b>D:</b> %{customdata[1]:.2e} m²/s<extra></extra>",
            ))
            fig.add_trace(go.Scatter(
                x=[1000.0 / t_kelvin], y=[np.log(d_calculated)],
                mode="markers", name="Operating Point",
                marker=dict(color="#FF2A00", size=12, symbol="diamond",
                            line=dict(color="white", width=2)),
            ))
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#1A1E24", plot_bgcolor="#121519",
                title=f"Arrhenius Plot: ln(D) vs. 1000/T | Slope (-Q/R) = {slope:,.1f} K",
                xaxis_title="1000 / T (K⁻¹)", yaxis_title="ln(D) [D in m²/s]",
                hovermode="closest",
                legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
            )
            st.plotly_chart(fig, use_container_width=True)

            st.success(
                f"📐 **Line Equation:** $\\ln(D) = {np.log(d0_val):.2f} - \\frac{{{q_j_val:,.0f}}}{{8.314 \\cdot T}}$  \n"
                f"**Slope ($-Q/R$):** `{slope:,.2f} K`"
            )

            plot_df = pd.DataFrame({
                "Temperature_K": t_range_k,
                "Temperature_C": t_range_k - 273.15,
                "1000_over_T_K-1": inv_t,
                "D_m2_s": d_vals,
                "ln_D": ln_d,
            })
            ec1, ec2 = st.columns(2)
            ec1.download_button(
                "📥 Export Curve (CSV)",
                data=plot_df.to_csv(index=False).encode("utf-8"),
                file_name=f"Arrhenius_{mat_row['Species']}_in_{mat_row['Host']}.csv",
                mime="text/csv",
            )
            ec2.download_button(
                "📥 Export Curve (Excel)",
                data=convert_df_to_excel(plot_df),
                file_name=f"Arrhenius_{mat_row['Species']}_in_{mat_row['Host']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )


# ------------------------------------------
# TAB 2
# ------------------------------------------
with tab2:
    st.subheader("Multi-Material Diffusion Comparison")
    st.caption("Compare 2+ diffusion systems simultaneously across a thermal regime.")

    default_selections = st.session_state.materials_db["Label"].tolist()[:3]
    selected_systems = st.multiselect(
        "Select Diffusion Systems to Compare:",
        options=st.session_state.materials_db["Label"].tolist(),
        default=default_selections,
    )

    c_t1, c_t2 = st.columns(2)
    t_start_c = c_t1.number_input("Min Temperature (°C):", value=400.0, step=50.0)
    t_end_c = c_t2.number_input("Max Temperature (°C):", value=1200.0, step=50.0)

    if t_start_c <= -273.15 or t_end_c <= -273.15 or t_start_c >= t_end_c:
        st.error("⚠️ Enter a valid range above -273.15 °C (Min < Max).")
    elif len(selected_systems) < 1:
        st.warning("Please select at least one material system.")
    else:
        t_comp_k = np.linspace(to_kelvin(t_start_c, "°C"), to_kelvin(t_end_c, "°C"), 120)
        inv_t_comp = 1000.0 / t_comp_k

        fig_comp = go.Figure()
        colors = ["#FF6B00", "#00E5FF", "#FFD600", "#00E676", "#FF4081", "#B388FF"]
        comp_records = {"Temperature_C": t_comp_k - 273.15, "Temperature_K": t_comp_k}

        for idx, sys_label in enumerate(selected_systems):
            row = st.session_state.materials_db[
                st.session_state.materials_db["Label"] == sys_label
            ].iloc[0]
            d_curve = calc_diffusion_coeff(row["D0_m2s"], row["Q_kJ_mol"] * 1000.0, t_comp_k)
            comp_records[f"D_{sys_label} (m2/s)"] = d_curve
            fig_comp.add_trace(go.Scatter(
                x=inv_t_comp, y=np.log10(d_curve), mode="lines",
                name=f"{sys_label} ({row['Mechanism']})",
                line=dict(color=colors[idx % len(colors)], width=3),
                customdata=np.stack((t_comp_k - 273.15, d_curve), axis=-1),
                hovertemplate="<b>%{fullData.name}</b><br>Temp: %{customdata[0]:.0f} °C<br>D: %{customdata[1]:.2e} m²/s<extra></extra>",
            ))

        fig_comp.update_layout(
            template="plotly_dark",
            paper_bgcolor="#1A1E24", plot_bgcolor="#121519",
            title="Comparative Arrhenius Plot: log₁₀(D) vs. 1000/T",
            xaxis_title="1000 / T (K⁻¹)", yaxis_title="log₁₀(D) [D in m²/s]",
            height=500,
        )
        st.plotly_chart(fig_comp, use_container_width=True)

        comp_df = pd.DataFrame(comp_records)
        st.download_button(
            "📥 Download Comparison (Excel)",
            data=convert_df_to_excel(comp_df),
            file_name="Diffusion_Comparison_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


# ------------------------------------------
# TAB 3
# ------------------------------------------
with tab3:
    st.subheader("📏 Fick's Second Law: Penetration Depth Estimation")
    st.markdown(
        "Engineering order-of-magnitude approximation: **$x \\approx \\sqrt{D \\cdot t}$**  \n"
        "*(For the exact 1-D erfc solution, use $x \\approx 2\\sqrt{Dt}$.)*"
    )

    f_col1, f_col2 = st.columns([1, 1.3], gap="large")
    with f_col1:
        use_tab1_d = st.checkbox(
            f"Use calculated D from Tab 1 ({selected_label})", value=True
        )
        if use_tab1_d and d_calculated is not None:
            d_fick = d_calculated
            st.info(f"Using **D = `{d_fick:.3e} m²/s`**")
        else:
            d_fick = st.number_input(
                "Enter D (m²/s):", value=1.0e-11, format="%.2e"
            )

        t_unit = st.selectbox("Time Unit:", ["Hours (h)", "Minutes (min)", "Seconds (s)"])
        t_val = st.number_input("Diffusion Time (t):", value=5.0, min_value=0.001, step=1.0)

        if t_unit == "Hours (h)":
            t_sec = t_val * 3600.0
        elif t_unit == "Minutes (min)":
            t_sec = t_val * 60.0
        else:
            t_sec = t_val

        if d_fick <= 0 or t_sec <= 0:
            st.error("D and Time must be positive!")
        else:
            depth_m = np.sqrt(d_fick * t_sec)
            fm1, fm2 = st.columns(2)
            fm1.metric("Penetration Depth (μm)", f"{depth_m * 1e6:,.2f} μm")
            fm2.metric("Penetration Depth (mm)", f"{depth_m * 1e3:,.4f} mm")
            st.caption(f"Exact SI: `{depth_m:.3e} m` after `{t_sec:,.0f} s`.")

    with f_col2:
        if d_fick > 0 and t_sec > 0:
            t_array = np.linspace(0, t_sec * 1.5, 100)
            x_um_array = np.sqrt(d_fick * t_array) * 1e6

            fig_fick = go.Figure()
            fig_fick.add_trace(go.Scatter(
                x=t_array / 3600.0 if t_unit == "Hours (h)" else t_array,
                y=x_um_array, mode="lines", name="Depth Profile",
                line=dict(color="#FFA500", width=3),
            ))
            fig_fick.add_trace(go.Scatter(
                x=[t_sec / 3600.0 if t_unit == "Hours (h)" else t_sec],
                y=[depth_m * 1e6], mode="markers", name="Target Time",
                marker=dict(color="#FF2A00", size=12, symbol="circle"),
            ))
            fig_fick.update_layout(
                template="plotly_dark",
                paper_bgcolor="#1A1E24", plot_bgcolor="#121519",
                title="Parabolic Diffusion Growth: Depth (x) vs. Time (t)",
                xaxis_title="Time (Hours)" if t_unit == "Hours (h)" else "Time (Seconds)",
                yaxis_title="Penetration Depth x (μm)",
            )
            st.plotly_chart(fig_fick, use_container_width=True)


# ------------------------------------------
# TAB 4
# ------------------------------------------
with tab4:
    st.subheader("📈 Activation Energy (Q) & D₀ Estimator")
    st.markdown(
        "Linear least-squares regression on $\\ln(D) = \\ln(D_0) - \\frac{Q}{R}\\left(\\frac{1}{T}\\right)$."
    )

    reg_col1, reg_col2 = st.columns([1, 1.4], gap="large")
    with reg_col1:
        exp_temp_unit = st.radio("Experimental T Unit:", ["°C", "K"], horizontal=True)
        default_exp_df = pd.DataFrame({
            "Temperature": [800.0, 900.0, 1000.0, 1100.0, 1200.0],
            "D_m2_s": [1.45e-12, 5.92e-12, 1.95e-11, 5.48e-11, 1.35e-10],
        })
        edited_df = st.data_editor(default_exp_df, num_rows="dynamic", use_container_width=True)

    with reg_col2:
        clean_df = edited_df.dropna()
        if len(clean_df) < 2:
            st.warning("Enter at least 2 valid data points.")
        else:
            t_exp_k = (
                clean_df["Temperature"].values + 273.15
                if exp_temp_unit == "°C"
                else clean_df["Temperature"].values
            )
            d_exp = clean_df["D_m2_s"].values

            if np.any(t_exp_k <= 0) or np.any(d_exp <= 0):
                st.error("All Temperatures (K) and D values must be > 0!")
            else:
                inv_t_exp = 1.0 / t_exp_k
                ln_d_exp = np.log(d_exp)

                slope_reg, intercept_reg = np.polyfit(inv_t_exp, ln_d_exp, 1)
                q_est_j = -slope_reg * R_GAS
                q_est_kj = q_est_j / 1000.0
                d0_est = np.exp(intercept_reg)

                ln_d_pred = slope_reg * inv_t_exp + intercept_reg
                ss_res = np.sum((ln_d_exp - ln_d_pred) ** 2)
                ss_tot = np.sum((ln_d_exp - np.mean(ln_d_exp)) ** 2)
                r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 1.0

                if q_est_j < 0:
                    st.warning("⚠️ Q is negative! Check if D increases with T.")

                rm1, rm2, rm3 = st.columns(3)
                rm1.metric("Estimated Q (kJ/mol)", f"{q_est_kj:.2f}")
                rm2.metric("Estimated D₀ (m²/s)", f"{d0_est:.3e}")
                rm3.metric("R²", f"{r_squared:.5f}")

                fig_reg = go.Figure()
                fig_reg.add_trace(go.Scatter(
                    x=1000.0 * inv_t_exp, y=ln_d_exp,
                    mode="markers", name="Experimental",
                    marker=dict(color="#00E5FF", size=10),
                ))
                fig_reg.add_trace(go.Scatter(
                    x=1000.0 * inv_t_exp, y=ln_d_pred,
                    mode="lines", name=f"Fit (R²={r_squared:.4f})",
                    line=dict(color="#FF6B00", width=3, dash="dash"),
                ))
                fig_reg.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="#1A1E24", plot_bgcolor="#121519",
                    title="Arrhenius Linear Regression Fit",
                    xaxis_title="1000 / T (K⁻¹)", yaxis_title="ln(D) [m²/s]",
                )
                st.plotly_chart(fig_reg, use_container_width=True)


# ------------------------------------------
# TAB 5
# ------------------------------------------
with tab5:
    st.subheader("🗂️ Active Diffusion Database")
    st.dataframe(
        st.session_state.materials_db.style.format(
            {"D0_m2s": "{:.2e}", "Q_kJ_mol": "{:.1f}"}
        ),
        use_container_width=True,
    )


# ==========================================
# 6. FOOTER
# ==========================================
st.markdown("---")
st.markdown(
    """
    <div style="
        text-align: center; padding: 16px 12px;
        margin: 25px 0 15px 0;
        background: linear-gradient(145deg, #1A1E24, #222831);
        border: 2px solid #FF8C00; border-radius: 10px;
        color: #FF8C00 !important;
        font-family: 'Segoe UI', Roboto, Helvetica, sans-serif;
        font-size: 16px; font-weight: 700;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 12px rgba(255, 140, 0, 0.25);
    ">
        Created by Behrad Mahbobi, Manufacturing Engineering student, University of Tabriz, Tabriz, Iran
    </div>
    """,
    unsafe_allow_html=True,
)
