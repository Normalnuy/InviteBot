from aiogram.fsm.state import StatesGroup, State


class CheckPassword(StatesGroup):
    password = State()
    

class AccountCode(StatesGroup):
    account_code = State()
    

class GetFile(StatesGroup):
    file = State()
