import streamlit as st
import pandas as pd
import random 


# Deck of cards
class Deck: 
    def __init__(self):
        self.suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
        self.ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        self.cards = [f"{rank} of {suit}" for suit in self.suits for rank in self.ranks]


def to_dataframe(self):
        return pd.DataFrame({
            "Rank": [card.rank for card in self.cards],
            "Suit": [card.suit for card in self.cards],
            "Card": [str(card) for card in self.cards]
        })


st.title("PokerStars")
st.write("This is a simple Streamlit app to display poker data.")
deck = Deck().cards

if st.button("Shuffle Deck"):
    random.shuffle(deck)
    st.write("Deck shuffled!")

df = pd.DataFrame({
    "Card": deck
})
st.dataframe(df)