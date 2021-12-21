import requests
from django.conf import settings

from core.models.wallets import ThenewbostonWallet

from .models.profile import Profile
from .models.advertisement import Advertisement
from core.utils.shortcuts import convert_to_int, convert_to_decimal
from escrow.models.payment_method import PaymentMethod


def get_or_create_user_profile(user):

    obj, created = Profile.objects.get_or_create(user=user)

    return obj


def create_offer_table(side, number_of_data):

    if side == Advertisement.BUY:
        advertisements = Advertisement.objects.filter(status=Advertisement.OPEN, side=Advertisement.BUY).order_by('-price')[:number_of_data]
    else:
        advertisements = Advertisement.objects.filter(status=Advertisement.OPEN, side=Advertisement.SELL).order_by('price')[:number_of_data]

    message = ""

    for advertisement in reversed(advertisements):

        payment_method_message = ""

        payment_methods = PaymentMethod.objects.filter(user=advertisement.owner)

        for payment_method in payment_methods:
            payment_method_message += f"{payment_method.name} | "

        comma_seperated_amount = "{:,}".format(convert_to_int(advertisement.amount))

        message += f"Advertisement ID: {advertisement.uuid_hex}; Amount: {comma_seperated_amount} TNBC; Price: {convert_to_decimal(advertisement.price)};\nPayment Method(s): {payment_method_message}\n\n"

    return message


def post_trade_to_api(amount, price):

    price_for_api = price / 10000

    data = {
        'amount': amount,
        'rate': price_for_api,
        'api_key': settings.MVP_SITE_API_KEY
    }

    headers = {
        'Content-Type': 'application/json'
    }

    r = requests.post('https://tnbcrow.pythonanywhere.com/recent-trades', json=data, headers=headers)

    if r.status_code == 201:
        return True, r.json()
    return False, r.json()


def get_total_balance_of_all_user():

    wallets = ThenewbostonWallet.objects.filter(balance__gt=settings.TNBC_MULTIPLICATION_FACTOR)

    total_balace = 0

    for wallet in wallets:
        total_balace += wallet.balance

    return total_balace


def get_advertisement_stats():

    total_tnbc = 0

    advertisements = Advertisement.objects.filter(status=Advertisement.OPEN)

    total_advertisements = advertisements.count()

    for adv in advertisements:

        total_tnbc += adv.amount

    return total_advertisements, total_tnbc
