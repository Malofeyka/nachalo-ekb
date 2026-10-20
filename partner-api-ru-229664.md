# Платформа AMAkids — передача заявок с сайта (API)

Инструкция описывает, как отправлять **заявки (лиды)** с вашего сайта в CRM платформы
AMAkids. Каждая заявка сразу появляется в CRM вашей франшизы как новый лид.

- **Адрес API** — любой из двух, они работают одинаково:
  `https://kidsplatform.ru/api/` или `https://amaclass.ru/platform/api/`
- Все ответы приходят в формате **JSON**.

---

## Ваши данные для подключения

| Поле | Значение |
|------|----------|
| `app_code` | `6` |
| `key` (секретный ключ) | `00a3635effa806b70c804b4d0de35cccb284da6432c867d758ed27b3` |
| `franch_id` (ваша франшиза) | `229664` |

> **Ключ секретный.** Не размещайте его в открытом коде страницы (HTML, JavaScript
> в браузере): оттуда его может скопировать кто угодно. Отправляйте заявки
> **со своего сервера** (обработчик формы на PHP, Node.js и т. п.).

Параметр `master` передавать **не нужно**.

---

## Адрес запроса

Можно использовать любой из доменов — результат одинаковый.

| Метод | kidsplatform.ru | amaclass.ru |
|-------|-----------------|-------------|
| GET | `https://kidsplatform.ru/api/add_lead_get` | `https://amaclass.ru/platform/api/add_lead_get` |
| POST | `https://kidsplatform.ru/api/add_lead_post` | `https://amaclass.ru/platform/api/add_lead_post` |

Параметры у всех адресов одинаковые:

- `add_lead_get` — параметры в строке запроса;
- `add_lead_post` — параметры в теле запроса (`application/x-www-form-urlencoded`
  или `multipart/form-data`).

Все значения передаются в кодировке **UTF-8**, в GET-запросе — с URL-кодированием
(например, `+` в телефоне — `%2B`).

---

## Параметры

| Параметр | Обязательный | Описание |
|----------|:---:|----------|
| `app_code` | да | `6` |
| `key` | да | Ваш секретный ключ |
| `franch_id` | да | `229664` |
| `name` | да | Имя клиента |
| `phone` | да | Телефон клиента |
| `email` | нет | Email клиента |
| `birth_date` | нет | Дата рождения ребёнка. Рекомендуемый формат `ГГГГ-ММ-ДД` (`2015-06-15`), также принимаются `ДД.ММ.ГГГГ` и `ДД/ММ/ГГГГ`. Некорректная дата просто не сохранится |
| `comment` | нет | Комментарий к заявке |
| `subject_code` | нет | Направление, которым интересуется клиент (коды — ниже) |
| `filial_id` | нет | ID вашего центра, если заявка относится к конкретному центру (сообщит AMAkids) |
| `target_utm_params` | нет | UTM-метки в виде JSON-строки, например `{"utm_source":"yandex","utm_campaign":"autumn"}` |

### Коды направлений (`subject_code`)

| `subject_code` | Направление |
|----------------|-------------|
| `mental_arithmetic` | Ментальная арифметика |
| `mental_arithmetic_online` | Ментальная арифметика онлайн |
| `memorica` | Меморика |
| `liberica` | Либерика |
| `speedcubing` | Спидкубинг |
| `alphabetica` | Букварика |
| `multiplication_table_online` | Таблица умножения онлайн |
| `preschool` | Подготовка к школе |
| `amamath` | Амаматика |
| `english` | Английский язык |

Если передан неизвестный код, заявка всё равно создастся, просто без направления.

---

## Примеры

В примерах используется `https://kidsplatform.ru/api/`. Для amaclass.ru замените
начало адреса на `https://amaclass.ru/platform/api/` — всё остальное без изменений.

### GET

```
https://kidsplatform.ru/api/add_lead_get?app_code=6&key=00a3635effa806b70c804b4d0de35cccb284da6432c867d758ed27b3&franch_id=229664&name=%D0%98%D0%B2%D0%B0%D0%BD&phone=%2B79991234567&email=ivan%40example.com&subject_code=mental_arithmetic&birth_date=2016-03-20&comment=%D0%97%D0%B0%D1%8F%D0%B2%D0%BA%D0%B0%20%D1%81%20%D1%81%D0%B0%D0%B9%D1%82%D0%B0
```

### POST (curl)

```bash
curl -X POST "https://kidsplatform.ru/api/add_lead_post?app_code=6" \
  --data-urlencode "key=00a3635effa806b70c804b4d0de35cccb284da6432c867d758ed27b3" \
  --data-urlencode "franch_id=229664" \
  --data-urlencode "name=Иван" \
  --data-urlencode "phone=+79991234567" \
  --data-urlencode "email=ivan@example.com" \
  --data-urlencode "subject_code=mental_arithmetic" \
  --data-urlencode "birth_date=2016-03-20" \
  --data-urlencode "comment=Заявка с сайта"
```

### PHP (обработчик формы на вашем сервере)

```php
<?php
$apiBase = 'https://kidsplatform.ru/api/'; // или 'https://amaclass.ru/platform/api/'

$params = [
    'key'          => '00a3635effa806b70c804b4d0de35cccb284da6432c867d758ed27b3',
    'franch_id'    => 229664,
    'name'         => $_POST['name'],
    'phone'        => $_POST['phone'],
    'email'        => $_POST['email'] ?? '',
    'subject_code' => 'mental_arithmetic',
    'comment'      => $_POST['comment'] ?? '',
];

$ch = curl_init($apiBase . 'add_lead_post?app_code=6');
curl_setopt_array($ch, [
    CURLOPT_POST           => true,
    CURLOPT_POSTFIELDS     => http_build_query($params),
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT        => 15,
]);
$result = json_decode(curl_exec($ch), true);
curl_close($ch);

if (($result['status'] ?? '') === 'ok') {
    // Заявка создана, $result['lead_id'] — её номер в CRM
} else {
    // Ошибка: $result['error']
}
```

---

## Ответ сервера

### Успех

```json
{
  "status": "ok",
  "lead_id": 123456
}
```

### Ошибки

Ответ вида `{"status": "fail", "error": "..."}`:

| `error` | Причина |
|---------|---------|
| `empty key` | Не передан или неверный ключ `key` |
| `empty required parameter: franch_id` | Не передан `franch_id` |
| `incorrect parameter: franch_id` | `franch_id` не `229664` |
| `param filial_id is incorrect or the filial is not owned by specified franch_id` | Неверный `filial_id`: центр не найден или не относится к вашей франшизе |
| `empty required parameters: name, phone, franch_id` | Не заполнены имя или телефон |
| `database_error` | Внутренняя ошибка — повторите запрос позже |

Если не передан или неверен `app_code`, ответ будет `{"status": false, "error": "unknown app"}`.

---

## Важно

- **Одна заявка — один запрос.** Дубли не отсеиваются: повторная отправка той же
  формы создаст ещё одну заявку. Защитите форму от двойного нажатия.
- Обязательны только `name` и `phone` (плюс `app_code`, `key`, `franch_id`) —
  остальные поля можно не передавать.
- По вопросам подключения обращайтесь в AMAkids.
