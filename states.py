from aiogram.fsm.state import StatesGroup, State

#Состояние регистрации - ожидание ввода имени
class Registration(StatesGroup):
    waiting_name = State()

#Состояние создания списка - ожидание ввода названия списка и товара
class CreateList(StatesGroup):
    waiting_list_name = State()
    waiting_products_count = State()
    waiting_product_name = State()
    waiting_product_quantity = State()