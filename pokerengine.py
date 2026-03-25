import streamlit as st
import random
import pandas as pd
from collections import Counter
from itertools import combinations

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def __str__(self):
        return f"{self.rank} of {self.suit}"
    
class Deck:
    suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
    rank_orders = {rank: index for index, rank in enumerate(ranks, start=2)}

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

class HandEvaluator:
    hand_ranks = {
        "High Card": 1,
        "One Pair": 2,
        "Two Pair": 3,
        "Three of a Kind": 4,
        "Straight": 5,
        "Flush": 6,
        "Full House": 7,
        "Four of a Kind": 8,
        "Straight Flush": 9,
        "Royal Flush": 10
    }

    @staticmethod
    def card_value(card):
        return Deck.rank_orders[card.rank]

    def is_straight(values):
        values = sorted(set(values))
        if len(values) < 5:
            return False
        if set ([14, 2, 3, 4, 5]).issubset(values):
            return True
        for i in range(len(values) - 4):
            window = values[i:i+5]
            if window == list(range(window[0], window[0] + 5)):
                return True, window[-1]
        return False
    
    def evaluate_hand(self, hand, community_cards):
        all_cards = hand + community_cards
        values = sorted([self.card_value(card) for card in all_cards], reverse=True)
        suits = [card.suit for card in all_cards]
        counts = Counter(values)
        is_flush = len(set(suits)) == 1
        is_straight, high_straight = HandEvaluator.is_straight(values)

     # Straight Flush / Royal Flush
        if is_flush and is_straight:
            if high_straight == 14:
                return self.hand_ranks["Royal Flush"], [14]
            return self.hand_ranks["Straight Flush"], [high_straight]

        # Four of a Kind
        if 4 in counts.values():
            four = max(k for k, v in counts.items() if v == 4)
            kicker = max(k for k, v in counts.items() if v == 1)
            return self.hand_ranks["Four of a Kind"], [four, kicker]

        # Full House
        if sorted(counts.values()) == [2, 3]:
            three = max(k for k, v in counts.items() if v == 3)
            pair = max(k for k, v in counts.items() if v == 2)
            return self.hand_ranks["Full House"], [three, pair]

        # Flush
        if is_flush:
            return self.hand_ranks["Flush"], values
        # Straight
        if is_straight:
            return self.hand_ranks["Straight"], [high_straight]    


        if 3 in counts.values():
            three = max(k for k, v in counts.items() if v == 3)
            kickers = sorted([k for k, v in counts.items() if v == 1], reverse=True)
            return self.hand_ranks["Three of a Kind"], [three] + kickers

        # Two Pair
        if list(counts.values()).count(2) == 2:
            pairs = sorted([k for k, v in counts.items() if v == 2], reverse=True)
            kicker = max(k for k, v in counts.items() if v == 1)
            return self.hand_ranks["Two Pair"], pairs + [kicker]

        # One Pair
        if 2 in counts.values():
            pair = max(k for k, v in counts.items() if v == 2)
            kickers = sorted([k for k, v in counts.items() if v == 1], reverse=True)
            return self.hand_ranks["One Pair"], [pair] + kickers

        # High Card
        return self.hand_ranks["High Card"], values
        

    @staticmethod
    def best_hand(hand, community_cards):
        all_cards = hand + community_cards
        best_rank = "High Card"
        for combo in combinations(all_cards, 5):
            rank = HandEvaluator().evaluate_hand(list(combo), [])
            if HandEvaluator.hand_ranks[rank] > HandEvaluator.hand_ranks[best_rank]:
                best_rank = rank
        return best_rank

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

# ------ Buttons on Streamlit ------

col1, col2, col3, col4 = st.columns(4)

if col1.button("Shuffle Deck", key="shuffle"):
    st.session_state.deck = Deck()  # Reset the deck
    st.session_state.deck.shuffle()
    st.session_state.player_hand = []
    st.session_state.community_cards = []
    st.write("Deck shuffled!")

if col2.button("Deal Player Hand", key="deal_hand"):
    st.session_state.player_hand = st.session_state.deck.deal(2)
    for card in st.session_state.player_hand:
        st.write(str(card))

if col3.button("Burn + Turn", key="burn_turn"):
    if len(st.session_state.community_cards) == 0:
        st.session_state.deck.deal(1)  # burn
        st.session_state.community_cards.extend(st.session_state.deck.deal(3))  # flop
        st.success("Flop dealt")
    elif len(st.session_state.community_cards) == 3:
        st.session_state.deck.deal(1)  # burn
        st.session_state.community_cards.extend(st.session_state.deck.deal(1))  # turn
        st.success("Turn dealt")
    elif len(st.session_state.community_cards) == 4:
        st.session_state.deck.deal(1)  # burn
        st.session_state.community_cards.extend(st.session_state.deck.deal(1))  # river
        st.success("River dealt")
    else:
        st.warning("All community cards already dealt")

if col4.button("Reset Game", key="reset"):
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

st.subheader("Best Possible Hand")

if st.session_state.player_hand and st.session_state.community_cards:
    all_cards = st.session_state.player_hand + st.session_state.community_cards
    score, best5 = HandEvaluator.best_hand(all_cards)

    rank_name = [name for name, val in HandEvaluator.hand_ranks.items() if val == score[0]][0]

    st.write(f"**Hand Rank:** {rank_name}")
    st.write(f"**Best 5 Cards:** {[str(c) for c in best5]}")
    st.write(f"**Score Details:** {score}")
else:
    st.write("Deal player hand and community cards to evaluate.")

st.subheader("Remaining Deck")
st.dataframe(st.session_state.deck.to_dataframe())
