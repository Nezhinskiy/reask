"""Refund confirmation email. TD-7: built by joining strings, like every email here.

Customer-facing wording is owned by marketing.
"""

from notifications.format import rub


def refund_email(order, refund):
    return (
        "Здравствуйте, " + order.customer_name + "!\n\n"
        + "Мы оформили возврат по заказу № " + str(order.number) + ".\n"
        + "Сумма возврата: " + rub(order.total) + ".\n"  # ORD-219
        + "Деньги придут на карту в течение 10 рабочих дней.\n"
    )
