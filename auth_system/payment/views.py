import os
import json

import aioredis
import stripe
from fastapi import APIRouter, responses, HTTPException, Request, Header, BackgroundTasks
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from pathlib import Path

from company.schemas import CompanyUpdatePartial
from db.models.company import CompanyStore
from db.models.doctors.company_doctor import CompanyDoctorStore
from db.models.tariff_plan_info import TariffPlanStore
from datetime import datetime, timedelta

from db.models.user_tariff import UserTariffPlanStore
from payment.utils import get_customer_payments, get_payment_method_details, calculate_discount
from core.config import settings

router = APIRouter(tags=["Payment"], prefix="/payment")
rb = aioredis.Redis(host=settings.redis.host, port=settings.redis.port, db=0)


@router.get("/checkout")
async def create_checkout_session(tariff_id: int, request: Request):
    try:
        # Fetch tariff from DB
        tariff = await TariffPlanStore.get_plan_by_id(plan_id=tariff_id)
        payload = request.state.payload
        # Fetch user from DB based on user_type and user_id
        if payload["user_type"] == "company":
            user = await CompanyStore.get_company_clean_by_id(company_id=payload["sub"])
            username = user.name
        else:
            raise HTTPException(status_code=400, detail="Invalid user type")

        # Check if customer exists in Stripe, create if not
        # stripe_customer = None

        if not user.stripe_customer_id:
            stripe_customer = stripe.Customer.create(
                email=user.email,
                name=username,
                metadata={"user_id": user.id, "user_type": payload["user_type"]},
            )
            # Update user record with the Stripe customer ID
            user = await CompanyStore.update_company(company_id=user.id,
                                              data=CompanyUpdatePartial(stripe_customer_id=stripe_customer.id))
            # elif payload["user_type"] == "user":
            #     user = await DoctorStore.update_doctor(doctor_id=user.id,
            #                                     data=CompanyUpdatePartial(stripe_customer_id=stripe_customer.id))

        checkout_session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,  # Use existing or newly created Stripe customer ID
            line_items=[
                {
                    "price": tariff.stripe_price_id,  # Use the Stripe Price ID associated with the tariff plan
                    "quantity": 1,
                }
            ],
            metadata={
                "tariff_id": tariff.id,
                "user_id": user.id,
                "user_type": payload["user_type"],
            },
            payment_method_types=["card",
                                  "paypal",
                                  "amazon_pay"],
            mode="subscription",
            discounts=[{
                "coupon": user.stripe_coupon_id if hasattr(user, 'stripe_coupon_id') else None
            }],
            success_url=settings.frontend_url + "/company/home",
            cancel_url=settings.frontend_url + "/company/home",
            expires_at=datetime.now() + timedelta(hours=4),
        )
        # Redirect to the Checkout session URL
        # return responses.RedirectResponse(checkout_session.url, status_code=303)
        return checkout_session.url
    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"error": str(e)})
        # return HTTPException(status_code=500, detail="Try latter")


