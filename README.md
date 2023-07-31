## Таблица в режиме реального времени

Реализация состоит из трёх приложений: сервера, клиента и приложения, которое обновляет данные в таблице.

### Приложение для обновления

Раз в секунду генерирует 50 случайных обновлений строк (добавление, удаление, обновление) и отправляет запрос серверу
на обновление этих строк. Также раз в 30 секунд делает запрос к серверу на изменение порядка сортировки таблицы.

### Клиент

Графическое приложение на Tkinter для отображения таблицы. Показывает окно размером в N строк с возможностью прокрутки 
и сортировки по столбцам. При нажатии на название столбца сортировка последовательно сменяется по кругу (дефолтная на
сервере, по возрастанию столбца, по убыванию столбца). В отдельном потоке клиент принимает от сервера обновлённые строки
таблицы (строки, которые изменило приложение для обновления).

### Сервер

Таблица хранится в виде списка из словарей, где каждый словарь - это строка таблицы. Клиент создаёт два сокета: первый
для работы с запросами и ответами, второй для приёма изменений, которые делает приложение для обновления, чтобы
изменения были сразу видны у клиента. Если сервер получает от клиента запрос на сортировку, то копия таблицы
сортируется и клиенту отправляются строки из этой отсортированной копии таблицы, которые находятся в окне, которое
он просматривает. Также сохраняется вид сортировки у клиента, чтобы при скроле выдавать строки с учётом этой сортировки.
Если сервер получает запрос на выдачу строк, то есть когда клиент делает скрол, то копия таблицы сортируется с учётом
сохранённого для этого клиента вида сортировки, и клиенту отправляются нужные строки. Если сервер получает запрос на
обновление таблицы или изменение сортировки от приложения, которое делает обновления, то он обновляет таблицу и
рассылает всем клиентам обновлённые строки, если они лежат в окне, которое просматривает клиент.

### Запуск

Сервер и приложение для обновления запускаются в docker контейнерах, клиент запускается вручную командой
python3 client.py --host 127.0.0.1 --port 5000 --num_rows "размер окна". Сервер и приложение для обновления запускаются
одной командой docker compose up -d.

### P.s.
На самом деле по-хорошему нужно ещё сделать адекватную обработку всевозможных ошибок, добавить логирование,
выделить некоторые куски кода в функции, но это сделать я уже не успеваю.