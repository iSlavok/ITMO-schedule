from contextlib import suppress
from datetime import date, timedelta
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from app.database import User, Role
from app.filters import RoleFilter
from app.keyboards.user import main_keyboard, ranking_order_keyboard, get_pagination_rating_keyboard, \
    get_rating_keyboard
from app.schedule import Lesson
from app.services import ScheduleService, AiService, RatingService

router = Router()
router.message.filter(RoleFilter(Role.USER))


@router.callback_query(
    F.data == "main_menu",
    flags={"services": ["schedule", "rating"]}
)
async def get_main_menu(callback: CallbackQuery, state: FSMContext, user: User, schedule_service: ScheduleService,
                        rating_service: RatingService):
    with suppress(Exception):
        await callback.answer()
        await callback.message.delete()
    await send_schedule(callback.message, user, schedule_service, rating_service, state, date.today(), "сегодня",
                        is_today=True)


@router.message(
    F.text == "Рейтинг"
)
async def get_rating_menu(message: Message, state: FSMContext):
    with suppress(Exception):
        await message.delete()
    new_message = await message.answer(
        f"Выберите, какой рейтинг вы хотите посмотреть:",
        reply_markup=ranking_order_keyboard
    )
    await delete_last_message(message, state, new_message.message_id)


@router.callback_query(
    F.data == "rating_menu",
)
async def get_rating_menu_button(callback: CallbackQuery, state: FSMContext):
    await get_rating_menu(callback.message, state)


@router.callback_query(
    F.data.startswith("rating_"),
    flags={"services": ["rating"]}
)
async def show_rating(callback: CallbackQuery, state: FSMContext, rating_service: RatingService):
    with suppress(Exception):
        await callback.answer()
        await callback.message.delete()
    is_best = callback.data.split("_")[1] == "best"
    page = int(callback.data.split("_")[2])
    rating = rating_service.get_top_lecturers_with_rank(page, ascending=not is_best)
    text = "<b>" + ("Лучшие преподаватели:" if is_best else "Худшие преподаватели:") + "</b>\n\n"
    for lecturer, rank, avg_rating, reviews_count in rating:
        text += f"{rank}. {lecturer} — ⭐️{avg_rating} ({reviews_count} оценок)\n"
    new_message = await callback.message.answer(
        text,
        reply_markup=get_pagination_rating_keyboard(page, rating_service.get_lecturers_page_count(), is_best),
    )
    await delete_last_message(callback.message, state, new_message.message_id)


@router.message(
    F.text == "Оценить",
    flags={"services": ["rating", "schedule"]}
)
async def select_rating(message: Message, state: FSMContext, rating_service: RatingService,
                        schedule_service: ScheduleService, user: User):
    with suppress(Exception):
        await message.delete()
    last_lecturer = schedule_service.get_last_lecturer(user.group.name)
    if last_lecturer:
        lecturer = rating_service.get_lecturer(last_lecturer)
        if lecturer:
            if rating_service.can_user_rate_lecturer(user.user_id, lecturer.id):
                new_message = await message.answer(
                    f"Выберите оценку для преподавателя {lecturer.name}:",
                    reply_markup=get_rating_keyboard(lecturer.id)
                )
            else:
                new_message = await message.answer(
                    f"Сегодня вы уже оценили преподавателя {lecturer.name}.",
                    reply_markup=main_keyboard
                )
            return await delete_last_message(message, state, new_message.message_id)
    new_message = await message.answer(
        "Нет доступного преподавателя для оценки.",
        reply_markup=main_keyboard
    )
    await delete_last_message(message, state, new_message.message_id)


@router.callback_query(
    F.data.startswith("add_rating_"),
    flags={"services": ["rating", "schedule"]}
)
async def submit_rating(callback: CallbackQuery, state: FSMContext, rating_service: RatingService,
                        schedule_service: ScheduleService, user: User):
    with suppress(Exception):
        await callback.answer()
        await callback.message.delete()
    lecturer_id, rating = map(int, callback.data.split("_")[2:])
    last_lecturer = schedule_service.get_last_lecturer(user.group.name)
    if not last_lecturer or rating_service.get_lecturer(last_lecturer).id != lecturer_id:
        new_message = await callback.message.answer("Вы не можете оценить этого преподавателя.")
        return await delete_last_message(callback.message, state, new_message.message_id)
    rating = rating_service.create_rating(rating, lecturer_id, callback.from_user.id)
    if rating:
        new_message = await callback.message.answer(
            f"Оценка {rating.rating} для преподавателя {rating.lecturer.name} успешно добавлена.",
            reply_markup=main_keyboard
        )
    else:
        new_message = await callback.message.answer(
            "Сегодня вы уже оценили этого преподавателя.",
            reply_markup=main_keyboard
        )
    await delete_last_message(callback.message, state, new_message.message_id)


