import psycopg2

database = "database" #название базы данных
user = "postgres" #имя пользователя
password = "00000" #пароль

help = '''
    create – команда создаст таблицы в базе данных.
    add – команда добавит клиента в созданные таблицы.
    find – команда ищет клиентов в базе.
    del – команда удаляет клиента из базы. 
    pa – phone add – команда добавляет номер телефона существующему клиенту. 
    pd – phone del – команда удаляет номер телефона существующего клиента. 
    change – команда изменяет данные существующего клиента.
'''

'''создание таблиц БД'''
def create_db(conn):
    with conn.cursor() as cur:
        cur.execute("""
        create table if not exists clients(
            id serial primary key,
            first_name varchar(40),
            last_name varchar(40),
            email varchar(255)
        );
        """)
        cur.execute("""
        create table if not exists phone(
            id serial primary key,
            number varchar(12),
            id_clients INTEGER NOT NULL REFERENCES clients(id)
        );
        """)
        conn.commit()

'''добавление нового клиента'''
def add_client(conn, first_name, last_name, email):
    with conn.cursor() as cur:
        cur.execute(f"""
        INSERT INTO clients(first_name, last_name, email) VALUES('{first_name}', '{last_name}', '{email}') RETURNING id;
        """)
        client_id = cur.fetchone()[0]
        print(f'Создан клиент id - {client_id}')
        conn.commit()
    return client_id

'''добавление телефона'''
def add_phone(conn, phone, client_id):
    with conn.cursor() as cur:
        cur.execute(f"""
            INSERT INTO phone(number, id_clients) VALUES('{phone}', '{client_id}') RETURNING id;
            """)
        contact_id = cur.fetchone()[0]
        print(f'Телефон {phone} добавлен с id {contact_id}')
        conn.commit()
    return contact_id

'''изменение клиента'''
def change_client(conn, client_id, first_name=None, last_name=None, email=None):
    with conn.cursor() as cur:
        set = []
        if first_name != '' and first_name != None:
            first_name = f"\nfirst_name = '{first_name}'"
            set.append(first_name)
        if last_name != '' and last_name != None:
            last_name = f"\nlast_name = '{last_name}'"
            set.append(last_name)
        if email != '' and email != None:
            email = f"\nemail = '{email}'"
            set.append(email)

        set = ', '.join(set)
        updateRequest = f"update clients set {set} where id = '{client_id}' RETURNING id;"
        cur.execute(updateRequest)
        response = cur.fetchall()
        conn.commit()
    return len(response) > 0

'''удаление телефона'''
def delete_phone(conn, client_id, phone):
    with conn.cursor() as cur:
        deleteRequest = f"DELETE FROM phone where id_clients = '{client_id}' and number = '{phone}' RETURNING id;"
        cur.execute(deleteRequest)
        response = cur.fetchall()
        conn.commit()
    return len(response)

'''удаление клиента'''
def delete_client(conn, client_id):
    with conn.cursor() as cur:
        cur.execute(f"DELETE FROM phone where id_clients = '{client_id}';")
        cur.execute(f"DELETE FROM clients where id = '{client_id}' RETURNING id;")
        response = cur.fetchall()
        conn.commit()
    return len(response)

'''поиск клиента'''
def find_client(conn, client_id=None, first_name=None, last_name=None, email=None, phone=None):
    with conn.cursor() as cur:
        selectRequest = '''
            select
                clients.id,
                clients.first_name,
                clients.last_name,
                clients.email,
                phone.number,
                phone.id
            from
                clients
                left join phone on phone.id_clients = clients.id
            where'''

        where = []
        if client_id != None:
            client_id = f"\nclients.client_id = '{client_id}'"
            where.append(client_id)
        if first_name != None:
            first_name = f"\nclients.first_name = '{first_name}'"
            where.append(first_name)
        if last_name != None:
            last_name = f"\nclients.last_name = '{last_name}'"
            where.append(last_name)
        if email != None:
            email = f"\nclients.email = '{email}'"
            where.append(email)
        if phone != None:
            phone = f"\nphone.phone = '{phone}'"
            where.append(phone)

        where = 'AND'.join(where)
        selectRequest += where + ';'
        print(selectRequest)

        cur.execute(selectRequest)
        response = cur.fetchall()

        conn.commit()
    return response

