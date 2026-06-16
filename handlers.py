from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters.command import CommandStart, Command
from aiogram.fsm.context import FSMContext

import asyncio
import database as db
import keyboards as kb
from states import Registration, CreateList

user = Router()

#Команда /start
@user.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    args = message.text.split()
    invite_list_id = None

    if len(args) > 1 and args[1].startswith('invite_list_'):
        try:
            invite_list_id = int(args[1].split('_')[2])
        except (ValueError, IndexError):
            pass
    
    user_name = await db.is_user_registered(message.from_user.id)
    
    if user_name:
        if invite_list_id:
            list_title = await db.get_list_title(invite_list_id)
            if not list_title:
                await message.answer("Этот список больше не существует!")
                return
            
            if await db.is_user_in_list(message.from_user.id, invite_list_id):
                await message.answer(f"Вы уже состоите в списке <b>«{list_title}»</b>!", 
                                    reply_markup = kb.menu, parse_mode = "HTML")
                return
            
            user_lists = await db.get_user_lists(message.from_user.id)
            guest_lists_count = 0
            for lst in user_lists:
                if lst['creator_id'] != message.from_user.id:
                    guest_lists_count += 1

            if guest_lists_count >= 20:
                await message.answer(f"Не удалось присоединиться к списку <b>«{list_title}»</b>!\n\n"
                    f"Вы уже вступили в максимальное количество чужих списков (допустимо не более <b>20</b>).", 
                    reply_markup = kb.menu, parse_mode = 'HTML')
                return

            current_members = await db.list_members(invite_list_id)
            if len(current_members) >= 20:
                await message.answer(f"Не удалось присоединиться к списку <b>«{list_title}»</b>!\n\n"
                    f"Достигнут лимит группы: в списке не может быть более <b>20 участников</b>!", 
                    reply_markup = kb.menu, parse_mode = 'HTML')
                return
            else:
                await db.add_user_to_list(message.from_user.id, invite_list_id)
                await message.answer(f"Вы вступили в список <b>«{list_title}»</b>!", 
                                    reply_markup = kb.menu, parse_mode = "HTML")
                await notify_list_members(message, invite_list_id, f'Пользователь <b>{user_name}</b> присоединился к списку!')
        else:
            await message.answer(f'Это снова вы, {user_name}!', reply_markup = kb.menu)

    else:
        if invite_list_id:
            await state.update_data(invite_list_id = invite_list_id)
        
        await message.answer('Добро пожаловать!\n\n' \
        'Вас приветствует <b>ShopShare</b> - сервис для совместного ведения списка покупок!\n\n' \
        '<b>Что умеет этот бот:</b>\n' \
        '- Создавать списки покупок\n' \
        '- Делиться своими списками\n' \
        '- Редактировать списки вместе\n\n' \
        'Для начала, введите ваше имя: ',
                         reply_markup = ReplyKeyboardRemove(), parse_mode = 'HTML')
        await state.set_state(Registration.waiting_name)

