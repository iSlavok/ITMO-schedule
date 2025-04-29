from aiogram.filters.callback_data import CallbackData


class UsersListPageCD(CallbackData, prefix="users_list_page"):
    page: int
