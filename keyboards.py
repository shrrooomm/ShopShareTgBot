from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, 
                           InlineKeyboardMarkup, InlineKeyboardButton)

#Главное меню (Reply keyboard)
menu = ReplyKeyboardMarkup(
    keyboard = [
        [KeyboardButton(text = 'Посмотреть мои списки', style = 'primary')],
        [KeyboardButton(text = 'Создать список', style = 'success')],
        [KeyboardButton(text = 'Помощь')]
    ],

    resize_keyboard = True,
    input_field_placeholder = 'Выберите пункт меню!'
)

#Клавиатура управления списком (Inline keyboard)
def get_list_menu(list_id):
    return InlineKeyboardMarkup(
    inline_keyboard = [
        [InlineKeyboardButton(text = 'Посмотреть список', callback_data = f'list_show_{list_id}')],
        [InlineKeyboardButton(text = 'Редактировать', callback_data = f'list_edit_{list_id}', style = 'primary'),
        InlineKeyboardButton(text = 'Участники', callback_data = f'list_membersEdit_{list_id}', style = 'primary')],
        [InlineKeyboardButton(text = 'Удалить список', callback_data = f'list_delete_{list_id}', style = 'danger')]
    ]
)

#Клавиатура "Помощь" (Inline keyboard)
help_keyboard = InlineKeyboardMarkup(
    inline_keyboard = [
        [InlineKeyboardButton(text = 'Руководство пользователя', url = 'https://disk.360.yandex.ru/d/RlLs4XGB9y9uLA', style = 'primary')],
        [InlineKeyboardButton(text = 'Разработчик 1', url = 'https://t.me/shrooomm')],
        [InlineKeyboardButton(text = 'Разработчик 2', url = 'https://t.me/anastzzwx')],
    ],
)

#Клавиатура выбора типа списка (Inline keyboard)
def get_list_category_menu():
    return InlineKeyboardMarkup(
         inline_keyboard = [
              [InlineKeyboardButton(text = 'Созданные мной', callback_data = 'show_my', style = 'primary')],
              [InlineKeyboardButton(text = 'По приглашению', callback_data = 'show_invited', style = 'primary')]
              ]
)

#Клавиатура выбора списка (Inline keyboard)
def get_lists_by_category_menu(lists, category):
    inline_keyboard = []
    for l in lists:
          inline_keyboard.append([
               InlineKeyboardButton(text = f"{l['title']}", callback_data = f"list_menu_view_{l['list_id']}")
          ])
    inline_keyboard.append([
         InlineKeyboardButton(text = 'Назад', callback_data = 'lists_back_categories', style = 'primary')
    ])
    return InlineKeyboardMarkup(inline_keyboard = inline_keyboard
)

#Кнопка назад в меню управления списком (Inline keyboard)
def get_back_to_list_menu(list_id):
     return InlineKeyboardMarkup(
          inline_keyboard = [
               [InlineKeyboardButton(text = 'Назад', callback_data = f'edit_back_{list_id}', style = 'primary')]
          ]
     )

#Клавиатура редактирования списка (Inline keyboard)
def get_edit_menu(list_id):
    return InlineKeyboardMarkup(
    inline_keyboard = [
        [InlineKeyboardButton(text = 'Посмотреть список', callback_data = f'list_show_{list_id}')],
        [InlineKeyboardButton(text = 'Добавить товар', callback_data = f'edit_add_{list_id}', style = 'success'),
        InlineKeyboardButton(text = 'Удалить товар', callback_data = f'edit_del_{list_id}', style = 'danger')],
        [InlineKeyboardButton(text = 'Пометить/убрать пометку "Срочно"', callback_data = f'edit_urgent_{list_id}', style = 'primary')],
        [InlineKeyboardButton(text = 'Пометить/убрать отметку "Куплено"', callback_data = f'edit_buy_{list_id}', style = 'primary')],
        [InlineKeyboardButton(text = 'Назад', callback_data = f'edit_back_{list_id}')]
    ]
)

#Клавиатура выбора срочности товара (Inline keyboard)
def get_urgency_menu(list_id):
    return InlineKeyboardMarkup(
        inline_keyboard = [
            [InlineKeyboardButton(text = 'Да', callback_data = f'prod_urgent_1_{list_id}', style = 'success'),
            InlineKeyboardButton(text = 'Нет', callback_data = f'prod_urgent_0_{list_id}', style = 'danger')],
            [InlineKeyboardButton(text = 'Отменить добавление', callback_data = f'cancel_add_{list_id}', style = 'danger')]
        ]
    )

#Кнопка отмены добавления товара (Inline keyboard)
def get_cancel_button(list_id):
     return InlineKeyboardMarkup(
          inline_keyboard = [
               [InlineKeyboardButton(text = 'Отменить добавление', callback_data = f'cancel_add_{list_id}', style = 'danger')]
          ]
)