#Регистрация пользователя
@user.message(Registration.waiting_name)
async def reg_name(message: Message, state: FSMContext):
    if len(message.text) > 50:
        await message.answer(f'Имя слишком длинное! ({len(message.text)} симв.)\n\n'
                             f'Максимальная длина - <b>50 символов</b>! Введите еще раз:', parse_mode = 'HTML')
        return
    
    await state.update_data(name = message.text)
    data = await state.get_data()

    await db.add_user(tg_id = message.from_user.id, name = data['name'])

    invite_list_id = data.get('invite_list_id')
    if invite_list_id:
        list_title = await db.get_list_title(invite_list_id)
        if list_title:
            current_members = await db.list_members(invite_list_id)
            if len(current_members) >= 20:
                await message.answer(f'Вы успешно зарегистрировались!\n\nВаше имя: {data['name']}\n\n'
                                     f'К сожалению, список <b>«{list_title}»</b> уже заполнен '
                                     f'(максимум 20 участников), вы не были в него добавлены!',
                                     reply_markup = kb.menu, parse_mode = 'HTML')
            else:
                await db.add_user_to_list(message.from_user.id, invite_list_id)
                await message.answer(f'Вы успешно зарегистрировались!\n\nВаше имя: {data['name']}\n\n'
                                     f'Вы добавлены в список <b>«{list_title}»</b>!',
                                     reply_markup = kb.menu, parse_mode = 'HTML')
                await notify_list_members(message, invite_list_id, f'Пользователь <b>{data['name']}</b> присоединился к списку!')
        else:
            await message.answer(f'Вы успешно зарегистрировались!\n\nВаше имя: {data['name']}\n\n'
                                 f'Cписок <b>«{list_title}»</b>, в который вас пригласили, больше не существует!',
                                 reply_markup = kb.menu, parse_mode = 'HTML')
    else:
        await message.answer(f'Вы успешно зарегистрировались!\n\n'
                             f'Ваше имя: {data['name']}\n\n' \
                             'Используйте нижнее меню, чтобы начать работу со списками:',
                         reply_markup = kb.menu)
    
    await state.clear()


#Функционал кнопки "Посмотреть мои списки" (Reply keyboard)
@user.message(F.text == 'Посмотреть мои списки')
async def cmd_view_my_lists(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Какие списки вы хотите посмотреть?',
                         reply_markup = kb.get_list_category_menu())
    
#Функционал кнопки "Создать список" (Reply keyboard)
@user.message(F.text == 'Создать список')
async def cmd_create_list(message: Message, state: FSMContext):
    await state.clear()

    user_lists = await db.get_user_lists(message.from_user.id)
    own_lists_count = 0
    for lst in user_lists:
        if lst['creator_id'] == message.from_user.id:
            own_lists_count += 1
    
    if own_lists_count >= 20:
        await message.answer('<b>Превышен лимит создания списков!</b>\n\n'
            'Вы не можете создать более <b>20 списков</b> одновременно!\n'
            'Удалите один из существующих списков, чтобы создать новый', 
            parse_mode='HTML'
        )
        return
    
    await message.answer('Введите название списка:')
    await state.set_state(CreateList.waiting_list_name)

@user.message(CreateList.waiting_list_name)
async def create_list_name(message: Message, state: FSMContext):
    if len(message.text) > 50:
        await message.answer(f'Название слишком длинное! ({len(message.text)} симв.)\n\n'
                             f'Максимальная длина - <b>50 символов</b>! Введите еще раз:', parse_mode = 'HTML')
        return
    
    await state.update_data(list_name = message.text)
    data = await state.get_data()

    list_id = await db.create_list(title = data['list_name'], creator_id = message.from_user.id)

    await message.answer(f'Список <b>«{data["list_name"]}»</b> создан!',
                         reply_markup = kb.get_list_menu(list_id), parse_mode = 'HTML')
    await state.clear()

