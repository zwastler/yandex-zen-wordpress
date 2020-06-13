# yandex-zen parser to wordpress

Простой парсер канала zen.yandex.ru и загрузка статей на сайт wordpress.
Позволяет выгрузить все кроме видео (включая прикрепленные в статьях картинки, ссылки, и т.д.)

## Использование

### установите зависимости:
```
pip3 install -r requirements.txt
```

### в файле zen_parser.py укажите название канала, ссылку на ваш Wordpress сайт, логин и пароль.
```
zen_channel_name = 'freelife'  # yandex.zen channel name
client = Client(url='https://example.com/xmlrpc.php', username='user', password='ppass')  # change WP url, login, pass
```

## p.s. 
Парсер очень простой. синхронный, медленный.
выкладываю как есть, вдруг кому понадобится.