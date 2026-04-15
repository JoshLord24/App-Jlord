import streamlit as st
import pandas as pd
import random 


# Deck of cards
class Deck: 
    def __init__(self):
        self.suits = ["♠️", "♥️", "♦️", "♣️"]
        self.ranks = ["𝟐", "𝟑", "𝟒", "𝟓", "𝟔", "𝟕", "𝟖", "𝟗", "𝟏𝟎", "𝐉", "𝐐", "𝐊", "𝐀"]
        self.cards = [f"{rank} of {suit}" for suit in self.suits for rank in self.ranks]


def to_dataframe(self):
        return pd.DataFrame({
            "Rank": [card.rank for card in self.cards],
            "Suit": [card.suit for card in self.cards],
            "Card": [str(card) for card in self.cards]
        })


st.title("Cards")
st.write("This is a simple Streamlit app to display a deck of cards.")
deck = Deck().cards

if st.button("Shuffle Deck"):
    random.shuffle(deck)
    st.write("Deck shuffled!")

df = pd.DataFrame({
    "Card": deck
})
st.dataframe(df)