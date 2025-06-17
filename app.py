import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests

# --- Title and Intro ---
st.set_page_config(page_title="Rainwater Harvesting Tool", layout="centered")
st.title("💧 Rainwater Harvesting Calculator")
st.markdown("Estimate rooftop rainwater harvesting potential using either a location or uploaded rainfall data.")

# --- User Selection for Data Input Method ---
method = st.radio("Choose rainfall input method:", ["📍 Enter location", "📄 Upload CSV data"])

# --- Initialize rainfall data ---
annual_rainfall_mm = None

# --- Method 1: Location-based API Fetch (using daily and summing to annual) ---
if method == "📍 Enter location":
    location = st.text_input("Enter your city or village name:")
    if location:
        geo_url = f"https://nominatim.openstreetmap.org/search?format=json&q={location}"
        geo_response = requests.get(geo_url, headers={"User-Agent": "streamlit-app"})

        if geo_response.status_code == 200 and geo_response.text.strip():
            try:
                geo_res = geo_response.json()
                if geo_res:
                    lat = geo_res[0]['lat']
                    lon = geo_res[0]['lon']
                    st.success(f"Coordinates found: {lat}, {lon}")

                    # Fetch daily precipitation and sum to get annual rainfall
                    weather_url = (
                        f"https://archive-api.open-meteo.com/v1/archive"
                        f"?latitude={lat}&longitude={lon}"
                        f"&start_date=2023-01-01&end_date=2023-12-31"
                        f"&daily=precipitation_sum&models=era5&timezone=auto"
                    )
                    weather_res = requests.get(weather_url).json()

                    # Debug: show raw response
                    st.subheader("Raw Rainfall API Response (for debugging)")
                    st.json(weather_res)

                    daily_data = weather_res.get("daily", {})
                    rainfall_list = daily_data.get("precipitation_sum", [])

                    if rainfall_list:
                        annual_rainfall_mm = sum(rainfall_list)
                        st.success(f"Estimated Annual Rainfall: {annual_rainfall_mm:.2f} mm")
                    else:
                        st.error("No daily rainfall data found.")
                else:
                    st.warning("Location not found. Please enter a valid city or town.")
            except ValueError:
                st.error("Error: Could not decode response from location service.")
        else:
            st.error("Error: Failed to retrieve coordinates. Check your location input or internet connection.")

# --- Method 2: Manual CSV Upload ---
elif method == "📄 Upload CSV data":
    uploaded_file = st.file_uploader("Upload a CSV with total annual rainfall value (in mm)", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file, header=None)
        try:
            annual_rainfall_mm = float(df.iloc[0, 0])
            st.success(f"Annual rainfall value loaded: {annual_rainfall_mm:.2f} mm")
        except Exception:
            st.error("Ensure the CSV has one number (total rainfall in mm) in the first cell.")

# --- Proceed with Calculation if Rainfall is Available ---
if annual_rainfall_mm is not None:
    st.header("Calculation Parameters")
    area = st.number_input("🏠 Rooftop Area (m²):", min_value=0.0, value=100.0)
    efficiency = st.slider("⚙️ Collection Efficiency (%)", min_value=50, max_value=100, value=85)
    cost_per_litre = st.number_input("💸 Water Cost (Rs/litre):", min_value=0.0, value=0.005)
    tank_cost = st.number_input("🛢️ Storage System Cost (Rs):", min_value=0.0, value=20000.0)
    maintenance_cost = st.number_input("🔧 Annual Maintenance Cost (Rs):", min_value=0.0, value=500.0)
    system_life = st.number_input("⏳ System Lifespan (Years):", min_value=1, value=10)

    # Calculate annual harvest
    annual_harvest = area * annual_rainfall_mm * (efficiency / 1000)
    annual_savings = annual_harvest * cost_per_litre
    payback_period = tank_cost / annual_savings if annual_savings else float('inf')
    total_savings = (annual_savings - maintenance_cost) * system_life
    roi = ((total_savings - tank_cost) / tank_cost * 100) if tank_cost else 0

    # --- Display Results ---
    st.header("Results")
    st.success(f"💧 Total Annual Harvest: **{annual_harvest:,.2f} litres**")
    st.success(f"💰 Annual Water Bill Savings: **Rs {annual_savings:,.2f}**")
    st.info(f"📆 Payback Period: **{payback_period:.1f} years**" if payback_period < 50 else "📆 Payback period too long")
    st.write(f"📈 Total Savings Over {system_life} Years: **Rs {total_savings:,.2f}**")
    st.write(f"📊 ROI: **{roi:.1f}%**")

    # --- Graphs ---
    years = list(range(1, system_life + 1))
    cumulative_savings = [(annual_savings - maintenance_cost) * y for y in years]
    fig, ax = plt.subplots()
    ax.plot(years, cumulative_savings, marker='o')
    ax.set_title("Cumulative Savings Over Time")
    ax.set_xlabel("Year")
    ax.set_ylabel("Rs Saved")
    st.pyplot(fig)

    # --- Download Option ---
    df_summary = pd.DataFrame({
        "Year": years,
        "Cumulative Savings (Rs)": cumulative_savings
    })
    st.download_button("Download Savings Report (CSV)", df_summary.to_csv(index=False), file_name="cumulative_savings.csv")