'''валидация ввода на длину строки'''
def validateString(str, count):
    return len(str) <= count

'''валидация ввода email'''
def validateEmail(str, count):
    isValid = False
    if (len(str) <= count and len(str) >= 6):
        str = str.split('@')
        if (len(str) == 2):
            domen = str[1].split('.')
            str = str[:-1]
            for symbol in domen:
                str.append(symbol)
            if(len(str) == 3):
                isValid = True
    return isValid

'''валидация номера телефона'''
def validatePhone(phone):
    nonValidSymbols = '+() -'
    if len(phone) > 0:
        for symbol in nonValidSymbols:
            phone = phone.replace(symbol, '')

        if (phone[0] == '8'):
            phone = '7' + phone[1:]
        phone = '+' + phone
    if (len(phone) != 12):
        phone = True
    return phone

'''валидация ввода'''
def enterRequiredData(str, count, validateRule):
    while True:
        data = input(str)
        if(validateRule(data, count)):
            break
    return data

'''блок команд для изменения данных клиента'''
def enter_change_client(conn):
    while True:
        client_id = input('Введите ID клиента, данные которого нужно поменять: ')

        if client_id == '/exit':
            break

        try:
            int(client_id)
        except ValueError:
            print(f'Введен некорректный ID {client_id}. Для выхода введите /exit')
            continue

        first_name = input('Введите фамилию: ').capitalize()
        last_name = input('Введите имя: ').capitalize()
        email = input('Введите e-mail: ').lower()

        if(first_name == '' and last_name == '' and email == ''):
            print('Недостаточно данных для изменения. Введите данные или /exit')
            continue
        elif(first_name != '' and validateString(first_name, 40) == False):
            print(f'Фамилия {first_name} получилась слишком длинной. Введите данные или /exit')
            continue
        elif(last_name != '' and validateString(last_name, 40) == False):
            print(f'Имя {last_name} получилось слишком длинным. Введите данные или /exit')
            continue
        elif(email != '' and validateEmail(email, 255) == False):
            print(f'Почта {email} некорректная. Введите данные или /exit')
            continue

        result = change_client(conn, client_id=client_id, first_name=first_name, last_name=last_name, email=email)
        if result:
            print(f'Данные клиента ID {client_id} успешно обновлены.')
            break
        else:
            action = input(f'Данные клиента ID {client_id} не были обновлены. Введите /exit для выхода или нажмите enter, чтобы продолжить: ')
            if action == '/exit':
                break

'''блок команд для удаления клиента'''
def enter_delete_client(conn):
    client_id = input('Введите ID клиента для удаления: ')
    count = delete_client(conn, client_id)
    if count > 0:
        print('Клиент успешно удален')
    else:
        print(f'Не найден клиент с ID {client_id}')

'''блок команд для удаления телефона'''
def enter_delete_phone(conn):
    exit = False
    while True:
        if(exit):
            break

        client_id = input('Введите ID клиента для удаления его телефона: ')
        if(client_id == '/exit'):
            break
        else:
            try:
                int(client_id)
            except ValueError:
                print(f'Введен некорректный ID {client_id}. Для выхода введите /exit')
                continue

            while True:
                phone = input('Введите номер телефона для удаления: ')

                if phone == '/exit':
                    exit = True
                    break
                else:
                    validedPhone = validatePhone(phone)
                    if validedPhone:
                        count = delete_phone(conn, client_id, validedPhone)
                        message = 'Введите /exit для выхода или нажмите enter, чтобы удалить другой номер этого клиента: '
                        if count > 0:
                            print(f'Телефон {phone} удален')
                            action = input(message)
                            if action == '/exit':
                                exit = True
                        else:
                            print(f'Телефон {phone} не найден у клиента с ID {client_id}')
                            action = input(message)
                            if action == '/exit':
                                exit = True
                    else:
                        print(f'Введен некорректный номер телефона {phone}. Для выхода введите /exit')
                        continue

