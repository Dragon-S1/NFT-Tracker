import streamlit as st
import requests
import pandas as pd
import time

class NFTTrackerApp:
    def __init__(self):
        # Set up Streamlit page title and layout
        st.set_page_config(page_title="NFT Tracker", layout="wide")

        # Table headers
        self.columns = ["Name", "Rarity", "Max Quantity", "Current Quantity", "Price (USDC)", "Price (MCG)", "Availability"]

        # Display a title on the Streamlit app
        st.title("NFT Tracker")

        # Create a placeholder for the table, so it can be replaced on each refresh
        self.table_placeholder = st.empty()

        # Initialize previous availability data
        self.prev_availability = {}

        # Initially fetch NFT data
        self.fetch_nft_data()

    def fetch_nft_data(self):
        url = "https://api.gameshift.dev/internal/storefront/skus-with-inventory"
        headers = {
            "x-api-key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXkiOiI0OTY5ZjE3My02ZDdlLTRiNWQtYjU3Mi1kNThlNDZiMTI3YTYiLCJzdWIiOiJlOTg2ZDU0YS1lMTNjLTQxNmUtOGYyMC0wNzZjYzRhYzRjYmIiLCJpYXQiOjE3MzM5NTcxNDV9.GO89nxfK-2bfIELfFZjFCXL6vjqsXw-C1HP4aSKftTU"
        }

        try:
            response = requests.get(url, headers=headers, params={"perPage": 100})
            response.raise_for_status()
            data = response.json()["data"]

            # Create a dictionary to store the combined data by NFT name
            nft_dict = {}

            # Consolidate NFTs by name
            for item in data:
                if item["type"] == "NewMintUniqueAsset":
                    nft_name = item["name"]
                    max_quantity = item["inventory"].get("maxQuantity", "Unlimited")
                    current_quantity = item["inventory"]["currentQuantity"]
                    rarity = self.get_rarity(item["inventory"]["attributes"])

                    # Initialize entry if not already in the dictionary
                    if nft_name not in nft_dict:
                        nft_dict[nft_name] = {
                            "Name": nft_name,
                            "Rarity": rarity,
                            "Max Quantity": max_quantity,
                            "Current Quantity": current_quantity,
                            "Price (USDC)": None,
                            "Price (MCG)": None,
                            "Availability": "",
                        }

                    # Add prices based on currencyId
                    if item["price"]["currencyId"] == "USDC":
                        nft_dict[nft_name]["Price (USDC)"] = item["price"]["naturalAmount"]
                    elif item["price"]["currencyId"] == "425fdb36-e222-4e09-be33-b42ce38788ca":
                        nft_dict[nft_name]["Price (MCG)"] = item["price"]["naturalAmount"]

                    # Calculate Availability
                    if max_quantity != "Unlimited":
                        ratio = current_quantity / max_quantity
                        if ratio < 0.2:
                            availability = "High"
                        elif ratio < 0.5:
                            availability = "Medium"
                        elif ratio < 0.8:
                            availability = "Low"
                        else:
                            availability = "Sold Out"
                    else:
                        availability = "Unlimited"

                    nft_dict[nft_name]["Availability"] = availability

            # Convert the combined dictionary into a pandas DataFrame
            nft_df = pd.DataFrame(nft_dict.values())

            # Check if availability has changed, if so, play a sound notification
            self.check_availability_changes(nft_dict)

            # Apply conditional row styling based on availability
            def apply_row_style(row):
                if row['Availability'] == "High":
                    return ['background-color: rgba(56, 142, 60, 0.5); text-align: left'] * len(row)  # Dark Green with 50% opacity
                elif row['Availability'] == "Medium":
                    return ['background-color: rgba(251, 192, 45, 0.5); text-align: left'] * len(row)  # Dark Yellow with 50% opacity
                elif row['Availability'] == "Low":
                    return ['background-color: rgba(245, 124, 0, 0.5); text-align: left'] * len(row)  # Dark Orange with 50% opacity
                elif row['Availability'] == "Sold Out":
                    return ['background-color: rgba(211, 47, 47, 0.5); text-align: left'] * len(row)  # Dark Red with 50% opacity
                else:
                    return ['text-align: left'] * len(row)

            # Apply the style to the DataFrame
            styled_df = nft_df.style.apply(apply_row_style, axis=1).set_properties(**{'text-align': 'left'})

            # Clear the previous table content
            self.table_placeholder.empty()

            # Display the styled DataFrame with highlighting
            self.table_placeholder.dataframe(styled_df, use_container_width=True, height=750)  # Set height to avoid scroll bar

            # Add the audio notification if there's a change in availability
            self.play_audio_notification()

        except requests.RequestException as e:
            st.error(f"Failed to fetch data: {e}")

        # Refresh every 30 seconds by re-running the function
        time.sleep(30)  # Delay for 30 seconds
        self.fetch_nft_data()  # Recursively call the fetch function to keep it updating

    def get_rarity(self, attributes):
        """Extracts the rarity from the attributes list."""
        for attribute in attributes:
            if attribute["traitType"] == "Rarity":
                return attribute["value"]
        return "Unknown"  # Return 'Unknown' if rarity is not found

    def check_availability_changes(self, nft_dict):
        """Check if availability has changed."""
        for nft_name, nft_data in nft_dict.items():
            current_availability = nft_data["Availability"]
            if nft_name in self.prev_availability:
                prev_availability = self.prev_availability[nft_name]
                # If availability changed, update the state and flag it for audio
                if current_availability != prev_availability:
                    self.availability_changed = True
            # Update previous availability
            self.prev_availability[nft_name] = current_availability

    def play_audio_notification(self):
        """Play an audio notification if availability changed."""
        if hasattr(self, 'availability_changed') and self.availability_changed:
            st.markdown("""
            <audio autoplay>
                <source src="https://www.soundjay.com/button/beep-07.wav" type="audio/wav">
            </audio>
            """, unsafe_allow_html=True)
            self.availability_changed = False  # Reset the flag

if __name__ == "__main__":
    # Initialize the app
    NFTTrackerApp()
