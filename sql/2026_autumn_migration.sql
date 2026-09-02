-- =====================================================================
-- Миграция групп: весна 2026 -> осень 2026 (новый учебный год)
--
-- Источник:
--   старая таблица 1mti1Ob_Q0BKeiwdtX-NA1yFQNmrHpT0KxnBjYT0dyIA (весна 2026)
--   новая  таблица 1rbrjpxqqqJ9YUuyWrP3kVN7kCPc_vhq1AufzZaAC6Mg (осень 2026)
--
-- ВАЖНО: номера групп переиспользуются между когортами.
--   Старая "3142" (1 курс) -> новая "3242" (2 курс),
--   а "3142" в новой таблице -- это уже новые первокурсники.
--   Поэтому пользователи ПЕРЕЦЕПЛЯЮТСЯ на другие строки groups,
--   а не переименовываются.
--
-- Порядок запуска:
--   1) PART 0 -- read-only аудит. Запустить отдельно, сверить вывод.
--   2) PART 1 -- сама миграция, одной транзакцией.
--
-- Если предыдущая попытка упала: сначала ROLLBACK, потом заново.
-- Пока сессия в аварийной транзакции, PostgreSQL глотает все команды
-- с ошибкой "current transaction is aborted" -- включая исправляющие.
-- =====================================================================


-- =====================================================================
-- PART 0. АУДИТ (read-only). Запустить ПЕРЕД миграцией.
-- =====================================================================

-- 0.1 Текущие курсы/группы и сколько в них юзеров
SELECT c.name AS course, g.name AS "group", g.id AS group_id, count(u.id) AS users
FROM groups g
JOIN courses c ON c.id = g.course_id
LEFT JOIN users u ON u.group_id = g.id
GROUP BY c.name, g.name, g.id
ORDER BY c.name, g.name;

-- 0.2 Дубли групп по (курс, имя) -- должно быть пусто.
--     Если не пусто, миграцию НЕ запускать: UPDATE ниже станет недетерминированным.
SELECT c.name AS course, g.name AS "group", count(*)
FROM groups g
JOIN courses c ON c.id = g.course_id
GROUP BY c.name, g.name
HAVING count(*) > 1;

-- 0.3 Как физически хранится роль (ожидается 'ADMIN' / 'USER' / 'GUEST').
--     Если в базе lowercase -- поправить литералы в PART 1.
SELECT DISTINCT role FROM users;

-- 0.4 Юзеры без группы
SELECT count(*) AS users_without_group FROM users WHERE group_id IS NULL;

-- 0.5 Отстали ли последовательности id от данных.
--     "ОТСТАЛА" -- любой INSERT упадёт на дубликате ключа. Пункт 1.3 это чинит,
--     но полезно увидеть заранее. last_value = NULL означает, что nextval ещё
--     ни разу не вызывался, то есть счётчик начнёт с 1.
SELECT
    t.name AS "table",
    s.last_value AS seq_last_value,
    t.max_id,
    CASE
        WHEN s.sequencename IS NULL THEN 'ПОСЛЕДОВАТЕЛЬНОСТЬ НЕ НАЙДЕНА'
        WHEN COALESCE(s.last_value, 1) <= t.max_id THEN 'ОТСТАЛА'
        ELSE 'ок'
    END AS verdict
FROM (
    SELECT 'courses' AS name, COALESCE(max(id), 0) AS max_id FROM courses
    UNION ALL SELECT 'groups', COALESCE(max(id), 0) FROM groups
    UNION ALL SELECT 'users', COALESCE(max(id), 0) FROM users
) t
LEFT JOIN pg_sequences s
    ON s.schemaname = 'public' AND s.sequencename = t.name || '_id_seq';

-- =====================================================================
-- PART 1. МИГРАЦИЯ
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- 1.1 Защита от повторного запуска.
--     Скрипт НЕ идемпотентен: второй прогон сдвинул бы курсы ещё раз
--     (2 курс уехал бы на 3-й и т.д.). Наличие таблицы бэкапа = уже мигрировали.
-- ---------------------------------------------------------------------
DO $$
BEGIN
    IF to_regclass('public.migration_backup_2026_autumn') IS NOT NULL THEN
        RAISE EXCEPTION
            'Миграция уже выполнялась: таблица migration_backup_2026_autumn существует. '
            'Повторный запуск сдвинет курсы повторно. Если это осознанный перезапуск -- '
            'переименуйте или удалите таблицу бэкапа вручную.';
    END IF;
END $$;


-- ---------------------------------------------------------------------
-- 1.2 Бэкап привязки юзеров к группам (постоянная таблица, для отката)
-- ---------------------------------------------------------------------
CREATE TABLE migration_backup_2026_autumn AS
SELECT
    u.id           AS user_id,
    u.telegram_id  AS telegram_id,
    u.role         AS old_role,
    u.group_id     AS old_group_id,
    g.name         AS old_group_name,
    c.name         AS old_course_name