'''блок команд для добавления нового клиента'''
def enter_client_data(conn):
    first_name = enterRequiredData('Введите фамилию клиента: ', 40, validateString).capitalize()
    last_name = enterRequiredData('Введите имя клиента: ', 40, validateString).capitalize()
    email = enterRequiredData('Введите e-mail клиента: ', 255, validateEmail).lower()

    client_id = add_client(conn, first_name, last_name, email)

    while True:
        phone = input('Введите номер телефона. Если не требуется, введите /exit.\nНомер телефона: ')
        if(phone == '/exit'):
            break
        elif (validatePhone(phone)):
            add_phone(conn, validatePhone(phone), client_id)
        else:
            print('Введен не правильный номер телефона.')

'''блок команд для поиска клиента'''
def enter_data_to_find_client(conn):
    while True:
        first_name = input('Введите фамилию: ').capitalize()
        if (first_name == ''):
            first_name = None
        last_name = input('Введите имя: ').capitalize()
        if (last_name == ''):
            last_name = None
        email = input('Введите email: ').lower()
        if (email == ''):
            email = None
        phone = input('Введите телефон: ')
        if (phone == ''):
            phone = None

        if(first_name == None and last_name == None and email == None and phone == None):
            print('Не было введено данных для поиска.\nЕсли желаете прекратить, введите /exit\nЕсли желаете продолжить, нажимите Enter')
            action = input()
            if action == '/exit':
                break
            else:
                continue

        if (phone != None):
            validatedPhone = validatePhone(phone)

        if (phone == False):
            print(f'Введен не правильный номер телефона {phone}. В поиске он не будет использован.')
            validatedPhone = None

        response = find_client(conn, first_name=first_name, last_name=last_name, email=email, phone=phone)

        if len(response) > 0:
            clients = {}
            for q in response:
                try:
                    clients[q[0]]
                except KeyError:
                    clients[q[0]] = {}

                clients[q[0]]['first_name'] = q[1]
                clients[q[0]]['last_name'] = q[2]
                clients[q[0]]['email'] = q[3]

                try:
                    clients[q[0]]['phone']
                except KeyError:
                    clients[q[0]]['phone'] = []

                if (q[4] != None):
                    clients[q[0]]['phone'].append(q[4])

            print('ID / ФАМИЛИЯ / ИМЯ / E-MAIL / ТЕЛЕФОНЫ')
            for q in clients.keys():
                if len(clients[q]['phone']) >= 1:
                    phone = ", ".join(clients[q]['phone'])
                    print(f'{q} / {clients[q]["first_name"]} / {clients[q]["last_name"]} / {clients[q]["email"]} / {phone}')
                else:
                    print(f'{q} / {clients[q]["first_name"]} / {clients[q]["last_name"]} / {clients[q]["email"]} / Отсутствует')
        else:
            print('Ничего не найдено.')
        break

'''блок команд для добавления телефона'''
def enter_client_phone(conn):
    exit = False
    while True:
        if(exit):
            break

        client_id = input('Введите ID клиента для добавления ему телефона: ')
        if(client_id == '/exit'):
            break
        else:
            try:
                int(client_id)
            except ValueError:
                print(f'Введен некорректный ID {client_id}. Для выхода введите /exit')
                continue

            while True:
                phone = input('Введите номер телефона: ')
                if phone != '/exit':
                    validedPhone = validatePhone(phone)
                    if validedPhone:
                        count = add_phone(conn, validedPhone, client_id)
                        message = 'Введите /exit для выхода или нажмите enter, чтобы добавить другой номер этого клиента: '
                        if count > 0:
                            action = input(message)
                            if action == '/exit':
                                exit = True
                                break
                    else:
                        print(f'Введен некорректный номер телефона {phone}. Для выхода введите /exit')
                        continue
                else:
                    exit = True
                    break

with psycopg2.connect(database = database, user="postgres", password="brenn") as conn:
        
    while True:
        print('''
        =====
        Введите h для получения списка доступных команд
        =====
        ''')
        command = input("Введите команду: ").lower()
        if command == "create":
            create_db(conn)
            break
        elif command == "add":
            enter_client_data(conn)
            break
        elif command == "find":
            enter_data_to_find_client(conn)
            break
        elif command == "del":
            enter_delete_client(conn)
            break
        elif command == "pa":
            enter_client_phone(conn)
            break
        elif command == "pd":
            enter_delete_phone(conn)
            break
        elif command == "as":
            enter_change_client(conn)
            break
        elif command == "h":
            print(help)
            break
        else:
            print("Введена некорректная команда.")
    conn.close()