#Функционал кнопки "Помощь"
@user.message(F.text == 'Помощь')
async def cmd_help(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Для получения руководства пользователя нажмите кнопку <b>«Руководство пользователя»</b> снизу' \
    '\n\nТакже Вы можете связаться с разработчиками:', reply_markup = kb.help_keyboard, parse_mode = 'HTML')





#Функционал кнопки "Созданные мной" после выбора просмотра списков (Inline keyboard)
@user.callback_query(F.data == 'show_my')
async def show_my_lists(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    lists = await db.get_user_lists(user_id, is_creator = True)

    if not lists:
        msg = await callback.message.answer('Вы еще не создали ни одного списка!')
        await asyncio.sleep(5)
        try:
            await msg.delete()
        except Exception:
            pass
        return
    
    await callback.message.edit_text(text = 'Списки, созданные вами:',
                                     reply_markup = kb.get_lists_by_category_menu(lists, 'my'))
    
#Функционал кнопки "По приглашению" после выбора просмотра списков (Inline keyboard)
@user.callback_query(F.data == 'show_invited')
async def show_invited_lists(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    lists = await db.get_user_lists(user_id, is_creator = False)

    if not lists:
        msg = await callback.message.answer(text = 'Вас еще не пригласили ни в один список!')
        await asyncio.sleep(5)
        try:
            await msg.delete()
        except Exception:
            pass
        return
    
    await callback.message.edit_text(text = 'Списки, в которые вас пригласили:',
                                     reply_markup = kb.get_lists_by_category_menu(lists, 'invited'))

#Функционал кнопки "Назад" в меню после выбора "Созданные мной" или "По приглашению" (Inline keyboard)
@user.callback_query(F.data == 'lists_back_categories')
async def back_to_categories(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(text = 'Какие списки вы хотите посмотреть?',
                                     reply_markup = kb.get_list_category_menu())
    
#Функционал кнопки "Название списка" в меню после выбора "Созданные мной" или "По приглашению" (Inline keyboard)
@user.callback_query(F.data.startswith('list_menu_view_'))
async def list_menu_view(callback: CallbackQuery):
    await callback.answer()
    list_id = int(callback.data.split('_')[3])
    list_name = await db.get_list_title(list_id)

    await callback.message.edit_text(text = f'Управление списком <b>«{list_name}»</b>',
                                     reply_markup = kb.get_list_menu(list_id), parse_mode = "HTML")





#Функционал кнопки "Посмотреть список" в меню управления списком и в меню редактирования (Inline keyboard)
@user.callback_query(F.data.startswith('list_show_'))
async def show_products_list(callback: CallbackQuery):
    await callback.answer()
    list_id = int(callback.data.split('_')[2])
    list_title = await db.get_list_title(list_id)
    products = await db.get_products(list_id)

    if not products:
        await callback.message.edit_text(
            text = f'Список <b>«{list_title}»</b> пуст\n\nДобавьте товары через меню "Редактировать"',
            reply_markup = kb.get_back_to_list_menu(list_id), parse_mode = 'HTML')
        return
    
    text = f"Список <b>«{list_title}»</b>:\n\n(❗️ - срочность, ✅/❌ - куплен/не куплен)\n\n"
    
    for index, p in enumerate(products, 1):
        status = '✅' if p['is_bought'] == 1 else '❌'
        urgent = '❗️' if p['is_urgent'] == 1 else ''
        quantity = f' ({p['quantity']})' if p['quantity'] else ''
        
        text += f"{index}. {urgent}<b>{p['title']}</b>{quantity}  {status}\n\n"

    await callback.message.edit_text(text = text, reply_markup = kb.get_back_to_list_menu(list_id),parse_mode = 'HTML')

#Функционал кнопки "Редактировать" в меню управления списком (Inline keyboard)
@user.callback_query(F.data.startswith('list_edit_'))
async def list_action(callback: CallbackQuery, state: FSMContext):
    list_id = int(callback.data.split('_')[2])
    list_name = await db.get_list_title(list_id)
    await callback.answer()

    await callback.message.edit_text(text = f"<b>Редактирование списка «{list_name}»</b>\n\nВыберите опцию:",
                                         reply_markup = kb.get_edit_menu(list_id), parse_mode = "HTML")

#Функционал кнопки "Участники" в меню управления списком (Inline keyboard)
@user.callback_query(F.data.startswith('list_membersEdit_'))
async def members_menu_view(callback: CallbackQuery):
    await callback.answer()
    list_id = int(callback.data.split('_')[2])
    list_name = await db.get_list_title(list_id)

    await callback.message.edit_text(text = f'Управление участниками списка <b>«{list_name}»</b>\n',
                                     reply_markup = kb.get_members_menu(list_id), parse_mode = 'HTML')
    
#Функционал кнопки "Удалить список" в меню управления списком (Inline keyboard). Запрашивает подтверждение удаления
@user.callback_query(F.data.startswith('list_delete_'))
async def ask_delete_list(callback: CallbackQuery):
    list_id = int(callback.data.split('_')[2])
    list_name = await db.get_list_title(list_id)

    creator_id = await db.get_list_creator(list_id)
    if callback.from_user.id != creator_id:
        msg = await callback.message.answer("Удалить список может только его создатель!")
        await callback.answer()
        await asyncio.sleep(5)
        try:
            await msg.delete()
        except Exception:
            pass
        return
    
    await callback.message.edit_text(text = f'<b>ВНИМАНИЕ!</b>\n\nВы уверены, что хотите удалить список <b>«{list_name}»</b>?\n\n'
                                     f'Это действие удалит ВСЕХ участников и ВСЕ товары внутри списка без возможности восстановления!',
                                     reply_markup = kb.get_delete_confirm_menu(list_id), parse_mode = 'HTML')
    
    await callback.answer()

#Функция удаления списка
@user.callback_query(F.data.startswith('list_del_confirm_'))
async def delete_list_inline(callback: CallbackQuery):
    await callback.answer()
    list_id = int(callback.data.split('_')[3])
    list_name = await db.get_list_title(list_id)

    creator_id = await db.get_list_creator(list_id)
    if callback.from_user.id != creator_id:
        await callback.message.answer("У вас нет прав на удаление этого списка!")
        try:
            await callback.message.delete()
        except Exception:
            pass
        return

    await db.delete_list(list_id)
    await callback.message.answer(f'Список <b>«{list_name}»</b> удален!', parse_mode = "HTML")

    try:
        await callback.message.delete()
    except Exception:
        pass





#Функционал кнопки "Отмена добавления" во время добавления товара (Inline keyboard)
@user.callback_query(F.data.startswith('cancel_add_'))
async def cancel_product_add(callback: CallbackQuery, state: FSMContext):
    list_id = int(callback.data.split('_')[2])
    list_name = await db.get_list_title(list_id)
    await state.clear()
    await callback.answer('Ввод товара отменен!')

    await callback.message.edit_text(text = f"Добавление товаров отменено\n\n<b>Редактирование списка «{list_name}»</b>\n\nВыберите опцию:",
                                     reply_markup = kb.get_edit_menu(list_id), parse_mode = "HTML")

#Функционал кнопки "Добавить товар" (Inline keyboard)
@user.callback_query(F.data.startswith('edit_add_'))
async def add_product_start(callback: CallbackQuery, state: FSMContext):
    list_id = int(callback.data.split('_')[2])

    await state.update_data(current_list_id = list_id)
    await state.set_state(CreateList.waiting_products_count)
    await callback.answer()

    sent_msg = await callback.message.edit_text(text = "Сколько вы хотите добавить товаров?",
                                                reply_markup = kb.get_cancel_button(list_id))
    await state.update_data(last_msg_id = sent_msg.message_id)

#Функция запроса названия товара
@user.message(CreateList.waiting_products_count)
async def add_product_count(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer("Пожалуйста, введите корректное число больше нуля:")
        return

    count = int(message.text)
    await state.update_data(remaining_count = count)
    data = await state.get_data()
    list_id = data['current_list_id']
    last_msg_id = data.get('last_msg_id')

    if last_msg_id:
        try:
            await message.bot.edit_message_reply_markup(chat_id = message.chat.id, message_id = last_msg_id, reply_markup = None)
        except Exception:
            pass

    await state.set_state(CreateList.waiting_product_name)

    sent_msg = await message.answer("Введите название товара:",
                                    reply_markup = kb.get_cancel_button(list_id))
    await state.update_data(last_msg_id = sent_msg.message_id)

#Функция запроса названия товара
@user.message(CreateList.waiting_product_name)
async def add_product_name(message: Message, state: FSMContext):
    data = await state.get_data()
    list_id = data['current_list_id']

    if len(message.text) > 50:
        await message.answer(f'Название слишком длинное! ({len(message.text)} симв.)\n\n'
                             f'Максимальная длина - <b>50 символов</b>! Введите еще раз:', 
                             reply_markup = kb.get_cancel_button(list_id), parse_mode = 'HTML')
        return
    
    await state.update_data(product_name = message.text)
    last_msg_id = data.get('last_msg_id')

    if last_msg_id:
        try:
            await message.bot.edit_message_reply_markup(chat_id = message.chat.id, message_id = last_msg_id, reply_markup = None)
        except Exception:
            pass

    await state.set_state(CreateList.waiting_product_quantity)

    sent_msg = await message.answer('Введите количество (например: 1 шт, 200 гр):',
                                    reply_markup = kb.get_cancel_button(list_id))
    await state.update_data(last_msg_id = sent_msg.message_id)

#Функция запроса срочности товара
@user.message(CreateList.waiting_product_quantity)
async def add_product_quantity(message: Message, state: FSMContext):
    data = await state.get_data()
    list_id = data['current_list_id']

    if len(message.text) > 50:
        await message.answer(f'Название слишком длинное! ({len(message.text)} симв.)\n\n'
                             f'Максимальная длина - <b>50 символов</b>! Введите еще раз:', 
                             reply_markup = kb.get_cancel_button(list_id), parse_mode = 'HTML')
        return
    
    await state.update_data(product_quantity = message.text)
    last_msg_id = data.get('last_msg_id')

    if last_msg_id:
        try:
            await message.bot.edit_message_reply_markup(chat_id = message.chat.id, message_id = last_msg_id, reply_markup = None)
        except Exception:
            pass

    sent_msg = await message.answer('Пометить товар как срочный?', reply_markup = kb.get_urgency_menu(list_id))
    await state.update_data(last_msg_id = sent_msg.message_id)

#Функция добавления товаров в базу данных и отворный запрос товара (если требуется)
@user.callback_query(F.data.startswith('prod_urgent_'))
async def add_product_finish(callback: CallbackQuery, state: FSMContext):
    is_urgent = int(callback.data.split('_')[2])
    list_id = int(callback.data.split('_')[3])
    list_name = await db.get_list_title(list_id)

    user_data = await state.get_data()
    product_name = user_data.get('product_name')
    product_quantity = user_data.get('product_quantity')
    remaining_count = user_data.get('remaining_count') - 1
    last_msg_id = user_data.get('last_msg_id')

    await db.add_product(list_id = list_id, title = product_name, quantity = product_quantity, is_urgent = is_urgent)
    await callback.answer("Товар добавлен!")

    qty_text = f" ({product_quantity})" if product_quantity else ""
    urgent_text = "❗️ " if is_urgent else ""
    notification = (f"Пользователь <b>{{user_name}}</b> добавил товар {urgent_text}<b>«{product_name}»</b>"
                    f"{qty_text} в список <b>«{list_name}»</b>!")
    await notify_list_members(callback, list_id, notification)

    if last_msg_id:
        try:
            await callback.message.bot.edit_message_reply_markup(chat_id = callback.message.chat.id, message_id = last_msg_id, reply_markup = None)
        except Exception:
            pass

    if remaining_count > 0:
        await state.update_data(remaining_count = remaining_count)
        await state.set_state(CreateList.waiting_product_name)
        sent_msg = await callback.message.answer(f"Товар добавлен. Осталось добавить товаров: {remaining_count}\nВведите название следующего товара: ",
                                                 reply_markup = kb.get_cancel_button(list_id))
        await state.update_data(last_msg_id = sent_msg.message_id)
    else:
        await callback.message.answer(text = f'Все товары успешно добавлены!\n\n<b>Редактирование списка «{list_name}»</b>\n\nВыберите опцию:',
            reply_markup=kb.get_edit_menu(list_id), parse_mode = "HTML")
        await state.clear()



#Функционал кнопки "Удалить товар" (Inline keyboard)
@user.callback_query(F.data.startswith('edit_del_'))
async def del_product(callback: CallbackQuery):
    list_id = int(callback.data.split('_')[2])
    list_name = await db.get_list_title(list_id)
    await callback.answer()
    
    creator_id = await db.get_list_creator(list_id)
    if callback.from_user.id != creator_id:
        msg = await callback.message.answer("Удалить товары из списка может только его создатель!")
        await callback.answer()
        await asyncio.sleep(5)
        try:
            await msg.delete()
        except Exception:
            pass
        return

    products = await db.get_products(list_id)
    if not products:
        msg = await callback.message.answer('В этом списке нет товаров!')
        await asyncio.sleep(5)
        try:
            await msg.delete()
        except Exception:
            pass
        return
    
    await callback.message.edit_text(text = 'Нажмите на товар, который хотите удалить:',
                                     reply_markup = kb.get_delete_products_menu(products, list_id))

#Функционал меню удаления товаров (Inline keyboard)
@user.callback_query(F.data.startswith('prod_confirm_del_'))
async def process_delete_product(callback: CallbackQuery):
    product_id = int(callback.data.split('_')[3])
    list_id = int(callback.data.split('_')[4])
    list_name = await db.get_list_title(list_id)

    products = await db.get_products(list_id)
    product_title = "Неизвестный товар"
    for prod in products:
        if prod['product_id'] == product_id:
            product_title = prod['title']
            break

    await db.delete_product(product_id)
    await callback.answer('Товар удален!')
    products_updated = await db.get_products(list_id)

    notification = f"Пользователь <b>{{user_name}}</b> удалил товар <b>«{product_title}»</b> из списка <b>«{list_name}»</b>!"
    await notify_list_members(callback, list_id, notification)

    if not products_updated:
        await callback.message.edit_text(
            text = f"Все товары удалены!\n\n<b>Редактирование списка «{list_name}»</b>\nВыберите опцию:",
            reply_markup = kb.get_edit_menu(list_id), parse_mode = 'HTML')
        return
    
    await callback.message.edit_text(text = 'Товар удален, выберите следующий для удаления:',
                                     reply_markup=kb.get_delete_products_menu(products_updated, list_id))
    
#Функционал кнопки "Пометить/убрать пометку 'Срочно'" (Inline keyboard)
@user.callback_query(F.data.startswith('edit_urgent_'))
async def urgent_product_start(callback: CallbackQuery):
    list_id = int(callback.data.split('_')[2])
    await callback.answer()

    products = await db.get_products(list_id)
    if not products:
        msg = await callback.message.answer('В списке нет товаров!')
        await asyncio.sleep(5)
        try:
            await msg.delete()
        except Exception:
            pass
        return
    
    await callback.message.edit_text(text = 'Нажмите на товар, чтобы изменить его статус срочности (❗️):', 
                                     reply_markup=kb.get_urgent_products_menu(products, list_id))

#Функционал меню изменения статуса срочности (Inline keyboard)
@user.callback_query(F.data.startswith('prod_edit_urg_'))
async def urgent_product_execute(callback: CallbackQuery):
    product_id = int(callback.data.split('_')[3])
    list_id = int(callback.data.split('_')[4])
    list_name = await db.get_list_title(list_id)

    products = await db.get_products(list_id)
    product_title = "Неизвестный товар"
    current_urgent = 0

    for prod in products:
        if prod['product_id'] == product_id:
            product_title = prod['title']
            current_urgent = prod['is_urgent']
            break

    await db.switch_urgent(product_id)
    await callback.answer('Статус срочности изменен!')
    
    new_status_text = "<b>СРОЧНЫМ</b>(❗️)" if current_urgent == 0 else "<b>НЕ СРОЧНЫМ</b>"
    notification = (f"Пользователь <b>{{user_name}}</b> сделал товар <b>«{product_title}»</b> "
                    f"{new_status_text} в списке <b>«{list_name}»</b>!")
    await notify_list_members(callback, list_id, notification)

    products_updated = await db.get_products(list_id)
    await callback.message.edit_text(text = 'Статус изменен, выберите следующий для изменения:',
                                     reply_markup = kb.get_urgent_products_menu(products_updated, list_id))
    

#Функционал кнопки "Пометить/убрать пометку 'Куплено'" (Inline keyboard)
@user.callback_query(F.data.startswith('edit_buy_'))
async def bought_menu(callback: CallbackQuery):
    list_id = int(callback.data.split('_')[2])
    await callback.answer()

    products = await db.get_products(list_id)
    if not products:
        msg = await callback.message.answer('В этом списке нет товаров!')
        await asyncio.sleep(5)
        try:
            await msg.delete()
        except Exception:
            pass
        return
    
    await callback.message.edit_text(text = 'Нажмите на товар, чтобы изменить его статус (Куплено✅ / Не куплено❌):',
                                     reply_markup = kb.get_buy_products_menu(products, list_id))

#Функционал меню изменения статуса 'Куплено' (Inline keyboard)
@user.callback_query(F.data.startswith('prod_edit_buy_'))
async def bought_menu_execute(callback: CallbackQuery):
    product_id = int(callback.data.split('_')[3])
    list_id = int(callback.data.split('_')[4])
    list_name = await db.get_list_title(list_id)

    products = await db.get_products(list_id)
    product_title = "Неизвестный товар"
    current_bought = 0

    for prod in products:
        if prod['product_id'] == product_id:
            product_title = prod['title']
            current_bought = prod['is_bought']
            break

    await db.switch_bought(product_id)
    await callback.answer('Статус изменен!')

    new_status_text = "<b>КУПЛЕННЫМ(✅)</b>" if current_bought == 0 else "<b>НЕ КУПЛЕННЫМ(❌)</b>"
    notification = (f"Пользователь <b>{{user_name}}</b> отметил товар <b>«{product_title}»</b> "
                    f"{new_status_text} в списке <b>«{list_name}»</b>!")
    await notify_list_members(callback, list_id, notification)

    products_updated = await db.get_products(list_id)
    await callback.message.edit_text(text = 'Статус изменен, выберите следующий для изменения:',
                                     reply_markup = kb.get_buy_products_menu(products_updated, list_id))

#Функционал кнопки "Назад" (назад в меню управления списком) (Inline keyboard)
@user.callback_query(F.data.startswith('edit_back_'))
async def back_to_list_menu(callback: CallbackQuery):
    list_id = int(callback.data.split('_')[2])
    list_name = await db.get_list_title(list_id)

    await callback.message.edit_text(text = f'Управление списком <b>«{list_name}»</b>',
                                     reply_markup = kb.get_list_menu(list_id), parse_mode = "HTML")
    await callback.answer()






#Функционал кнопки "Список участников" в меню управления участниками (Inline keyboard)
@user.callback_query(F.data.startswith('member_list_'))
async def members_list_view(callback: CallbackQuery):
    await callback.answer()
    list_id = int(callback.data.split('_')[2])

    list_name = await db.get_list_title(list_id)
    members = await db.list_members(list_id)
    current_user_id = callback.from_user.id

    text = f"Участники списка <b>«{list_name}»</b>:\n\n"

    for index, m in enumerate(members, 1):
        labels = []
        
        if m['is_creator'] == 1:
            labels.append("владелец")
            
        if m['tg_id'] == current_user_id:
            labels.append("вы")

        label_text = f" ({', '.join(labels)})" if labels else ""
        text += f"{index}. {m['name']}{label_text}\n"
    await callback.message.edit_text(text = text, reply_markup = kb.get_back_to_members_menu(list_id), parse_mode = 'HTML')

#Функционал кнопки "Удалить участников" (Inline keyboard)
@user.callback_query(F.data.startswith('member_confirm_del_'))
async def delete_member(callback: CallbackQuery):
    target_user_id = int(callback.data.split('_')[3])
    list_id = int(callback.data.split('_')[4])
    list_name = await db.get_list_title(list_id)

    await db.remove_user_from_list(target_user_id, list_id)
    await callback.answer("Участник удален из списка!")

    try:
        await callback.bot.send_message(chat_id = target_user_id, 
                                        text = f"Вы были удалены из списка покупок <b>«{list_name}»</b>!",parse_mode="HTML")
    except Exception as e:
        print(f"Не удалось отправить уведомление пользователю {target_user_id}: {e}")
    
    all_members = await db.list_members(list_id)
    members_to_del = [m for m in all_members if m['tg_id'] != callback.from_user.id]

    if not members_to_del:
        await callback.message.edit_text(text = "Все остальные участники были удалены!",
                                         reply_markup = kb.get_back_to_members_menu(list_id))
    else:
        await callback.message.edit_text(text = "Участник удален!\nВыберите следующего для удаления:",
                                         reply_markup = kb.get_delete_members_menu(members_to_del, list_id))

#Функционал меню удаления участников (Inline keyboard)
@user.callback_query(F.data.startswith('member_del_'))
async def delete_members_list(callback: CallbackQuery):
    await callback.answer()
    list_id = int(callback.data.split('_')[2])
    list_name = await db.get_list_title(list_id)
    members = await db.list_members(list_id)

    creator_id = await db.get_list_creator(list_id)
    if callback.from_user.id != creator_id:
        msg = await callback.message.answer("Удалять участников может только создатель списка!")
        await asyncio.sleep(5)
        try:
            await msg.delete()
        except Exception:
            pass
        return
    
    await callback.answer()
    members_to_del = [m for m in members if m['tg_id'] != callback.from_user.id]
    if not members_to_del:
        await callback.message.edit_text(text = f"В списке <b>«{list_name}»</b> больше нет других участников!",
                                         reply_markup = kb.get_back_to_members_menu(list_id), parse_mode = 'HTML')
        return
    await callback.message.edit_text(text = f"Выберите участника для удаления из списка <b>«{list_name}»</b>:",
                                     reply_markup = kb.get_delete_members_menu(members_to_del, list_id), parse_mode = 'HTML')

#Функционал кнопки "Добавление участников" (Inline keyboard)
@user.callback_query(F.data.startswith('member_add_'))
async def add_member(callback: CallbackQuery):
    await callback.answer()
    list_id = int(callback.data.split('_')[2])
    list_name = await db.get_list_title(list_id)

    creator_id = await db.get_list_creator(list_id)
    if callback.from_user.id != creator_id:
        msg = await callback.message.answer("Добавлять участников может только создатель списка!")
        await asyncio.sleep(5)
        try:
            await msg.delete()
        except Exception:
            pass
        return
    
    await callback.answer()
    bot_username = (await callback.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start=invite_list_{list_id}"

    text = (f'Добавление участников в список <b>«{list_name}»</b>\n\n'
            'Чтобы пригласить кого-то, отправьте эту ссылку:\n'
            f'{invite_link}\n\n'
            'При переходе по ссылке пользователь станет участником списка')
    await callback.message.edit_text(text = text, reply_markup = kb.get_back_to_members_menu(list_id), parse_mode = 'HTML')





#Обработчик неизвестных сообщений и команд
@user.message()
async def word_handler(message: Message):
    error_message = await message.answer(text = '<b>Вы ввели неизвестную команду!</b>', parse_mode = 'HTML')
    await asyncio.sleep(5)

    try:
        await error_message.delete()
        await message.delete()
    except Exception:
        pass

#Отправка сообщений пользователям об изменении в общем списке
async def notify_list_members(callback_or_message, list_id: int, text: str):
    sender_id = callback_or_message.from_user.id
    bot = callback_or_message.bot
    members = await db.list_members(list_id)

    sender_name = "Пользователь"
    for member in members:
         if member['tg_id'] == sender_id:
            sender_name = member['name']
            break
    
    final_text = text.format(user_name = sender_name)
    for member in members:
            if member['tg_id'] != sender_id:
                try:
                    await bot.send_message(chat_id = member['tg_id'], text = final_text,parse_mode='HTML')
                except Exception as e:
                    print(f"Не удалось отправить уведомление пользователю {member['tg_id']}: {e}"
)