FROM users u
LEFT JOIN groups g  ON g.id = u.group_id
LEFT JOIN courses c ON c.id = g.course_id;


-- ---------------------------------------------------------------------
-- 1.3 Синхронизация последовательностей id.
--
--     Если строки когда-то вставлялись с явными id (восстановление из дампа,
--     ручной INSERT), nextval отстал от данных: последовательность отдаёт 1,
--     а id=1 давно занят. Тогда INSERT ниже падает с
--       duplicate key value violates unique constraint "groups_pkey"
--
--     Делается через DO с проверкой, потому что setval -- STRICT-функция:
--     если pg_get_serial_sequence вернёт NULL, обычный SELECT setval(...)
--     вернёт пустую строку и молча ничего не сделает. Здесь это ошибка.
--
--     users тут не вставляется, но счётчик чиним и ей: если отстала и она,
--     у бота падает регистрация новых пользователей.
-- ---------------------------------------------------------------------
DO $$
DECLARE
    target_table text;
    sequence_name text;
    max_id bigint;
BEGIN
    FOREACH target_table IN ARRAY ARRAY['courses', 'groups', 'users'] LOOP
        sequence_name := pg_get_serial_sequence('public.' || target_table, 'id');

        IF sequence_name IS NULL THEN
            RAISE EXCEPTION
                'Не найдена последовательность id для таблицы %. Синхронизируйте '
                'счётчик вручную и запустите миграцию заново.', target_table;
        END IF;

        EXECUTE format('SELECT COALESCE(max(id), 0) FROM public.%I', target_table) INTO max_id;
        PERFORM setval(sequence_name, max_id + 1, false);
        RAISE NOTICE 'Последовательность % установлена на %', sequence_name, max_id + 1;
    END LOOP;
END $$;


-- ---------------------------------------------------------------------
-- 1.4 Курсы: убедиться, что все четыре существуют
-- ---------------------------------------------------------------------
INSERT INTO courses (name)
VALUES ('1 курс'), ('2 курс'), ('3 курс'), ('4 курс')
ON CONFLICT (name) DO NOTHING;


-- ---------------------------------------------------------------------
-- 1.5 Целевой набор групп нового года (как их отдаёт парсер новой таблицы)
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS tmp_new_groups;

CREATE TEMP TABLE tmp_new_groups (course_name text, group_name text);

INSERT INTO tmp_new_groups (course_name, group_name) VALUES
    ('1 курс', '3142'),
    ('1 курс', '3143'),
    ('1 курс', '3144'),
    ('1 курс', '3145'),
    ('1 курс', '3100'),
    ('1 курс', '3101'),
    ('2 курс', '3242'),
    ('2 курс', '3243'),
    ('2 курс', '3244'),
    ('2 курс', '3200'),
    ('2 курс', '3201'),
    ('3 курс', '3342'),
    ('3 курс', '3343'),
    -- Треки 3 курса поделены на подгруппы Z3300 / Z3301 (бывшие 3200 / 3201):
    -- в одной и той же паре у них разные предметы, поэтому трек и подгруппа
    -- склеены в одну группу. Имена совпадают с тем, что отдаёт парсер.
    ('3 курс', 'радио Z3300'),
    ('3 курс', 'радио Z3301'),
    ('3 курс', 'навигация Z3300'),
    ('3 курс', 'навигация Z3301'),
    ('3 курс', 'телеком Z3300'),
    ('3 курс', 'телеком Z3301'),
    ('4 курс', 'стф'),
    ('4 курс', 'нанооптика'),
    ('4 курс', 'моделирование'),
    ('4 курс', 'радио'),
    ('4 курс', 'навигация'),
    ('4 курс', 'телеком');

-- Создать недостающие группы. Существующие строки переиспользуются:
-- например (2 курс, 3200) остаётся той же строкой, но её прошлогодних
-- юзеров п. 1.7 выселит, а п. 1.6 заселит нынешних первокурсников.
INSERT INTO groups (name, course_id)
SELECT n.group_name, c.id
FROM tmp_new_groups n
JOIN courses c ON c.name = n.course_name
WHERE NOT EXISTS (
    SELECT 1 FROM groups g
    WHERE g.course_id = c.id AND g.name = n.group_name
);


-- ---------------------------------------------------------------------
-- 1.6 Соответствие групп прошлого года группам нового
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS tmp_group_mapping;

CREATE TEMP TABLE tmp_group_mapping (
    old_course text,
    old_group  text,
    new_course text,
    new_group  text
);

