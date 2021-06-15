import pybithumb
from common.utils import *

# def _create_bithumb_api() -> object:
"""
빗썸 private api 생성
:return: api 객체
"""
bit_keys: dict = read_bithumb_key('.env.local')
secretKey, connectKey = tuple(bit_keys.values())
bithumb = pybithumb.Bithumb(connectKey, secretKey)


# return bithumb


# bithumb = _create_bithumb_api()


def is_in_market(ticker: str) -> bool:
    """ 해당 코인티커가 빗썸시장에 상장되어 있는지 확인 체크 """
    all_tickers = pybithumb.get_tickers()
    return ticker in all_tickers


def get_krw_balance() -> tuple:
    """
    보유 원화 금액 조회하기
    :return: 주문 가능 금액
    """
    _balance = bithumb.get_balance('BTC')
    _total_coin, _coin_use_quantity, total_krw, _buy_use_krw = _balance
    # print(f'{total_krw:,}')
    return int(total_krw), int(_buy_use_krw)


def calc_buy_quantity(ticker: str) -> float:
    """
    매수 가능한 수량 계산(수수료 미고려)
    본인 계좌의 원화 잔고를 조회후 최우선 매도 호가금액을 조회후 매수할수 있는 갯수 계산
    :param ticker: 코인티커
    :return: quantity: 주문 가능한 수량
    """
    active_ticker: list = pybithumb.get_tickers()
    if ticker in active_ticker:
        total_krw, use_krw = get_krw_balance()
        order_krw = total_krw - use_krw
        # print(f'보유 원화: {total_krw:,}')
        orderbook: dict = pybithumb.get_orderbook(ticker)
        # 매도 호가
        asks: list = orderbook['asks']
        if (len(asks) > 0) and (order_krw > 0):
            min_sell_price: float = asks[0]['price']
            # print(min_sell_price)
            quantity: float = order_krw / min_sell_price
            return quantity


def buy_limit_price(ticker: str, price: float, quantity: float) -> tuple:
    """
    지정가 매수 주문
    :param ticker:
    :param price:
    :param quantity:
    :return: 주문 정보 ('bid', 'XLM', 'C0504000000166659595', 'KRW')
        주문타입, 코인티커, 주문번호, 주문 통화
    """
    if ticker in pybithumb.get_tickers():
        # 지정가 주문
        total_krw, use_krw = get_krw_balance()
        order_krw = total_krw - use_krw
        orderbook = pybithumb.get_orderbook(ticker)
        asks = orderbook['asks']
        possible_order_quantity = order_krw / asks[0]['price']
        if len(asks) > 0 and order_krw > 0:
            if possible_order_quantity >= quantity:
                order = bithumb.buy_limit_order(ticker, price, quantity)
                return order
            else:
                log('주문가능 수량보다 더 많은 수량을 주문했습니다.')
                log(f'quantity: {quantity}, possible_order_quantity: {possible_order_quantity} ')
                return None
        else:
            log('주문 호가가 존재하지 않습니다.')


def buy_market_price(ticker: str, quantity: float) -> tuple:
    """
    시장가 매수하기
    :param ticker: 코인 티커
    :param quantity:  수량
    :return:  ('bid', 'XLM', 'C0504000000166655824', 'KRW')
    주문타입, 코인티커, 주문번호, 주문에 사용된 통화
    """
    try:
        active_ticker: list = pybithumb.get_tickers()
        if ticker in active_ticker:
            orderbook: dict = pybithumb.get_orderbook(ticker)
            # 매도 호가 목록
            asks: list = orderbook['asks']
            if len(asks) > 0:
                order_no = bithumb.buy_market_order(ticker, quantity)
                return order_no
        return None
    except Exception as e:
        log(f'시장가 매수주문 예외 발생:  {str(e)}')
        traceback.print_exc()


def get_coin_quantity(ticker: str):
    """
     코인 잔고 조회
    :param ticker: 코인티커
    :return: (총 보유수랑, 매수/매도에 사용된 수량)
    """
    if ticker in pybithumb.get_tickers():
        coin_total, coin_use, krw_total, krw_use = bithumb.get_balance(ticker)
        return coin_total, coin_use


