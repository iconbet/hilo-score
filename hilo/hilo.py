from iconservice import *

TAG = "ICONbet HI-LO"
MAIN_BET_MULTIPLIER = 98.5
BET_MIN = 100000000000000000
CARD_SUITES = [
    '',  # 0
    'HEART',  # 1
    'DIAMOND',  # 2
    'SPADE',  # 3
    'CLUB'  # 4
]

CARD_SUITE_COLORS = [
    '',  # 0
    'RED',  # 1
    'RED',  # 2
    'BLACK',  # 3
    'BLACK'  # 4
]

SIDE_BET_TYPES = {
    1: "COLOR_RED",
    2: "COLOR_BLACK",
    3: "GROUP_FIRST",  # 2-3-4-5
    4: "GROUP_SECOND",  # 6-7-8-9
    5: "GROUP_THIRD",  # J-Q-K-A
}

SIDE_BET_MULTIPLIERS = {
    1: 1.961,
    2: 1.961,
    3: 2.941,
    4: 2.941,
    5: 2.941
}

BET_LIMIT_RATIOS_SIDE_BET = {
    1: 2000000000000000000000,
    2: 2000000000000000000000,
    3: 500000000000000000000,
    4: 500000000000000000000,
    5: 500000000000000000000
}

CARD_TITLES = {
    1: '2',
    2: '3',
    3: '4',
    4: '5',
    5: '6',
    6: '7',
    7: '8',
    8: '9',
    9: 'J',
    10: 'Q',
    11: 'K',
    12: 'A'
}


# An interface to treasury score
class TreasuryInterface(InterfaceScore):
    @interface
    def get_treasury_min(self) -> int:
        pass

    @interface
    def send_wager(self, _amount: int) -> None:
        pass

    @interface
    def wager_payout(self, _payout: int) -> None:
        pass


