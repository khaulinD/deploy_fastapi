# from sqlalchemy import String, DateTime, func, Integer, ForeignKey
# from sqlalchemy.orm import mapped_column, relationship
#
# from db.postgres import Base
# from decorators.as_dict import AsDictMixin
# from typing import TYPE_CHECKING
#
# if TYPE_CHECKING:
#     from db.models.user_tariff import UserTariffPlanStore, UserTariffPlan
#
# class AddtionalUser(Base, AsDictMixin):
#     payment_intent_id = mapped_column(String, nullable=True)
#     #good_id = ewrfgefhgjh
#     created_at = mapped_column(DateTime, default=func.now())
#     updated_at = mapped_column(DateTime, default=func.now(), onupdate=func.now())
#
#     user_tariff_id = mapped_column(Integer, ForeignKey('usertariffplans.id'))
#     user_tariff = relationship("UserTariffPlan", back_populates="company")