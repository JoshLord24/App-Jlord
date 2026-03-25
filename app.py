import streamlit as st
import pandas as pd

st.title("PokerStars")
st.write("This is a simple Streamlit app to display poker data.")

# Sample Data
data = {
    "Card": ["Ace of Spades", "King of Hearts", "Queen of Diamonds", "Jack of Clubs"],
    "Value": [14, 13, 12, 11]
}
df = pd.DataFrame(data)
st.subheader("Sample Poker Data")
st.dataframe(df)