import streamlit as st
import random
import pandas as pd

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def __str__(self):
        return f"{self.rank} of {self.suit}"
    
class Deck:
    suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']

    def __init__(self):
        self.cards = [Card(suit, rank) for suit in self.suits for rank in self.ranks]

    def shuffle(self):
        random.shuffle(self.cards)  

    def deal(self, n=1):
        dealt = self.cards[:n]
        self.cards = self.cards[n:]
        return dealt
    def to_dataframe(self):
        return pd.DataFrame({
            "Rank": [card.rank for card in self.cards],
            "Suit": [card.suit for card in self.cards],
            "Card": [str(card) for card in self.cards]
        })
    
st.title("Poker Engine")
st.write("This is a simple Streamlit app to display poker data.")

if "deck" not in st.session_state:
    st.session_state.deck = Deck()
if st.button("Shuffle Deck"):
    st.session_state.deck.shuffle()
    st.write("Deck shuffled!")
if "player_hand" not in st.session_state:
    st.session_state.player_hand = []
if "community_cards" not in st.session_state:
    st.session_state.community_cards = []

col1, col2, col3, col4 = st.columns(4)

if col1.button("Shuffle Deck"):
    st.session_state.deck = Deck()  # Reset the deck
    st.session_state.deck.shuffle()
    st.session_state.player_hand = []
    st.session_state.community_cards = []
    st.write("Deck shuffled!")

if col2.button("Deal Player Hand"):
    st.session_state.player_hand = st.session_state.deck.deal(2)
    st.write("Player Hand:")
    for card in st.session_state.player_hand:
        st.write(str(card))

if col3.button("Burn & Turn"):
    if len(st.session_state.deck.cards) == 0:
        st.session_state.deck.deal(1) # Burn one card
        st.session_state.community_cards.extend(st.session_state.deck.deal(3)) # Turn the Flop
    elif len(st.session_state.deck.cards) == 3:
        st.session_state.deck.deal(1) # Burn one card
        st.session_state.community_cards.extend(st.session_state.deck.deal(1)) # Turn the Turn 
    elif len(st.session_state.deck.cards) == 4:  
        st.session_state.deck.deal(1) # Burn one card
        st.session_state.community_cards.extend(st.session_state.deck.deal(1)) # Turn the River
    else: 
        st.write("All community cards have already been dealt.")

if col4.button("Reset Game"):
    st.session_state.deck = Deck()  # Reset the deck
    st.session_state.player_hand = []
    st.session_state.community_cards = []
    st.write("Game reset.")

# ------ Display ------
st.subheader("Player Hand")
if st.session_state.player_hand:
    for card in st.session_state.player_hand:
        st.write(str(card))
else:
    st.write("No cards in player hand.")

st.subheader("Community Cards")
if st.session_state.community_cards:
    for card in st.session_state.community_cards:
        st.write(str(card))
else:    
    st.write("No community cards dealt yet.")

st.subheader("Remaining Deck")
st.dataframe(st.session_state.deck.to_dataframe())
