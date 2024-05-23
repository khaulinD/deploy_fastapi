from datetime import datetime

import stripe

from db.models.company import CompanyStore
from db.models.tariff_plan_info import TariffPlanStore


# Function to cancel a subscription
async def cancel_subscription(subscription_id):
    stripe.Subscription.delete(subscription_id)


# Function to handle refunds
async def handle_refund(payment_intent_id):

    payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
    subscription_id = payment_intent.subscription

    await cancel_subscription(subscription_id)

    # Notify the user about the refund and subscription cancellation
    # send_notification_email(user_email, "Your payment has been refunded and your subscription has been cancelled.")


async def get_customer_payments(customer_id):
    try:
        payments = stripe.PaymentIntent.list(customer=customer_id)
        return payments.data
    except stripe.error.StripeError as e:
        # Handle errors
        print(f"Error retrieving payments: {e}")
        return []


# def get_payment_method_details(payment_intent):
#     try:
#         # print(payment_intent)
#         payment_method = stripe.PaymentMethod.retrieve(payment_intent.payment_method)
#         if payment_method.type == 'card':
#             return payment_method.card.brand
#         else:
#             return payment_method.type
#     except stripe.error.StripeError as e:
#         # Handle errors
#         print(f"Error retrieving payment method details: {e}")
#         return None

async def get_payment_method_details(payment_intent):
    try:
        payment_method = stripe.PaymentMethod.retrieve(payment_intent.payment_method)
        return payment_method
    except stripe.error.StripeError as e:
        # Handle errors
        print(f"Error retrieving payment method details: {e}")
        return []


async def calculate_discount(plan_id: int, user_id: int):
    user = await CompanyStore.get_company_with_tariff_plan(company_id=user_id)
    old_tariff = await TariffPlanStore.get_plan_by_id(plan_id=user.user_tariff_id)
    new_tariff = await TariffPlanStore.get_plan_by_id(plan_id=plan_id)
    if old_tariff.price < new_tariff.price:
        used_time = (datetime.now() - user.user_tariff.updated_at).days + 1

        # amount of money used in this plan duration
        used_money = old_tariff.price - ((old_tariff.price * used_time) / (old_tariff.duration * 30.5))

        return used_money
    else:
        return 0




