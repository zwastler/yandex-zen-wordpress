from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.compat import xmlrpc_client
from wordpress_xmlrpc.methods import media, posts
import urllib
import requests
from bs4 import BeautifulSoup
from urllib.request import urlopen
import string
import random


# Не забываем указать свои данные
zen_channel_name = 'freelife'  # yandex.zen channel name
client = Client(url='https://example.com/xmlrpc.php', username='user', password='ppass')  # change WP url, login, pass


existingPostTitles = []
SEEK_ATTRIBUTES = ['p', 'h2', 'h3', 'img']


def parseTitle(parse_soup):
    tag = parse_soup.find(class_='article__title')
    tag = removeAttr(tag, "class")
    tag = removeAttr(tag, "itemprop")
    return tag


def parseHtml(soup):
    html_body = soup.find(class_='article__content')
    if not html_body: return False
    html_parse_list = html_body.find_all(SEEK_ATTRIBUTES)
    return html_parse_list


def id_generator(size=10, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def removeAttr(tag, attrName):
    del tag[attrName]
    return tag


def getImageSrc(tag):
    try:
        dataSet = ""
        if tag.has_attr("data-srcset") and tag["data-srcset"] != '':
            dataSet = tag['data-srcset'].split(',')[1].strip().replace(" 2x", "")
        if tag.has_attr("srcset") and tag["srcset"] != '' and dataSet == "":
            dataSet = tag['srcset'].split(',')[1].strip().replace(" 2x", "")
        if tag.has_attr("data-src") and tag["data-src"] != '' and dataSet == "":
            dataSet = tag['data-src']
        if tag.has_attr("src") and dataSet == "" and dataSet == "":
            dataSet = tag['src']
    except:
        return ''
    return dataSet


def downloadImage(url):
    name = url.split('/')[-1]
    f = open(url, 'wb')
    f.write(urlopen(name).read())
    f.close()
    return


def downloadImageStream(url, directory, alias, i):
    try:
        if url == '': return False
        imgData = urlopen(url).read()
        # name = id_generator() + ".jpg"
        name = alias.split('-')
        name.pop()
        name = '-'.join(name)
        name = name + '-' + str(i) + '.jpg'
        output = open(directory + "/" + name, 'wb')
        output.write(imgData)
        output.close()
        return name
    except Exception as e:
        print("Can't download img " + url)
        pass


def processParagraph(tag):
    tag = removeAttr(tag, "class")
    return tag


def processHeaderTwo(tag):
    tag = removeAttr(tag, "class")
    return tag


def processHeaderThree(tag):
    tag = removeAttr(tag, "class")
    return tag


def processHeaderImg(tag, directory, alias, i):
    tag = removeAttr(tag, "class")
    bigImgSrc = getImageSrc(tag)
    if tag.has_attr("data-src"):
        tag = removeAttr(tag, "data-src")
    if tag.has_attr("data-srcset"):
        tag = removeAttr(tag, "data-srcset")
    if tag.has_attr("srcset"):
        tag = removeAttr(tag, "srcset")
    new_name = downloadImageStream(bigImgSrc, directory, alias, i)
    if not new_name: return False
    tag["src"] = [new_name]
    return tag


def imageUpload(img_url, file_name=None, i=None):
    cleanImgUrl = img_url.split('?')[0]
    imageName = img_url.split('/')[-1]
    cleanImgName = imageName.split('?')[0]
    fileImg = urllib.request.urlretrieve(cleanImgUrl, cleanImgName)
    imageType = fileImg[1]['Content-Type']
    if file_name:
        fname = file_name.split('-')
        fname.pop()
        fname = '-'.join(fname)
        if i: fname += '_%s' % i
        data = {'name': fname + '.' + imageType.split('/')[-1], 'type': imageType}
    else:
        data = {'name': cleanImgName + '.' + imageType.split('/')[-1], 'type': imageType}
    with open(cleanImgName, 'rb') as img:
        data['bits'] = xmlrpc_client.Binary(img.read())
    print(data)
    response = client.call(media.UploadFile(data))
    return response


def generateAlias(url):
    return url.split('/')[-1]


def makeSoup(url):
    return BeautifulSoup(urlopen(url), 'html.parser')


items = []
link_channel = 'https://zen.yandex.ru/api/v3/launcher/export?channel_name=%s' % zen_channel_name

res = requests.get(link_channel).json()
items.extend(res['items'])

links = res['more']['link']
while 'link' in res['more']:
    rres = requests.get(links)
    try:
        pres = rres.json()
        items.extend(pres['items'])
        links = pres['more']['link']
    except:
        pass
        break

urls = [ii['link'].split('?')[0] for ii in items if 'link' in ii]

for url in urls:
    print("Start processing URL: " + url)
    alias = generateAlias(url)
    soup = makeSoup(url)
    html_p_list = parseHtml(soup)
    if not html_p_list: continue
    i = 1
    content, image = "", None
    for tag in html_p_list:
        el = tag.name
        if el == "p":
            tag = processParagraph(tag)
        if el == "h2":
            tag = processHeaderTwo(tag)
        if el == "h3":
            tag = processHeaderThree(tag)
        if el == "img":
            if not image:
                image = getImageSrc(tag)
                continue
            if not tag: continue
            if getImageSrc(tag) != '':
                img_id = imageUpload(getImageSrc(tag), alias, i=i)
            else:
                continue
            img_tag = '<!-- wp:image {"id":%s,"sizeSlug":"large"} --><figure class="wp-block-image size-large"><img src="%s" alt="" class="wp-image-%s"/></figure><!-- /wp:image -->' % (
                img_id['id'], img_id['link'], img_id['id']
            )
            content += img_tag
            i += 1
            continue

        try:
            content += tag.prettify()
        except Exception as e:
            print('Exception: %s' % e)

    img_id = imageUpload(image, alias)

    post = WordPressPost()
    post.title = soup.find(class_='article__title').text
    post.content = content
    post.mime_type = "text/html"
    post.user = 2  # WP Author ID
    post.link = alias
    post.post_type = "post"
    post.thumbnail = img_id['id']
    post.post_status = "publish"  # "draft"
    post_id = client.call(posts.NewPost(post))
    print("Post: %s (%s) Done!" % (post_id, alias))
