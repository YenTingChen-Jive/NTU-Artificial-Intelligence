# Reference: https://www.data-blogger.com/pokerbot-create-your-poker-ai-bot-in-python/
# Based On This Method, With Further Modifications To Improve Win Rate

from game.engine.hand_evaluator import HandEvaluator
from game.players import BasePokerPlayer

import random

from game.engine.card import Card
from game.engine.deck import Deck
from game.engine.hand_evaluator import HandEvaluator

def gen_cards(cards_str):
    return [Card.from_str(s) for s in cards_str]

def _fill_community_card(base_cards, used_card):
    need_num = 5 - len(base_cards)
    return base_cards + _pick_unused_card(need_num, used_card)

def _pick_unused_card(card_num, used_card):
    used = [card.to_id() for card in used_card]
    unused = [card_id for card_id in range(1, 53) if card_id not in used]
    choiced = random.sample(unused, card_num)
    return [Card.from_id(card_id) for card_id in choiced]

# Estimate the ratio of winning games given the current state of the game
def estimate_win_rate(nb_simulation, nb_player, hole_card, community_card=None):
    if not community_card: community_card = []

    # Make lists of Card objects out of the list of cards
    community_card = gen_cards(community_card)
    hole_card = gen_cards(hole_card)

    # Estimate the win count by doing a Monte Carlo simulation
    win_count = sum([montecarlo_simulation(nb_player, hole_card, community_card) for _ in range(nb_simulation)])
    return 1.0 * win_count / nb_simulation

def montecarlo_simulation(nb_player, hole_card, community_card):
    # Do a Monte Carlo simulation given the current state of the game by evaluating the hands
    community_card = _fill_community_card(community_card, used_card=hole_card + community_card)
    unused_cards = _pick_unused_card((nb_player - 1) * 2, hole_card + community_card)
    opponents_hole = [unused_cards[2 * i:2 * i + 2] for i in range(nb_player - 1)]
    opponents_score = [HandEvaluator.eval_hand(hole, community_card) for hole in opponents_hole]
    my_score = HandEvaluator.eval_hand(hole_card, community_card)
    return 1 if my_score >= max(opponents_score) else 0



class MyPlayer(BasePokerPlayer):

    def __init__(self):
        super().__init__()
        self.wins = 0
        self.losses = 0

    def declare_action(self, valid_actions, hole_card, round_state):
        # Estimate the win rate
        win_rate = estimate_win_rate(500, self.num_players, hole_card, round_state['community_card'])

        # Check whether it is possible to call
        can_call = len([item for item in valid_actions if item['action'] == 'call']) > 0
        if can_call:
            # If so, compute the amount that needs to be called
            call_amount = [item for item in valid_actions if item['action'] == 'call'][0]['amount']
        else:
            call_amount = 0

        # Check whether it is possible to raise
        can_raise = len([item for item in valid_actions if item['action'] == 'raise']) > 0

        amount = None

        # If the win rate is large enough, then raise
        if win_rate > 0.5:
            raise_amount_options = [item for item in valid_actions if item['action'] == 'raise'][0]['amount']
            if win_rate > 0.85:
                # If it is extremely likely to win, then all-in
                if can_raise:
                    action = 'raise'
                    amount = raise_amount_options['max']
                else:
                    action = 'call'
                    amount = call_amount
            elif win_rate > 0.75:
                # If it is likely to win, then raise by the minimum amount possible
                if can_raise:
                    action = 'raise'
                    amount = raise_amount_options['min']
                else:
                    action = 'call'
                    amount = call_amount
            else:
                if can_call and call_amount <= 100:
                    action = 'call'
                    amount = call_amount
                else:
                    action = 'fold'
        else:
            # If win_rate < 50%, then either call or fold. 
            action = 'fold'

        # Set the amount
        if amount is None:
            items = [item for item in valid_actions if item['action'] == action]
            amount = items[0]['amount']

        return action, amount

    def receive_game_start_message(self, game_info):
        self.num_players = game_info['player_num']

    def receive_round_start_message(self, round_count, hole_card, seats):
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        is_winner = self.uuid in [item['uuid'] for item in winners]
        self.wins += int(is_winner)
        self.losses += int(not is_winner)


def setup_ai():
    return MyPlayer()