class HiLo(IconScoreBase):
    _GAME_ON = "game_on"
    _TREASURY_SCORE = "treasury_score"
    _USER_CARD = "user_card"
    _ADMIN_ADDRESS = "Admin_Address"

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        if DEBUG is True:
            Logger.debug(f'In __init__.', TAG)
            Logger.debug(f'owner is {self.owner}.', TAG)
        self._game_on = VarDB(self._GAME_ON, db, value_type=bool)
        self._game_admin = VarDB(self._ADMIN_ADDRESS, db, value_type=Address)
        self._treasury_score = VarDB(self._TREASURY_SCORE, db, value_type=Address)
        self._user_card = DictDB(self._USER_CARD, db, value_type=int)

    @eventlog(indexed=3)
    def BetPlaced(self, amount: int, bet_type: int, prev_card: int):
        pass

    @eventlog(indexed=2)
    def OldCard(self, card_number: str, card_suite: str):
        pass

    @eventlog(indexed=2)
    def NewCard(self, card_number: str, card_suite: str):
        pass

    @eventlog(indexed=2)
    def BetSource(self, _from: Address, timestamp: int):
        pass

    @eventlog(indexed=3)
    def PayoutAmount(self, payout: int, main_bet_payout: int, side_bet_payout: int):
        pass

    @eventlog(indexed=3)
    def BetResult(self, new_card: int, old_card: int, payout: int):
        pass

    @eventlog(indexed=3)
    def DebugPayout(self, payout: int, main_bet_payout: int, side_bet_payout: int):
        pass

    @eventlog(indexed=2)
    def FundTransfer(self, recipient: Address, amount: int, note: str):
        pass

    def on_install(self) -> None:
        super().on_install()
        self._game_on.set(False)

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return TAG

    @external(readonly=True)
    def get_score_owner(self) -> Address:
        """
        A function to return the owner of this score.
        :return: Owner address of this score
        :rtype: :class:`iconservice.base.address.Address`
        """
        return self.owner

    @external
    def set_treasury_score(self, _score: Address) -> None:
        """
        Sets the treasury score address. The function can only be invoked by score owner.
        :param _score: Score address of the treasury
        :type _score: :class:`iconservice.base.address.Address`
        """
        if self.msg.sender != self.owner:
            revert(f"{TAG}: Only owner can set the treasury score.")

        if not _score.is_contract:
            revert(f"{TAG}: {_score} should be a contract address.")

        self._treasury_score.set(_score)

    @external(readonly=True)
    def get_treasury_score(self) -> Address:
        """
        Returns the treasury score address.
        :return: Address of the treasury score
        :rtype: :class:`iconservice.base.address.Address`
        """
        return self._treasury_score.get()

    @external
    def set_game_admin(self, admin_address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'{TAG}: Only the owner can call set_game_admin method')
        self._game_admin.set(admin_address)

    @external(readonly=True)
    def get_game_admin(self) -> Address:
        """
        A function to return the admin of the game
        :return: Address
        """
        return self._game_admin.get()

    @external
    def game_on(self) -> None:
        """
        Set the status of game as on. Only the owner of the game can call this method.
        Owner must have set the treasury score before changing the game status as on.
        """
        if self.msg.sender != self._game_admin.get() and self.msg.sender != self.owner:
            revert(f'{TAG}: Only the owner or admin can call the game_on method')

        if not self._game_on.get() and self._treasury_score.get() is not None:
            self._game_on.set(True)
        else:
            revert(f'{TAG}: Game On Failed.')

    @external
    def game_off(self) -> None:
        """
        Set the status of game as off. Only the owner of the game can call this method.
        """
        if self.msg.sender != self._game_admin.get() and self.msg.sender != self.owner:
            revert(f'{TAG}: Only the owner or admin can call the game_off method')

        if self._game_on.get():
            self._game_on.set(False)
        else:
            revert(f"{TAG}: Game is already off.")

    @external(readonly=True)
    def get_game_on(self) -> bool:
        """
        Returns the current game status
        :return: Current game status
        :rtype: bool
        """
        return self._game_on.get()

    @external
    def clear_user(self) -> bool:
        user_id = self.tx.origin
        self._user_card[user_id] = 0
        return True

    @external
    def untether(self) -> None:
        """
        A function to redefine the value of  self.owner once it is possible .
        To  be included through an update if it is added to ICONSERVICE
        Sets the value of self.owner to the score holding the game treasury
        """
        if self.msg.sender != self.owner:
            revert(f'{TAG}: Only the owner can call the untether method ')
        pass

    @external
    def first_call(self, user_seed: str = '') -> int:
        if self.msg.sender.is_contract:
            revert(f"{TAG}: Contracts are not allowed to play ICONbet Games.")

        self.BetSource(self.tx.origin, self.tx.timestamp)

        if not self._game_on.get():
            Logger.debug(f'Game not active yet.', TAG)
            revert(f'{TAG}: Game not active yet.')

        user_id = self.tx.origin

        if self._user_card[user_id] != 0:
            cardNumber, cardSuite = self.get_real_card(self._user_card[user_id])
            self.NewCard(CARD_TITLES[cardNumber], CARD_SUITES[cardSuite])
            return self._user_card[user_id]

        cardNumber, cardSuite = self.get_random_card(user_seed)
        self._user_card[user_id] = self.get_normalized_card(cardNumber, cardSuite)

        self.NewCard(CARD_TITLES[cardNumber], CARD_SUITES[cardSuite])
        return self._user_card[user_id]

    @payable
    @external
    def call_bet(self, main_bet_type: int, user_seed: str = '', side_bet_amount: int = 0,
                 side_bet_type: int = 0) -> None:
        """
        Main bet function. It takes the upper and lower number for bet. Upper and lower number must be in the range
        [0,99]. The difference between upper and lower can be in the range of [0,95].

        Bet types:
        0 - none
        1 - lower
        2 - upper 
        3 - match
        4 - unmatch

        :param side_bet_type:
        :param side_bet_amount:
        :param main_bet_type: User bet type
        :param user_seed: 'Lucky phrase' provided by user, defaults to ""
        :type user_seed: str,optional
        """

        return self.__bet(main_bet_type, user_seed, side_bet_amount, side_bet_type)

    def __bet(self, main_bet_type: int, user_seed: str, side_bet_amount: int, side_bet_type: int) -> None:
        # Guards
        if self.msg.sender.is_contract:
            revert(f"{TAG}: Contracts are not allowed to play ICONbet Games.")
        if not self._game_on.get():
            Logger.debug(f'Game not active yet.', TAG)
            revert(f'{TAG}: Game not active yet.')

        if main_bet_type == 0 and side_bet_type == 0:
            Logger.debug(f'Need at least one bet(main/side)', TAG)
            revert(f'{TAG}: Need at least one bet(main/side)')

        if not (0 <= main_bet_type <= 4):
            Logger.debug(f'Invalid bet type', TAG)
            revert(f'{TAG}: Invalid bet type')

        if main_bet_type == 4 and side_bet_type != 0:
            Logger.debug(f'Can not play unmatch with side bet!', TAG)
            revert(f'{TAG}: Can not play unmatch with side bet!')

        if (side_bet_type == 0 and side_bet_amount != 0) or (side_bet_type != 0 and side_bet_amount == 0):
            Logger.debug(f'should set both side bet type as well as side bet amount', TAG)
            revert(f'{TAG}: should set both side bet type as well as side bet amount')

        if side_bet_amount < 0:
            revert(f'{TAG}: Side bet amount cannot be negative')

        side_bet_won = False
        side_bet_set = False
        side_bet_payout = 0

        # unmatch is always played with red/black, it is not considered as sidebet!
        if main_bet_type != 4 and side_bet_type != 0 and side_bet_amount != 0:
            side_bet_set = True

        self.BetSource(self.tx.origin, self.tx.timestamp)

        treasury_score = self.create_interface_score(self._treasury_score.get(), TreasuryInterface)
        _treasury_min = treasury_score.get_treasury_min()

        treasury_score.icx(self.msg.value).send_wager(self.msg.value)
        self.FundTransfer(self._treasury_score.get(), self.msg.value, "Sending icx to Treasury")

        user_id = self.tx.origin
        main_bet_amount = self.msg.value - side_bet_amount

        user_prev_card = self._user_card[user_id]
        if user_prev_card == 0:
            # previous card does not exist
            Logger.debug(f'Start game for user first!', TAG)
            revert(f'{TAG}: Start game for user first!')

        oldCardNumber, oldCardSuite = self.get_real_card(user_prev_card)

        self.BetPlaced(main_bet_amount, main_bet_type, user_prev_card)

        if (main_bet_type == 1 and oldCardNumber == 1) or (main_bet_type == 2 and oldCardNumber == 12):
            Logger.debug(f'Invalid main bet!', TAG)
            revert(f'{TAG}: Invalid main bet!')

        if main_bet_type != 0:  # If main bet is played
            main_bet_limit = self.calculate_bet_limit(main_bet_type, oldCardNumber, _treasury_min)
            if main_bet_amount < BET_MIN or main_bet_amount > main_bet_limit:
                Logger.debug(f'Betting amount {main_bet_amount} out of range.', TAG)
                revert(f'{TAG}: Bet amount {main_bet_amount} out of range {BET_MIN},{main_bet_limit} ')

        main_bet_payout = 0
        if main_bet_type != 0:  # If main bet is played
            gap = self.calculate_gap(main_bet_type, oldCardNumber)
            main_bet_payout = self.calculate_bet_payout(gap, main_bet_amount)

        if self.icx.get_balance(self._treasury_score.get()) < main_bet_payout + side_bet_payout:
            Logger.debug(f'Not enough in treasury to make the play.', TAG)
            revert(f'{TAG}: Not enough in treasury to make the play.')

        # Actual bet part
        cardNumber, cardSuite = self.get_random_card(user_seed)
        main_bet_won = False

        if cardNumber < oldCardNumber and main_bet_type == 1:
            main_bet_won = True
        elif cardNumber > oldCardNumber and main_bet_type == 2:
            main_bet_won = True
        elif cardNumber == oldCardNumber and main_bet_type == 3:
            main_bet_won = True
        elif main_bet_type == 4:
            if cardNumber != oldCardNumber:
                main_bet_won = True
            elif CARD_SUITE_COLORS[cardSuite] != CARD_SUITE_COLORS[oldCardSuite]:
                main_bet_won = True

        if side_bet_set:
            side_bet_won = self.check_side_bet_win(side_bet_type, cardNumber, cardSuite)
            if not side_bet_won:
                side_bet_payout = 0
            else:
                if side_bet_type not in SIDE_BET_TYPES:
                    Logger.debug(f'Invalid side bet type', TAG)
                    revert(f'{TAG}: Invalid side bet type.')
                side_bet_limit = int(BET_LIMIT_RATIOS_SIDE_BET[side_bet_type])
                if side_bet_amount < BET_MIN or side_bet_amount > side_bet_limit:
                    Logger.debug(f'Betting amount {side_bet_amount} out of range.', TAG)
                    revert(f'{TAG}: Betting amount {side_bet_amount} out of range ({BET_MIN} ,{side_bet_limit}).')
                side_bet_payout = int(SIDE_BET_MULTIPLIERS[side_bet_type] * 1000) * side_bet_amount // 1000

        normalizedNewCard = self.get_normalized_card(cardNumber, cardSuite)
        Logger.debug(f'Old card: {user_prev_card} new card {normalizedNewCard} has won {main_bet_won} '
                     f'bet amount {main_bet_amount}', TAG)

        self.DebugPayout(main_bet_payout * main_bet_won + side_bet_payout, main_bet_payout, side_bet_payout)

        main_bet_payout = main_bet_payout * main_bet_won
        payout = main_bet_payout + side_bet_payout

        self._user_card[user_id] = normalizedNewCard
        self.BetResult(normalizedNewCard, user_prev_card, payout)
        self.PayoutAmount(payout, main_bet_payout, side_bet_payout)
        self.OldCard(CARD_TITLES[oldCardNumber], CARD_SUITES[oldCardSuite])
        self.NewCard(CARD_TITLES[cardNumber], CARD_SUITES[cardSuite])

        if main_bet_won or side_bet_won:
            Logger.debug(f'Amount owed to winner: {payout}', TAG)
            try:
                Logger.debug(f'Trying to send to ({self.tx.origin}): {payout}.', TAG)
                treasury_score.wager_payout(payout)
                Logger.debug(f'Sent winner ({self.tx.origin}) {payout}.', TAG)
            except BaseException as e:
                Logger.debug(f'Send failed. Exception: {e}', TAG)
                revert(f'{TAG}: Network problem. Winnings not sent. Returning funds.')
        else:
            Logger.debug(f'Player lost. ICX retained in treasury.', TAG)

    def get_random(self, user_seed: str = '') -> float:
        """
        Generates a random # from tx hash, block timestamp and user provided
        seed. The block timestamp provides the source of unpredictability.

        :param user_seed: 'Lucky phrase' provided by user, defaults to ""
        :type user_seed: str,optional
        :return: Number from [x / 100000.0 for x in range(100000)]
        :rtype: float
        """
        Logger.debug(f'Entered get_random.', TAG)
        seed = (str(bytes.hex(self.tx.hash)) + str(self.now()) + user_seed)
        spin = (int.from_bytes(sha3_256(seed.encode()), "big") % 100000) / 100000.0
        Logger.debug(f'Result of the spin was {spin}.', TAG)
        return spin

    def get_random_card(self, user_seed: str = '') -> [int, int]:
        spin = self.get_random(user_seed)
        return self.get_real_card(int(spin * 48) + 1)

    @staticmethod
    def get_normalized_card(cardNumber: int, cardSuite: int) -> int:
        return (cardSuite - 1) * 12 + cardNumber

    def get_real_card(self, cardAsInt: int = 0) -> [int, int]:
        cardMod = cardAsInt % 12
        cardNumber = 12 if cardMod == 0 else cardMod
        cardSuite = self.ceil(cardAsInt / 12)
        return cardNumber, cardSuite

    @staticmethod
    def ceil(number: float) -> int:
        return int(number) + int((number > 0) and (number - int(number)) > 0)

    @external(readonly=True)
    def current_card(self, user_id: Address) -> list:
        # user has no card
        if self._user_card[user_id] == 0:
            return ['-1', '-1']

        cardNumber, cardSuite = self.get_real_card(self._user_card[user_id])
        return [CARD_TITLES[cardNumber], CARD_SUITES[cardSuite]]

    def calculate_bet_limit(self, bet_type: int, user_prev_card_number: int, treasury_min: int) -> int:
        gap = self.calculate_gap(bet_type, user_prev_card_number)

        return int((treasury_min * 1.5 * gap) // (68134 - 681.34 * gap))

    @staticmethod
    def calculate_bet_payout(gap: float, bet_amount: int) -> int:
        return int(int(MAIN_BET_MULTIPLIER * 100) * bet_amount // (100 * gap))

    @staticmethod
    def calculate_gap(bet_type: int, user_prev_card_number: int) -> float:
        if bet_type == 0:  # main bet not played, this should not even be called
            gap = 0
        elif bet_type == 1:  # lower
            gap = user_prev_card_number - 1
        elif bet_type == 2:  # upper
            gap = 12 - user_prev_card_number
        elif bet_type == 3:  # match win rate 1/12
            gap = 1
        elif bet_type == 4:  # unmatch win rate 23/24
            gap = 11.5
        else:
            gap = 0

        # scale from 12 to 100.
        return gap * 100 / 12

    # check for bet limits and side limits
    @staticmethod
    def check_side_bet_win(side_bet_type: int, card_number: int, card_suite: int) -> bool:
        """
        Checks the conditions for side bets are matched or not.
        :param card_suite:
        :param card_number:
        :param side_bet_type: side bet types can be one of this ["digits_match", "icon_logo1","icon_logo2"], defaults to
         ""
        :type side_bet_type: str,optional
        :return: Returns true or false based on the side bet type and the winning number
        :rtype: bool
        """
        if side_bet_type == 1:  # red
            return card_suite in [1, 2]
        elif side_bet_type == 2:  # black
            return card_suite in [3, 4]
        elif side_bet_type == 3:  # group 1-4 (2, 3, 4, 5)
            return card_number in [1, 2, 3, 4]
        elif side_bet_type == 4:  # group 5-8 (6, 7, 8, 9)
            return card_number in [5, 6, 7, 8]
        elif side_bet_type == 5:  # group 9-12 (J, Q, K, A)
            return card_number in [9, 10, 11, 12]
        else:
            return False

    @payable
    def fallback(self):
        pass
