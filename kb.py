from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

verif_btn = [
    [InlineKeyboardButton(text="ВЕРИФИКАЦИЯ", callback_data="verif")]
]
verif = InlineKeyboardMarkup(inline_keyboard=verif_btn)


admin_menu = [
        [
            KeyboardButton(text="💬 Отправить список чатов"),
            KeyboardButton(text="❇️ Запустить")
        ],
        [
            KeyboardButton(text="👾 Проверить прокси"),
            
        ]
    ]
admin_menu = ReplyKeyboardMarkup(
    keyboard=admin_menu,
    resize_keyboard=True,
    input_field_placeholder="Выберите пункт..."
    )