INSERT INTO tmp_group_mapping (old_course, old_group, new_course, new_group) VALUES
    -- 1 курс -> 2 курс
    ('1 курс', '3142',          '2 курс', '3242'),
    ('1 курс', '3143',          '2 курс', '3243'),
    ('1 курс', '3144-3145',     '2 курс', '3244'),  -- объединённая группа стала одной
    ('1 курс', '3100',          '2 курс', '3200'),
    ('1 курс', '3101',          '2 курс', '3201'),
    -- 2 курс -> 3 курс
    ('2 курс', '3242',          '3 курс', '3342'),
    ('2 курс', '3243',          '3 курс', '3343'),
    -- 3244 / 3200 / 3201 преемника не имеют: на 3 курсе это треки,
    -- поделённые на подгруппы (радио Z3300, навигация Z3301, ...).
    -- Трек за студента не выбрать, поэтому они уходят в GUEST, п. 1.7.
    -- 3 курс -> 4 курс
    ('3 курс', 'стф',           '4 курс', 'стф'),
    ('3 курс', 'нанооптика',    '4 курс', 'нанооптика'),
    ('3 курс', 'моделированеи', '4 курс', 'моделирование'),  -- опечатка в старой таблице
    ('3 курс', 'фбс',           '4 курс', 'радио'),
    ('3 курс', 'навигационные', '4 курс', 'навигация'),
    ('3 курс', 'телеком',       '4 курс', 'телеком');
    -- 4 курс выпустился: преемников нет, юзеры уходят в GUEST, п. 1.7.

-- Перевод. Одним UPDATE: PostgreSQL берёт source из снимка ДО апдейта,
-- поэтому цепочки 3242 -> 3342 и 3142 -> 3242 не конфликтуют между собой.
UPDATE users u
SET group_id = ng.id
FROM groups og
JOIN courses oc          ON oc.id = og.course_id
JOIN tmp_group_mapping m ON m.old_course = oc.name AND m.old_group = og.name
JOIN courses nc          ON nc.name = m.new_course
JOIN groups ng           ON ng.course_id = nc.id AND ng.name = m.new_group
WHERE u.group_id = og.id;


-- ---------------------------------------------------------------------
-- 1.7 Юзеры, чья прошлогодняя группа не имеет преемника:
--       2 курс 3244 / 3200 / 3201 -> на 3 курсе треки, выбор за студентом;
--       весь старый 4 курс        -> выпустились.
--
--     Считаем по бэкапу (снимок ДО п. 1.6), а не по текущему group_id:
--     строка группы могла уцелеть под тем же именем, но принадлежит уже
--     другой когорте.
--
--     Роль ADMIN сохраняется: RoleFilter пускает в registration_router
--     только GUEST, так что админа в гостя превращать нельзя.
-- ---------------------------------------------------------------------
UPDATE users u
SET group_id = NULL,
    role     = CASE WHEN u.role = 'ADMIN' THEN u.role ELSE 'GUEST' END
FROM migration_backup_2026_autumn b
WHERE b.user_id = u.id
  AND b.old_group_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM tmp_group_mapping m
      WHERE m.old_course = b.old_course_name
        AND m.old_group  = b.old_group_name
  );


-- ---------------------------------------------------------------------
-- 1.8 Удалить группы прошлого года, которых нет в новой таблице
-- ---------------------------------------------------------------------
DELETE FROM groups g
USING courses c
WHERE c.id = g.course_id
  AND (c.name, g.name) NOT IN (SELECT course_name, group_name FROM tmp_new_groups);


-- ---------------------------------------------------------------------
-- 1.9 Проверки. Смотреть вывод ПЕРЕД COMMIT.
-- ---------------------------------------------------------------------

-- Итоговый расклад: должен совпасть с tmp_new_groups, 25 строк, лишнего нет.
SELECT c.name AS course, g.name AS "group", count(u.id) AS users
FROM groups g
JOIN courses c ON c.id = g.course_id
LEFT JOIN users u ON u.group_id = g.id
GROUP BY c.name, g.name
ORDER BY c.name, g.name;

-- Кто именно уехал в GUEST (2 курс 3244/3200/3201 + весь старый 4 курс).
SELECT b.old_course_name, b.old_group_name, count(*) AS users
FROM migration_backup_2026_autumn b
JOIN users u ON u.id = b.user_id
WHERE u.group_id IS NULL AND b.old_group_id IS NOT NULL
GROUP BY b.old_course_name, b.old_group_name
ORDER BY b.old_course_name, b.old_group_name;

-- Админы без группы -- им группу выставить руками, регистрация им недоступна.
SELECT id, telegram_id, name FROM users WHERE role = 'ADMIN' AND group_id IS NULL;

-- Сверка количества: сколько было с группой / сколько стало.
SELECT
    (SELECT count(*) FROM migration_backup_2026_autumn WHERE old_group_id IS NOT NULL) AS had_group_before,
    (SELECT count(*) FROM users WHERE group_id IS NOT NULL)                            AS has_group_after;

COMMIT;
-- ROLLBACK;  -- если что-то в 1.9 не сошлось


-- =====================================================================
-- ОТКАТ (если уже закоммичено, а вернуть надо).
-- Работает только пока целы строки groups из бэкапа -- то есть если
-- п. 1.8 удалил группы, сначала пересоздать их с теми же id.
-- =====================================================================
-- BEGIN;
-- UPDATE users u
-- SET group_id = b.old_group_id, role = b.old_role
-- FROM migration_backup_2026_autumn b
-- WHERE b.user_id = u.id;
-- COMMIT;
