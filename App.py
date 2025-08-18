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
        # Using LIKE with % for partial matches in both location and zone
        query = f"SELECT * FROM delivery_fees WHERE location LIKE '%{search_query}%' OR zone LIKE '%{search_query}%'"
    else:
        query = "SELECT * FROM delivery_fees"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_all_locations_list():
    """Retrieves a list of all unique locations from the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("SELECT DISTINCT location FROM delivery_fees ORDER BY location")
    locations = [row[0] for row in c.fetchall()]
    conn.close()
    return locations

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
            return f"Delivery Charge: ${charge:.2f}"
        else:
            return f"Minimum Order Amount of ${min_order:.2f} not met. Delivery Charge: ${charge:.2f}"
    else:
        return "Location not found in database."

# --- Streamlit App Layout ---
st.set_page_config(layout="wide", page_title="Delivery Fee Tracker 🚚")

# Custom CSS for a professional look with dark mode adaptation:
st.markdown(
    """
    <style>
    /* Light Mode Default Styles */
    .stApp {
        background-color: #F8F9FA; /* A very light, clean gray, close to white */
        color: #343A40; /* Darker gray for primary text for better contrast */
    }

    /* Set color for labels and general text within Streamlit components */
    div.stTextInput label, div.stNumberInput label, div.stSelectbox label,
    div.stTextInput input, div.stNumberInput input, div.stSelectbox div[data-baseweb="select"] {
        color: #343A40; /* Darker text for labels */
    }
    
    /* Ensure input fields and selectboxes have a white background and standard border */
    div.stTextInput div[data-baseweb="input"],
    div.stNumberInput div[data-baseweb="input"],
    div.stSelectbox div[data-baseweb="select"] {
        background-color: #FFFFFF; /* White background for text boxes */
        border: 1px solid #CED4DA; /* Standard light gray border */
        border-radius: 0.25rem; /* Slightly rounded corners */
    }

    /* Style for the selectbox dropdown options, ensuring black text on white */
    div[data-baseweb="popover"] ul li {
        color: #343A40;
        background-color: #FFFFFF;
    }

    /* Professional styling for buttons */
    .stButton>button {
        background-color: #007BFF; /* A clean blue */
        color: white;
        border: none;
        padding: 0.6em 1.2em;
        border-radius: 0.25rem;
        cursor: pointer;
        font-weight: bold;
        transition: background-color 0.2s ease;
    }

    .stButton>button:hover {
        background-color: #0056b3; /* Darker blue on hover */
    }

    /* General text and headers */
    h1, h2, h3, h4, h5, h6 {
        color: #212529; /* Even darker gray for headings */
        font-weight: 600; /* Slightly bolder headings */
    }

    p, li {
        color: #343A40;
    }

    /* Improve tab styling for a professional look */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #E9ECEF; /* Light gray for inactive tabs */
        border-radius: 0.25rem 0.25rem 0 0;
        padding: 0.6rem 1rem;
        font-weight: 500;
        color: #495057; /* Darker gray for tab text */
        transition: background-color 0.2s ease, color 0.2s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background-color: #DEE2E6; /* Slightly darker on hover */
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #FFFFFF; /* White for active tab */
        color: #007BFF; /* Blue for active tab text */
        border-bottom: 3px solid #007BFF; /* Blue underline for active tab */
        font-weight: 600;
    }

    /* --- Dark Mode Styles --- */
    @media (prefers-color-scheme: dark) {
        .stApp {
            background-color: #212529; /* Darker background for dark mode */
            color: #F8F9FA; /* Lighter text for dark mode */
        }

        div.stTextInput label, div.stNumberInput label, div.stSelectbox label,
        div.stTextInput input, div.stNumberInput input, div.stSelectbox div[data-baseweb="select"] {
            color: #E9ECEF; /* Lighter text for labels in dark mode */
        }
        
        div.stTextInput div[data-baseweb="input"],
        div.stNumberInput div[data-baseweb="input"],
        div.stSelectbox div[data-baseweb="select"] {
            background-color: #343A40; /* Darker background for input boxes in dark mode */
            border: 1px solid #6C757D; /* Lighter border for dark mode */
        }

        div[data-baseweb="popover"] ul li {
            color: #E9ECEF;
            background-color: #343A40;
        }

        .stButton>button {
            background-color: #0056b3; /* Slightly darker blue for buttons in dark mode */
            color: white;
        }
        .stButton>button:hover {
            background-color: #004085; /* Even darker blue on hover in dark mode */
        }

        h1, h2, h3, h4, h5, h6 {
            color: #F8F9FA; /* Lighter headings for dark mode */
        }

        p, li {
            color: #F8F9FA;
        }

        .stTabs [data-baseweb="tab"] {
            background-color: #343A40; /* Darker gray for inactive tabs in dark mode */
            color: #ADB5BD; /* Lighter gray for tab text in dark mode */
        }

        .stTabs [data-baseweb="tab"]:hover {
            background-color: #495057; /* Slightly lighter on hover in dark mode */
        }

        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: #212529; /* Dark background for active tab in dark mode */
            color: #0099FF; /* Brighter blue for active tab text in dark mode */
            border-bottom: 3px solid #0099FF; /* Brighter blue underline */
        }
    }

    /* Hide Streamlit's "Made with Streamlit" header badge */
    [data-testid="stHeader"] {
        display: none !important;
    }

    /* Hide Streamlit's "Made with Streamlit" footer text */
    [data-testid="stFooter"] {
        display: none !important;
    }

    /* Hide the hamburger menu and the app title in the header if desired */
    /* Note: Hiding stToolbar will also hide the default app title and menu button */
    [data-testid="stToolbar"] {
        visibility: hidden !important;
        height: 0 !important;
        position: fixed !important; /* Prevents layout shift */
    }

    </style>
    """,
    unsafe_allow_html=True
)

st.title("🚚 Delivery Fee Tracker")
st.markdown("---")

# Initialize the database on first run
init_db()

# --- Initialize session state for calculation inputs ---
if 'calc_location_selected_index' not in st.session_state:
    st.session_state.calc_location_selected_index = 0
if 'calc_order_amount_value' not in st.session_state:
    st.session_state.calc_order_amount_value = 0.0
if 'fee_calculation_result' not in st.session_state:
    st.session_state.fee_calculation_result = ""
if 'selected_location_for_edit_delete' not in st.session_state:
    st.session_state.selected_location_for_edit_delete = None


# --- Tabs for different functionalities ---
tab_search, tab_add, tab_edit, tab_calculate, tab_about = st.tabs(["Search Delivery Fee", "Add Entry", "Edit/Delete Entry", "Calculate Fee", "About"])

with tab_search:
    st.header("Search Delivery Fee")

    st.subheader("Existing Delivery Fee Data")
    
    # Real-time search bar (not in a form)
    search_query = st.text_input("Search by Location or Zone (Type to filter)", key="search_bar")

    # Display current data, filtered by search query
    df = get_all_entries(search_query)
    st.dataframe(df, use_container_width=True)

    # Note: Update and Delete functionality moved to a separate tab
    st.info("To update or delete an entry, please navigate to the 'Edit/Delete Entry' tab.")

with tab_add:
    st.header("Add New Delivery Fee Entry")

    with st.form("add_form", clear_on_submit=True):
        new_location = st.text_input("Location", key="add_location_text_input_field")
        
        col2, col3 = st.columns(2)
        with col2:
            new_min_order = st.number_input("Minimum Order Amount ($)", min_value=0.0, format="%.2f", key="add_min_order")
        with col3:
            new_delivery_charge = st.number_input("Delivery Charge ($)", min_value=0.0, format="%.2f", key="add_delivery_charge")
        
        col4, col5 = st.columns(2)
        with col4:
            new_free_delivery_amount = st.number_input("Amount for Free Delivery ($)", min_value=0.0, format="%.2f", key="add_free_delivery_amount")
        with col5:
            new_zone = st.text_input("Zone (e.g., North, South)", key="add_zone")
        
        add_submitted = st.form_submit_button("Add Entry")
        if add_submitted:
            if new_location and new_min_order is not None and new_delivery_charge is not None and new_free_delivery_amount is not None:
                if add_entry(new_location, new_min_order, new_delivery_charge, new_free_delivery_amount, new_zone):
                    st.success(f"Entry for {new_location} added successfully!")
                    st.rerun() # Rerun to update table on other tabs
            else:
                st.error("Please fill in all required fields (Location, Minimum Order Amount, Delivery Charge, Amount for Free Delivery).")


with tab_edit:
    st.header("Edit or Delete Delivery Fee Entry")

    df = get_all_entries() # Get all entries for selection in this tab
    if not df.empty:
        location_to_id = {row['location']: row['id'] for index, row in df.iterrows()}
        current_options = list(location_to_id.keys())
        
        # Ensure selected_location for edit/delete persists or defaults appropriately
        default_edit_delete_index = 0
        if st.session_state.selected_location_for_edit_delete in current_options:
            default_edit_delete_index = current_options.index(st.session_state.selected_location_for_edit_delete)
        # If the previous selection is no longer in current_options, default_edit_delete_index remains 0

        selected_location_value = st.selectbox(
            "Select Location to Update/Delete",
            options=current_options,
            key="select_update_delete",
            index=default_edit_delete_index
        )
        st.session_state.selected_location_for_edit_delete = selected_location_value # Store the selected *value*

        selected_id = location_to_id.get(selected_location_value) # Use selected_location_value here

        if selected_id:
            # Pre-fill update form with selected entry's data
            selected_entry = df[df['id'] == selected_id].iloc[0]
            
            with st.form("update_delete_form"):
                col1_upd, col2_upd, col3_upd = st.columns(3)
                with col1_upd:
                    update_location = st.text_input("Location", value=selected_entry['location'], key="upd_location")
                with col2_upd:
                    update_min_order = st.number_input("Minimum Order Amount ($)", min_value=0.0, value=float(selected_entry['min_order_amount']), format="%.2f", key="upd_min_order")
                with col3_upd:
                    update_delivery_charge = st.number_input("Delivery Charge ($)", min_value=0.0, value=float(selected_entry['delivery_charge']), format="%.2f", key="upd_delivery_charge")
                
                col4_upd, col5_upd = st.columns(2)
                with col4_upd:
                    update_free_delivery_amount = st.number_input("Amount for Free Delivery ($)", min_value=0.0, value=float(selected_entry['amount_for_free_delivery']), format="%.2f", key="upd_free_delivery_amount")
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
                    st.session_state.selected_location_for_edit_delete = None # Clear selection after deletion
                    st.rerun() # Rerun to refresh the dataframe and selectbox
        else:
            st.info("No entry selected or no matching entries found for update/delete.")
    else:
        st.info("No delivery fee entries yet. Add some in the 'Add Entry' tab!")

with tab_calculate:
    st.header("Calculate Delivery Fee")
    all_locations = get_all_entries()['location'].tolist() # Get all locations regardless of search
    if all_locations:
        # Set default index for selectbox based on session state
        default_calc_index = 0
        if isinstance(st.session_state.calc_location_selected_index, int) and \
           0 <= st.session_state.calc_location_selected_index < len(all_locations):
            default_calc_index = st.session_state.calc_location_selected_index

        selected_calc_location = st.selectbox(
            "Select Location",
            options=all_locations,
            key="calc_location",
            index=default_calc_index
        )
        
        # Update the session state index based on the actual selected *value*
        if selected_calc_location:
            try:
                st.session_state.calc_location_selected_index = all_locations.index(selected_calc_location)
            except ValueError:
                # Should not happen if selected_calc_location comes from all_locations
                st.session_state.calc_location_selected_index = 0
        else:
            st.session_state.calc_location_selected_index = 0

        calc_order_amount = st.number_input(
            "Enter Order Amount ($)",
            min_value=0.0,
            format="%.2f",
            key="calc_order_amount",
            value=st.session_state.calc_order_amount_value
        )
        
        # Only one button now: Calculate Fee
        if st.button("Calculate Fee"):
            if selected_calc_location and calc_order_amount is not None:
                st.session_state.fee_calculation_result = get_fee_for_location(selected_calc_location, calc_order_amount)
                st.info(f"For an order of ${calc_order_amount:.2f} in {selected_calc_location}: {st.session_state.fee_calculation_result}")
            else:
                st.error("Please select a location and enter an order amount.")
        
        # Display the fee calculation result persistently
        if st.session_state.fee_calculation_result:
            # Re-display the result if it was set, using the actual selected location string
            if selected_calc_location: # Ensure selected_calc_location is not None before displaying
                st.info(f"For an order of ${st.session_state.calc_order_amount_value:.2f} in {selected_calc_location}: {st.session_state.fee_calculation_result}")

    else:
        st.warning("No locations available to calculate fees. Please add locations in the 'Add Entry' tab first.")

with tab_about:
    st.header("About This App")
    st.markdown("""
    This application helps you manage and calculate delivery fees based on different locations.
    It stores the data locally using **SQLite3**, provides a user-friendly interface with **Streamlit**,
    and is built using **Python**.

    **Features:**
    - Add new delivery fee entries (Location, Minimum Order Amount, Delivery Charge, Amount for Free Delivery, Zone).
    - View all existing delivery fee data.
    - Update details of existing entries.
    - Delete entries.
    - Calculate delivery fees based on a selected location and order amount.
    - Real-time search for entries by Location or Zone.

    **How to use:**
    1.  **Search Delivery Fee:** Use this tab to view and search existing delivery fee records.
    2.  **Add Entry:** Use this tab to add new delivery fee records.
    3.  **Edit/Delete Entry:** Use this tab to update or delete specific delivery fee records.
    4.  **Calculate Fee:** Use this tab to quickly check the delivery fee for a specific location and order amount.
    """)
