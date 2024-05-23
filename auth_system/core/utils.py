# from functools import wraps
#
#
# def rate_limit(limit: int, period: int):
#     def decorator(func):
#         @wraps(func)
#         async def wrapper(*args, **kwargs):
#             path = kwargs.get('request').url.path
#             if requests_count[path] >= limit:
#                 raise HTTPException(status_code=429, detail="Too Many Requests")
#
#             result = await func(*args, **kwargs)
#             requests_count[path] += 1
#
#             async def reset_counter():
#                 await asyncio.sleep(period)
#                 requests_count[path] = 0
#
#             asyncio.create_task(reset_counter())
#             return result
#
#         return wrapper
#
#     return decorator