@router.message(
    flags={"services": ["schedule", "ai", "rating"]},
)
async def get_schedule(message: Message, user: User, schedule_service: ScheduleService, ai_service: AiService,
                       rating_service: RatingService, state: FSMContext):
    await message.delete()
    if message.text == "Сегодня":
        day = date.today()
        day_str = "сегодня"
    elif message.text == "Завтра":
        day = date.today() + timedelta(days=1)
        day_str = "завтра"
    else:
        day = await ai_service.date_parsing(message.text)
        if not day:
            return
        else:
            day_str = day.strftime("%Y-%m-%d")

    await send_schedule(message, user, schedule_service, rating_service, state, day, day_str, message.text == "Сегодня")


async def send_schedule(message: Message, user: User, schedule_service: ScheduleService, rating_service: RatingService,
                        state: FSMContext, day: date, day_str: str, is_today: bool = False):
    schedule = schedule_service.get_schedule(day, user.group.name)
    if schedule is None:
        return

    text = schedule_to_text(schedule, day_str, schedule_service, rating_service, is_today=is_today)
    schedule_message = await message.bot.send_message(message.chat.id, text, reply_markup=main_keyboard)

    await delete_last_message(message, state, schedule_message.message_id)


async def delete_last_message(message, state, new_message_id):
    data = await state.get_data()
    old_message = data.get("last_message_id")
    if old_message:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=old_message)
        except Exception:
            pass
    await state.update_data(last_message_id=new_message_id)


def schedule_to_text(schedule: list[Lesson], day: str, schedule_service: ScheduleService, rating_service: RatingService,
                     is_today: bool = False):
    current, is_waiting = 0, False
    if is_today:
        current, is_waiting = schedule_service.get_current_lesson()
    text = (f"📆 <b>Расписание на {day}</b> 📆\n"
            "════════════════════════")
    for lesson in schedule:
        text += lesson_to_text(lesson, current, is_waiting, rating_service)
    return text


def lesson_to_text(lesson: Lesson, current_lesson: int, is_waiting: bool, rating_service: RatingService):
    status_emoji = get_lesson_status_emoji(lesson.number, current_lesson, is_waiting)
    text = f"\n\n{status_emoji} <b>{times[lesson.number - 1]}</b> | {lesson.number} пара\n"
    text += f"📚 {lesson.name}"
    if lesson.type:
        text += f" — {lesson.type}"
    text += "\n"
    if lesson.lecturer:
        rating = rating_service.get_lecturer_rating(lesson.lecturer)
        emoji = get_rating_emoji(rating)
        text += f"{emoji} {lesson.lecturer}"
        if rating is not None:
            text += f" | ⭐️{rating}"
        text += "\n"
    if lesson.room:
        text += f"🚪 Аудитория: <b>{lesson.room}</b>\n"
    text += "\n———————————————"
    return text


def get_lesson_status_emoji(lesson_number: int, current_lesson: int, is_waiting: bool):
    if lesson_number == current_lesson:
        return "🔴" if is_waiting else "🟠"
    elif lesson_number < current_lesson:
        return "✅"
    else:
        return "🕒"


def get_rating_emoji(rating: float):
    if rating is None or rating >= 4.5:
        return "👨"
    elif rating >= 4.0:
        return "👨🏽"
    elif rating >= 3.5:
        return "👨🏾"
    elif rating >= 2.0:
        return "🌚"
    else:
        return "🤡"


times = [
    "8.10-9.40",
    "9.50-11.20",
    "11.30-13.00",
    "13.30-15.00",
    "15.30-17.00",
    "17.10-18.40",
    "18:40-20:10",
]