#Клавиатура меню удаления товаров (Inline keyboard)
def get_delete_products_menu(products, list_id):
    inline_keyboard = []
    for index, p in enumerate(products, 1):
        status = "✅" if p['is_bought'] == 1 else "❌"
        urgent = "❗️" if p['is_urgent'] == 1 else ""
        quantity = f" ({p['quantity']})" if p['quantity'] else ""
        
        button_text = f"{index}. {urgent}{p['title']} {quantity} {status}"
        
        inline_keyboard.append([
             InlineKeyboardButton(text = button_text, callback_data = f"prod_confirm_del_{p['product_id']}_{list_id}")
             ])
        
    inline_keyboard.append([
                 InlineKeyboardButton(text = 'Назад', callback_data = f"list_edit_{list_id}", style = 'primary')
                 ])
    return InlineKeyboardMarkup(inline_keyboard = inline_keyboard
)

#Клавиатура меню изменения статуса срочности товаров (Inline keyboard)
def get_urgent_products_menu(products, list_id):
    inline_keyboard = []
    for index, p in enumerate(products, 1):
            status = "✅" if p['is_bought'] == 1 else "❌"
            urgent = "❗️" if p['is_urgent'] == 1 else ""
            quantity = f" ({p['quantity']})" if p['quantity'] else ""

            button_text = f"{index}. {urgent}{p['title']} {quantity} {status}"

            inline_keyboard.append([
                 InlineKeyboardButton(text = button_text, callback_data = f"prod_edit_urg_{p['product_id']}_{list_id}")
        ])
    
    inline_keyboard.append([
                 InlineKeyboardButton(text = 'Назад', callback_data = f"list_edit_{list_id}", style = 'primary')])
    return InlineKeyboardMarkup(inline_keyboard = inline_keyboard
)

#Клавиатура меню изменения статуса покупки товаров (Inline keyboard)
def get_buy_products_menu(products, list_id):
    inline_keyboard = []
    for index, p in enumerate(products, 1):
         status = "✅" if p['is_bought'] == 1 else "❌"
         urgent = "❗️" if p['is_urgent'] == 1 else ""
         quantity = f" ({p['quantity']})" if p['quantity'] else ""

         button_text = f"{index}. {urgent}{p['title']} {quantity} {status}"

         inline_keyboard.append([
              InlineKeyboardButton(text = button_text, callback_data = f"prod_edit_buy_{p['product_id']}_{list_id}")
         ])

    inline_keyboard.append([
         InlineKeyboardButton(text = 'Назад', callback_data = f"list_edit_{list_id}", style = 'primary')])
    return InlineKeyboardMarkup(inline_keyboard = inline_keyboard
)

#Клавиатура меню участников (Inline keyboard)
def get_members_menu(list_id):
     return InlineKeyboardMarkup(
          inline_keyboard = [
               [InlineKeyboardButton(text = 'Список участников', callback_data = f'member_list_{list_id}')],
               [InlineKeyboardButton(text = 'Добавить участников', callback_data = f'member_add_{list_id}', style = 'success')],
               [InlineKeyboardButton(text = 'Удалить участников', callback_data = f'member_del_{list_id}', style = 'danger')],
               [InlineKeyboardButton(text = 'Назад', callback_data = f'edit_back_{list_id}', style = 'primary')]
          ]
)

#Клавиатура меню удаления участников (Inline keyboard)
def get_delete_members_menu(members, list_id):
    inline_keyboard = []
    for m in members:
          inline_keyboard.append([
               InlineKeyboardButton(text = f"{m['name']}", callback_data = f"member_confirm_del_{m['tg_id']}_{list_id}")
          ])
    inline_keyboard.append([
         InlineKeyboardButton(text = 'Назад', callback_data = f'list_membersEdit_{list_id}', style = 'primary')
    ])
    return InlineKeyboardMarkup(inline_keyboard = inline_keyboard)

#Кнопка назад в списке участников (Inline keyboard)
def get_back_to_members_menu(list_id):
     return InlineKeyboardMarkup(
          inline_keyboard = [
               [InlineKeyboardButton(text = 'Назад', callback_data = f'list_membersEdit_{list_id}', style='primary')]
          ]
     )

#Подтверждение удаления списка (Inline keyboard)
def get_delete_confirm_menu(list_id):
     return InlineKeyboardMarkup(
          inline_keyboard = [
               [InlineKeyboardButton(text = 'Удалить', callback_data = f'list_del_confirm_{list_id}', style = 'danger'),
                InlineKeyboardButton(text = 'Отмена', callback_data = f'edit_back_{list_id}', style = 'primary')]
          ]
)