def sell_market_price(ticker: str, quantity: float) -> tuple:
    """
    시장가 매도하기
    :param ticker: 코인티커
    :return: 주문 정보
    """
    try:
        coin_total, coin_use = get_coin_quantity(ticker)
        order_coin_qty = coin_total - coin_use
        orderbook: dict = bithumb.get_orderbook(ticker)
        bids: list = orderbook['bids']
        if len(bids) > 0:
            if order_coin_qty >= quantity:
                order = bithumb.sell_market_order(ticker, quantity)  # 시장가 매도
                return order
            else:
                log(f'주문 실패: 주문가능수량:{order_coin_qty}, 요청 수량: {quantity}')
        else:
            log(f'매수 호가가 존재하지 않습니다. {bids}')
    except Exception as e:
        log('지정가 매도 주문 실패 => ', str(e))


def sell_limit_price(ticker: str, price: float, quantity: float) -> tuple:
    """
    지정가 매도
    :param ticker: 코인티커
    :param price: 매도가격
    :param quantity: 수량
    :return: 주문번호
    """
    try:
        coin_total, coin_use = get_coin_quantity(ticker)
        order_coin_qty = coin_total - coin_use
        orderbook: dict = bithumb.get_orderbook(ticker)
        bids: list = orderbook['bids']
        if len(bids) > 0:
            if order_coin_qty >= quantity:
                order = bithumb.sell_limit_order(ticker, price, quantity)
                return order
            else:
                log(f'주문 실패: 주문가능수량:{order_coin_qty}, 요청 수량: {quantity}')
        else:
            log(f'매수 호가가 존재하지 않습니다. {bids}')
    except Exception as e:
        log('지정가 매도 주문 실패 => ', str(e))


def get_my_order_completed_info(order_desc: tuple) -> tuple:
    """
    체결된 주문 내역 조회
    :param order_desc:
        (type: 'bid' or 'ask', ticker, order_id, 통화 )
        ex: ('bid', 'ETH', 'C1231242131', 'KRW')
    :return: tuple
        체결 1건일 경우: (거래타입, 코인티커, 가격, 수량 ,수수료(krw), 거래금액)
        여러건 채결일 경우: (거래타입, 코인티커, 체결평균가격, 총수량, 총수수료, 거래금액)
    """
    try:
        res: dict = bithumb.get_order_completed(order_desc)
        if res['status'] == '0000':
            data: dict = res['data']
            order_type = data['type']
            order_status = data['order_status']
            if order_status == 'Completed':
                ticker = data['order_currency']
                # order_price = data['order_price']  # 시장가 주문시 비어있음
                contract: list = data['contract']
                transaction_krw_amount = 0
                if len(contract) == 1:
                    tr = contract[0]
                    buy_price = float(tr['price'])
                    order_qty = float(tr['units'])
                    fee = float(tr['fee'])
                    transaction_krw_amount = int(tr['total'])
                    return (order_type, ticker, buy_price, order_qty, fee, transaction_krw_amount)
                elif len(contract) > 1:
                    total_order_qty = 0
                    total_fee = 0
                    avg_buy_price = 0
                    for tr in contract:
                        avg_buy_price += float(tr['price'])
                        total_order_qty += float(tr['units'])
                        total_fee += float(tr['fee'])
                        transaction_krw_amount += int(tr['total'])

                    avg_buy_price = avg_buy_price / len(contract)
                    return (order_type, ticker, avg_buy_price, total_order_qty, total_fee, transaction_krw_amount)
            else:
                log(f'체결된 주문내역 상태 확인필요: {order_status}')
                return None

    except Exception as e:
        log(f'체결된 주문 내역 조회 실패 => {str(e)}')
        return None


if __name__ == '__main__':
    # bithumb = _create_bithumb_api()
    print(f'{get_krw_balance():}')
    print('btc 매수 가능 수량:', calc_buy_quantity('BTC'))

    # order_desc = buy_limit_price('XRP', 1020.0, 3)
    # print(order_desc)
    # order_2 = bithumb.buy_limit_order('XRP', 1020.0, 1)
    # print(order_2)

    # order3 = bithumb.buy_market_order('XRP', 1)
    # print(order3)