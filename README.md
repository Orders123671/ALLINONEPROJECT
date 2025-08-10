# ALLINONEPROJECT
import streamlit as st
import sqlite3
import pandas as pd

# --- Database Management ---
DATABASE_NAME = "delivery_fees.db"

def init_db():
    """Initializes the SQLite database and creates the delivery_fees table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS delivery_fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT NOT NULL UNIQUE,
            min_order_amount REAL NOT NULL,
            delivery_charge REAL NOT NULL,
            amount_for_free_delivery REAL,
            zone TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_entry(location, min_order_amount, delivery_charge, amount_for_free_delivery, zone):
    """Adds a new delivery fee entry to the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO delivery_fees (location, min_order_amount, delivery_charge, amount_for_free_delivery, zone)
            VALUES (?, ?, ?, ?, ?)
        ''', (location, min_order_amount, delivery_charge, amount_for_free_delivery, zone))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        st.error(f"Error: Location '{location}' already exists. Please choose a unique location or update the existing one.")
        return False
    finally:
        conn.close()

def get_all_entries(search_query=""):
    """
    Retrieves all delivery fee entries from the database,
    optionally filtering by location or zone.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    if search_query:
        query = f"SELECT * FROM delivery_fees WHERE location LIKE '%{search_query}%' OR zone LIKE '%{search_query}%'"
    else:
        query = "SELECT * FROM delivery_fees"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def update_entry(entry_id, location, min_order_amount, delivery_charge, amount_for_free_delivery, zone):
    """Updates an existing delivery fee entry in the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    try:
        c.execute('''
            UPDATE delivery_fees
            SET location = ?, min_order_amount = ?, delivery_charge = ?, amount_for_free_delivery = ?, zone = ?
            WHERE id = ?
        ''', (location, min_order_amount, delivery_charge, amount_for_free_delivery, zone, entry_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        st.error(f"Error: Location '{location}' already exists for another entry. Please choose a unique location.")
        return False
    finally:
        conn.close()

def delete_entry(entry_id):
    """Deletes a delivery fee entry from the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM delivery_fees WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()

def get_fee_for_location(location, order_amount):
    """Calculates the delivery fee for a given location and order amount."""
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("SELECT min_order_amount, delivery_charge, amount_for_free_delivery FROM delivery_fees WHERE location = ?", (location,))
    result = c.fetchone()
    conn.close()

    if result:
        min_order, charge, free_delivery_amount = result
        if order_amount >= free_delivery_amount:
            return "Free Delivery (Order amount qualifies)"
        elif order_amount >= min_order:
            return f"Delivery Charge: AED{charge:.2f}"
        else:
            return f"Minimum Order Amount of AED{min_order:.2f} not met. Delivery Charge: AED{charge:.2f}"
    else:
        return "Location not found in database."

# --- Streamlit App Layout ---
st.set_page_config(layout="wide", page_title="Delivery Fee Tracker 🚚")

st.title("🚚 Katrina Delivery Fee Tracker")
st.markdown("---")

# Initialize the database on first run
init_db()

# --- Tabs for different functionalities ---
tab1, tab2, tab3 = st.tabs(["Manage Fees", "Calculate Fee", "About"])

with tab1:
    st.header("Manage Delivery Fees")

    st.subheader("Add New Entry")
    with st.form("add_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            new_location = st.text_input("Location", key="add_location")
        with col2:
            new_min_order = st.number_input("Minimum Order Amount (AED)", min_value=0.0, format="%.2f", key="add_min_order")
        with col3:
            new_delivery_charge = st.number_input("Delivery Charge (AED)", min_value=0.0, format="%.2f", key="add_delivery_charge")
        
        col4, col5 = st.columns(2)
        with col4:
            new_free_delivery_amount = st.number_input("Amount for Free Delivery (AED)", min_value=0.0, format="%.2f", key="add_free_delivery_amount")
        with col5:
            new_zone = st.text_input("Zone", key="add_zone")
        
        add_submitted = st.form_submit_button("Add Entry")
        if add_submitted:
            if new_location and new_min_order is not None and new_delivery_charge is not None and new_free_delivery_amount is not None:
                if add_entry(new_location, new_min_order, new_delivery_charge, new_free_delivery_amount, new_zone):
                    st.success(f"Entry for {new_location} added successfully!")
            else:
                st.error("Please fill in all required fields (Location, Minimum Order Amount, Delivery Charge, Amount for Free Delivery).")

    st.markdown("---")
    st.subheader("Existing Delivery Fee Data")
    
    # Add search bar
    search_query = st.text_input("Search by Location or Zone", key="search_bar")

    # Display current data, filtered by search query
    df = get_all_entries(search_query)
    st.dataframe(df, use_container_width=True)

    st.markdown("---")
    st.subheader("Update or Delete Entry")

    if not df.empty:
        # Create a dictionary for easy lookup of IDs based on displayed locations
        # This now uses the potentially filtered DataFrame
        location_to_id = {row['location']: row['id'] for index, row in df.iterrows()}
        
        # Ensure selected_location is in the currently filtered list if a search is active
        # Otherwise, pick the first item if list is not empty
        if selected_location := st.selectbox("Select Location to Update/Delete", options=list(location_to_id.keys()), key="select_update_delete"):
            selected_id = location_to_id.get(selected_location)

            if selected_id:
                # Pre-fill update form with selected entry's data
                selected_entry = df[df['id'] == selected_id].iloc[0]
                
                with st.form("update_delete_form"):
                    col1_upd, col2_upd, col3_upd = st.columns(3)
                    with col1_upd:
                        update_location = st.text_input("Location", value=selected_entry['location'], key="upd_location")
                    with col2_upd:
                        update_min_order = st.number_input("Minimum Order Amount (AED)", min_value=0.0, value=float(selected_entry['min_order_amount']), format="%.2f", key="upd_min_order")
                    with col3_upd:
                        update_delivery_charge = st.number_input("Delivery Charge (AED)", min_value=0.0, value=float(selected_entry['delivery_charge']), format="%.2f", key="upd_delivery_charge")
                    
                    col4_upd, col5_upd = st.columns(2)
                    with col4_upd:
                        update_free_delivery_amount = st.number_input("Amount for Free Delivery (AED)", min_value=0.0, value=float(selected_entry['amount_for_free_delivery']), format="%.2f", key="upd_free_delivery_amount")
                    with col5_upd:
                        update_zone = st.text_input("Zone", value=selected_entry['zone'] if pd.notna(selected_entry['zone']) else "", key="upd_zone") # Handle NaN for zone
                    
                    col_buttons = st.columns(2)
                    with col_buttons[0]:
                        update_submitted = st.form_submit_button("Update Entry")
                    with col_buttons[1]:
                        delete_submitted = st.form_submit_button("Delete Entry")

                    if update_submitted:
                        if update_location and update_min_order is not None and update_delivery_charge is not None and update_free_delivery_amount is not None:
                            if update_entry(selected_id, update_location, update_min_order, update_delivery_charge, update_free_delivery_amount, update_zone):
                                st.success(f"Entry for {update_location} updated successfully!")
                                st.rerun() # Rerun to refresh the dataframe
                        else:
                            st.error("Please fill in all required fields for update.")
                    elif delete_submitted:
                        delete_entry(selected_id)
                        st.success(f"Entry for {selected_entry['location']} deleted successfully!")
                        st.rerun() # Rerun to refresh the dataframe
        else:
            st.info("No matching entries for update/delete based on your search.")
    else:
        st.info("No delivery fee entries yet. Add some above!")


with tab2:
    st.header("Calculate Delivery Fee")
    all_locations = get_all_entries()['location'].tolist() # Get all locations regardless of search
    if all_locations:
        calc_location = st.selectbox("Select Location", options=all_locations, key="calc_location")
        calc_order_amount = st.number_input("Enter Order Amount (AED)", min_value=0.0, format="%.2f", key="calc_order_amount")
        
        if st.button("Calculate Fee"):
            if calc_location and calc_order_amount is not None:
                fee_info = get_fee_for_location(calc_location, calc_order_amount)
                st.info(f"For an order of AED{calc_order_amount:.2f} in {calc_location}: {fee_info}")
            else:
                st.error("Please select a location and enter an order amount.")
    else:
        st.warning("No locations available to calculate fees. Please add locations in the 'Manage Fees' tab first.")

with tab3:
    st.header("About This App")
    st.markdown("""

    **Features:**
    - Add new delivery fee entries (Location, Minimum Order Amount, Delivery Charge, Amount for Free Delivery, Zone).
    - View all existing delivery fee data.
    - Update details of existing entries.
    - Delete entries.
    - Calculate delivery fees based on a selected location and order amount.
    - **New: Search for entries by Location or Zone!**

    **How to use:**
    1.  **Manage Fees:** Use this tab to add, view, update, or delete delivery fee records. You can now use the search bar to filter entries.
    2.  **Calculate Fee:** Use this tab to quickly check the delivery fee for a specific location and order amount.
    """)