@router.post("/webhook")
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks):
    payload = await request.body()

    try:
        event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)

    except ValueError as e:
        print("Invalid payload")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        print("Invalid signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    try:
        print("-----------", event["type"], "---------------")
        # # -------------coupon----------
        if event['type'] == "coupon.created":
            customer = int(event["data"]["object"]["metadata"]["customer"])
            await CompanyStore.update_company(company_id=customer,
                                              data=CompanyUpdatePartial(stripe_coupon_id=event["data"]["object"]["id"]))
        # ---------subscription--------
        if event["type"] == "payment_intent.succeeded":
            payment_intent_id = event["data"]["object"]["id"]
            customer = event["data"]["object"]["customer"]
            # tariff = await UserTariffPlanStore.get_by_customer(customer=customer)
            # if not tariff:
            plan = await UserTariffPlanStore.get_by_customer(customer=customer)
            await UserTariffPlanStore.setup_payment(plan_id=plan.id,
                                                    data={"payment_intent_id": payment_intent_id})

        if event["type"] == "customer.subscription.created":
            # print(event, "\n\n\n\n\n")
            subscription_id = event["data"]["object"]["id"]
            customer = event["data"]["object"]["customer"]
            await UserTariffPlanStore.create_previous(data={"customer": customer,
                                                            "subscription_id": subscription_id})

        if event["type"] == "invoice.paid":
            expired_at = event["data"]["object"]["lines"]["data"][0]["period"]["end"]
            customer = event["data"]["object"]["customer"]
            plan = await UserTariffPlanStore.get_by_customer(customer=customer)
            await UserTariffPlanStore.setup_payment(plan_id=plan.id,
                                                    data={"expired_at": expired_at})
            customer = await CompanyStore.get_company_by_stripe_id(stripe_id=customer)
            await rb.delete(f"payment_list_{customer.id}")


        if event["type"] == "checkout.session.completed":
            payment = event["data"]["object"]
            customer = event["data"]["object"]["customer"]
            user_id = payment["metadata"]["user_id"]
            user_type = payment["metadata"]["user_type"]
            tariff_id = payment["metadata"]["tariff_id"]
            if user_type:
                plan = await UserTariffPlanStore.get_by_customer(customer=customer)
                await UserTariffPlanStore.setup_payment(plan_id=plan.id,
                                                        data={"tariff_id": int(tariff_id),
                                                              "user_id": int(user_id),
                                                              "user_type": user_type})

                await CompanyStore.update_company(company_id=int(user_id),
                                                  data=CompanyUpdatePartial(
                                                      stripe_coupon_id=None))

            # send email in background task
            # background_tasks.add_task()
            print("send email")

    except Exception as e:
        print(e)
        pass


@router.get("/refund")
async def refund_checkout_session(request: Request):
    try:
        payload = request.state.payload
        user = await CompanyStore.get_company_by_id(company_id=payload["sub"])
        if not user.has_refunded:
            if user.tariff_plan and user.tariff_plan.created_at + timedelta(days=7) > datetime.now():
                refund = stripe.Refund.create(
                    payment_intent=user.tariff_plan.payment_intent_id,
                )
                if refund:
                    stripe.Subscription.cancel(user.tariff_plan.subscription_id)
                    await CompanyStore.update_company(company_id=user.id, data=CompanyUpdatePartial(has_refunded=True))
                    await UserTariffPlanStore.delete_customer_plan(customer_id=user.id, plan_id=user.user_tariff_id)
                    await CompanyDoctorStore.delete_all_doctors(company_id=user.id)
                return JSONResponse(status_code=200, content={"detail": "Refund successful"})
        return JSONResponse(status_code=403, content={"detail": "You already refunded"})
    except Exception as e:
        print(str(e))
        return JSONResponse(status_code=403, content={"detail": "Error while refund checkout session"})


@router.get("/cancel-subscription")
async def cancel_subscription(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = request.state.payload
        user = await CompanyStore.get_company_by_id(company_id=payload["sub"])
        if user.tariff_plan and user.tariff_plan.subscription_id:
            subscription = stripe.Subscription.cancel(
                user.tariff_plan.subscription_id
            )
        else:
            return JSONResponse(status_code=403, content={"detail": "Subscription not found"})
        return JSONResponse(status_code=200, content={"detail": "Subscription cancelled"})
    except Exception as e:
        return JSONResponse(status_code=403, content={"detail": "Error while cancel subscription"})


@router.get("/list")
async def payment_list(request: Request):
    payload = request.state.payload
    cache = await rb.get(f"payment_list_{payload['sub']}")
    if cache:
        return json.loads(cache)
    user = await CompanyStore.get_company_clean_by_id(company_id=payload["sub"])
    customer_payments = await get_customer_payments(user.stripe_customer_id)
    list_payments = []
    for payment in customer_payments:
        payment_method_details = await get_payment_method_details(payment)
        data = {"status": payment["status"],
                "date": datetime.fromtimestamp(payment["created"]),
                "amount": payment["amount"] / 100,
                "last4": payment_method_details['card']["last4"],
                "transaction": payment_method_details["card"]['brand'],
                }
        list_payments.append(data)
    else:
        print("Failed to retrieve payments for the customer.")
    list_payments_json = json.dumps(list_payments, default=str)
    await rb.set(f"payment_list_{payload['sub']}", list_payments_json)
    await rb.expire(f"payment_list_{payload['sub']}", 600)
    return list_payments


@router.get("/upgrate_subscription")
async def upgrate_subscription(plan_id: int, request: Request, background_tasks: BackgroundTasks):
    payload = request.state.payload
    discount = await calculate_discount(plan_id=plan_id, user_id=payload["sub"])
    if discount > 0:
        coupon = stripe.Coupon.create(
            amount_off=int(discount) * 100,
            currency="usd",
            duration='once',  # or 'repeating' for a recurring coupon
            max_redemptions=1,
            metadata={"customer": payload["sub"]}
        )
    return discount
