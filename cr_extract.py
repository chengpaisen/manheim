import requests
from lxml import etree
import pymongo
import redis
import json
import re

# def parse_CR_url(CR_url):
#     resp = requests.get(CR_url,session=self.session)
#     CR_html_str = resp.text
#     return CR_html_str

# rediscli = redis.Redis(host='192.168.199.154', port=6379, db=0,decode_responses=True)
# mongocli = pymongo.MongoClient(host='192.168.199.154',port=27017)
# mon_db =  mongocli['vehicle']['vehicle']




class CR():
    map_heat_num = 1

    def __init__(self):
        self.s = requests.session()
        self.s.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36'}
        self.url = 'https://www.manheim.com'


        self.rediscli = redis.Redis(host='192.168.199.132', port=6379, db=0, decode_responses=True)
        self.mongocli = pymongo.MongoClient(host='192.168.199.132', port=27017)
        self.mon_db = self.mongocli['vehicle']['vehicle']

        # =====================导入封装好了包含session的对象
    def getCookies(self):
        """登陆获取cookies"""
        self.s.get(self.url)
        self.s.get('https://publish.manheim.com/en/locations/international.html')
        self.s.get('https://manheim.demdex.net/dest5.html?d_nsid=0')
        self.s.get('https://publish.manheim.com/en/locations/us-locations.html?WT.svl=m_uni_hdr')
        resp = self.s.get('https://www.manheim.com/login?WT.svl=m_uni_hdr')
        self.s.get('https://manheim.demdex.net/dest5.html?d_nsid=0')
        # print(resp.text)
        authenticity_token = re.search('name="authenticity_token" type="hidden" value="(.*?)" />', resp.text).group(1)
        # print(authenticity_token)
        login_url = 'https://www.manheim.com/login/authenticate'
        data = {
            'utf8': '✓',
            'authenticity_token': authenticity_token,
            'user[username]': 'yuzhongkai',
            'user[password]': 'sl8m79mg3',
            'submit': 'Login',
        }
        self.s.post(login_url, data=data) # 登陆


    # 从redis获取数据。提取出CR的url和_id
    def get_redis_data(self):
        redis_CR_str = self.rediscli.spop('CR_url')
        print(redis_CR_str,type(redis_CR_str))
        CR_url_dic = json.loads(redis_CR_str)
        CR_url_id = CR_url_dic['_id']
        CR_url = CR_url_dic['url']
        print('～～成功从master节点的redis队列中获取到了1个cr_url～～')
        return CR_url_id,CR_url

    '''
    函数:抽取CR页面信息。使用xpath来抽取。
    判断CR为新版页面还是旧版页面。
       若新版：则返回 ①2轮驱动位置。 ②热力图文档url ③position/treadDepth/brand/size
       若旧版：则返回 ①空          ②空          ③position/treadDepth/brand/size
    备注:关于②，写一个函数，接收参数（热力图的html代码），把热力图html代码写入文档，返回文档的路径。
    '''

    def extract_CR_page(self,CR_url_id,CR_url):
        # ====================
        CR_html_obj = self.s.get(url=CR_url)
        html = etree.HTML(CR_html_obj.text)
        logo = html.xpath('//*[@class="logo"]') #xpath包含class="logo"的标签，新版有logo，旧版没有。

        # 先判断是new_CR还是old_CR 。若列表长度为0，则为旧CR。
        if len(logo) == 0:
            L_F_treadDepth = html.xpath('//*/td[text()="Left Front:"]/../td[2]/text()')
            L_F_brand = html.xpath('//*/td[text()="Left Front:"]/../td[3]/text()')
            L_F_size = html.xpath('//*/td[text()="Left Front:"]/../td[4]/text()')

            L_R_treadDepth = html.xpath('//*/td[text()="Left Rear:"]/../td[2]/text()')
            L_R_brand = html.xpath('//*/td[text()="Left Rear:"]/../td[3]/text()')
            L_R_size = html.xpath('//*/td[text()="Left Rear:"]/../td[4]/text()')

            R_F_treadDepth = html.xpath('//*/td[text()="Right Front:"]/../td[2]/text()')
            R_F_brand = html.xpath('//*/td[text()="Right Front:"]/../td[3]/text()')
            R_F_size = html.xpath('//*/td[text()="Right Front:"]/../td[4]/text()')

            R_R_treadDepth = html.xpath('//*/td[text()="Right Rear:"]/../td[2]/text()')
            R_R_brand = html.xpath('//*/td[text()="Right Rear:"]/../td[3]/text()')
            R_R_size = html.xpath('//*/td[text()="Right Rear:"]/../td[4]/text()')

            L_F_treadDepth = L_F_treadDepth[0] if len(L_F_treadDepth)>0 else ''
            L_F_brand = L_F_brand[0] if len(L_F_brand)>0 else ''
            L_F_size = L_F_size[0] if len(L_F_size)>0 else ''

            L_R_treadDepth = L_R_treadDepth[0] if len(L_R_treadDepth)>0 else ''
            L_R_brand = L_R_brand[0] if len(L_R_brand)>0 else ''
            L_R_size = L_R_size[0] if len(L_R_size)>0 else ''

            R_F_treadDepth = R_F_treadDepth[0] if len(R_F_treadDepth)>0 else ''
            R_F_brand = R_F_brand[0] if len(R_F_brand)>0 else ''
            R_F_size =  R_F_size[0] if len(R_F_size)>0 else ''

            R_R_treadDepth = R_R_treadDepth[0] if len(R_R_treadDepth)>0 else ''
            R_R_brand =  R_R_brand[0] if len(R_R_brand)>0 else ''
            R_R_size =  R_R_size[0] if len(R_R_size)>0 else ''

            # 提取图片url
            url_list = html.xpath('//*[@class="thumbnails"]//a/img/@src')

            self.mon_db.update({'_id':CR_url_id},{'$set':{'L_F_treadDepth':L_F_treadDepth,'L_F_brand':L_F_brand,'L_F_size':L_F_size,'L_R_treadDepth':L_R_treadDepth,'L_R_brand':L_R_brand,'L_R_size':L_R_size,'R_F_treadDepth':R_F_treadDepth,'R_F_brand':R_F_brand,'R_F_size':R_F_size,'R_R_treadDepth':R_R_treadDepth,'R_R_brand':R_R_brand,'R_R_size':R_R_size,'url_list':url_list}})

            print(L_F_treadDepth,L_F_brand,L_F_size,L_R_treadDepth,L_R_brand,L_R_size,R_F_treadDepth,R_F_brand,R_F_size,R_R_treadDepth,R_R_brand,R_R_size)
            print(url_list)


        else: #新CR

            drivetrain = html.xpath('//span[@class="drivetrain"]/text()') #驱动位置

            L_F_brand = html.xpath('//*[@class ="layout"]/div[1]/div[2]/text()')
            L_F_treadDepth = html.xpath('//*[@class="layout"]/div[1]/div[3]/text()')
            L_F_size = html.xpath('//*[@class="layout"]/div[1]/div[4]/text()')

            R_F_brand = html.xpath('//*[@class="layout"]/div[2]/div[2]/text()')
            R_F_treadDepth = html.xpath('//*[@class ="layout"]/div[2]/div[3]/text()')
            R_F_size = html.xpath('//*[@class="layout"]/div[2]/div[4]/text()')

            L_R_brand = html.xpath('//*[@class ="layout"]/div[3]/div[2]/text()')
            L_R_treadDepth = html.xpath('//*[@class="layout"]/div[3]/div[3]/text()')
            L_R_size = html.xpath('//*[@class="layout"]/div[3]/div[4]/text()')

            R_R_brand = html.xpath('//*[@class="layout"]/div[4]/div[2]/text()')
            R_R_treadDepth = html.xpath('//*[@class ="layout"]/div[4]/div[3]/text()')
            R_R_size = html.xpath('//*[@class="layout"]/div[4]/div[4]/text()')

            L_F_treadDepth = L_F_treadDepth[0] if len(L_F_treadDepth) > 0 else ''
            L_F_brand = L_F_brand[0] if len(L_F_brand) > 0 else ''
            L_F_size = L_F_size[0] if len(L_F_size) > 0 else ''

            L_R_treadDepth = L_R_treadDepth[0] if len(L_R_treadDepth) > 0 else ''
            L_R_brand = L_R_brand[0] if len(L_R_brand) > 0 else ''
            L_R_size = L_R_size[0] if len(L_R_size) > 0 else ''

            R_F_treadDepth = R_F_treadDepth[0] if len(R_F_treadDepth) > 0 else ''
            R_F_brand = R_F_brand[0] if len(R_F_brand) > 0 else ''
            R_F_size = R_F_size[0] if len(R_F_size) > 0 else ''

            R_R_treadDepth = R_R_treadDepth[0] if len(R_R_treadDepth) > 0 else ''
            R_R_brand = R_R_brand[0] if len(R_R_brand) > 0 else ''
            R_R_size = R_R_size[0] if len(R_R_size) > 0 else ''

            print(L_F_treadDepth, L_F_brand, L_F_size, L_R_treadDepth, L_R_brand, L_R_size, R_F_treadDepth, R_F_brand,
                  R_F_size, R_R_treadDepth, R_R_brand, R_R_size)

            self.mon_db.update({'_id':CR_url_id},{'$set':{'L_F_treadDepth':L_F_treadDepth,'L_F_brand':L_F_brand,'L_F_size':L_F_size,'L_R_treadDepth':L_R_treadDepth,'L_R_brand':L_R_brand,'L_R_size':L_R_size,'R_F_treadDepth':R_F_treadDepth,'R_F_brand':R_F_brand,'R_F_size':R_F_size,'R_R_treadDepth':R_R_treadDepth,'R_R_brand':R_R_brand,'R_R_size':R_R_size}})

            # 分别提取4类部位的损坏数量 Exterior  Interior  Structure  Other
            exterior_dam_num = int(html.xpath('//*[@id="cr-damage-list-item-exterior"]/a/text()')[0].split(' ')[1][1])
            interior_dam_num = int(html.xpath('//*[@id="cr-damage-list-item-interior"]/a/text()')[0].split(' ')[1][1])
            structural_dam_num = int(html.xpath('//*[@id="cr-damage-list-item-structural"]/a/text()')[0].split(' ')[1][1])
            other_dam_num = int(html.xpath('//*[@id="cr-damage-list-item-other"]/a/text()')[0].split(' ')[1][1])

            # 提取3张（Exterior  Interior  Structure）热力图的前端代码.为svg标签包含的代码
            exterior_heat_map = html.xpath('//*[@id="cr-damage-exterior"]//*[@class="flat-car-container print--hide"]')[0]
            interior_heat_map = html.xpath('//*[@id="cr-damage-interior"]//*[@class="flat-car-container print--hide"]')[0]
            frame_heat_map = html.xpath('//*[@id="cr-damage-structural"]//*[@class="flat-car-container print--hide"]')[0]

            # 转为字符串
            ext_svg_code = etree.tostring(exterior_heat_map, method='html').decode()
            int_svg_code = etree.tostring(interior_heat_map, method='html').decode()
            frame_svg_code = etree.tostring(frame_heat_map, method='html').decode()
            merge_heat_map = ext_svg_code + '\n' + int_svg_code + '\n' + frame_svg_code

            svg_html = '''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <title>Title</title>
                <link rel="styleSheet" type="text/css" href="./cr-display.min.css" />
            </head>
            <body>
                %s
            </body>
            </html>
            ''' % (merge_heat_map)

            with open('./heat_map_code%d.html'%CR.map_heat_num,'w') as f:  #交付时，文件名需要改为英文
                f.write(svg_html)
                print('创建热力图文件')
            CR.map_heat_num += 1

            # 判断是否有信息。①如果exterior_dam_num大于0说明有信息需要返回。
            if exterior_dam_num > 0:
                # 提取具体损坏部位的信息。先分组，再提取
                exterior_damage_items = html.xpath('//*[@id="exterior_damage_items"]')[0]
                for i in range(exterior_dam_num):
                    dam_list = exterior_damage_items.xpath('./div[%d]' % (i + 1))[0]
                    # name = dam_list[3]
                    # Condition = dam_list[12]
                    # Severity = dam_list[16]
                    # Type = dam_list[20]

                    name = dam_list.xpath('.//*[@class="damage-item__header"]/span[2]/text()')[0]
                    Condition = dam_list.xpath('.//*[@class="damage-value mui-m-n"]/text()')[0]
                    Severity = dam_list.xpath('.//*[@class="damage-value"]/text()')[0]
                    Type = dam_list.xpath('.//*[@class="damage-value"][2]//text()')

                    Type = Type[0].strip() + '  ' + Type[1] if len(Type) > 1 else Type[0]

                    Additional = dam_list.xpath('.//*[@class="damage-value damage-value--block mui-m-h-b"]/text()')
                    Additional = Additional[0] if len(Additional) > 0 else ''
                    # 获取图片位置的div的class属性的值
                    url_div = dam_list.xpath('./div[2]/div[1]')[0]
                    url_div_class = url_div.xpath('./@class')[0]
                    # if 'has' in url_div_class:
                    #     url = url_div.xpath('./img/@src')
                    #     print(url)
                    # else:
                    #     url = ''
                    url = url_div.xpath('./img/@src')[0] if 'has' in url_div_class else ''

                    print('损伤位置类型为：Exterior,第%d个' % (i + 1), name, Condition, Severity, Type, Additional, url + '\n',
                          )
                    # 数据入库
                    self.mon_db.update({'_id':CR_url_id},{'$set':{'Condition':Condition, 'Severity':Severity, 'Type':Type, 'Additional':Additional, 'url':url}})

            else:
                # name = ''
                # Condition = ''
                # Severity = ''
                # Type = ''
                # url = ''
                name, Condition, Severity, Type, url ,Additional= '', '', '', '', '',''
                self.mon_db.update({'_id': CR_url_id}, {'$set': {'Condition': Condition, 'Severity': Severity, 'Type': Type, 'Additional': Additional,'url': url}})

            # ②interior_dam_num
            if interior_dam_num > 0:
                # 提取具体损坏部位的信息。先分组，再提取
                interior_damage_items = html.xpath('//*[@id="interior_damage_items"]')[0]
                for i in range(interior_dam_num):
                    dam_list = interior_damage_items.xpath('./div[%d]' % (i + 1))[0]
                    # name = dam_list[3]
                    # Condition = dam_list[12]
                    # Severity = dam_list[16]
                    # Type = dam_list[20]
                    name = dam_list.xpath('.//*[@class="damage-item__header"]/span[2]/text()')[0]
                    Condition = dam_list.xpath('.//*[@class="damage-value mui-m-n"]/text()')[0]
                    Severity = dam_list.xpath('.//*[@class="damage-value"]/text()')[0]
                    Type = dam_list.xpath('.//*[@class="damage-value"][2]//text()')
                    print(Type)
                    Type = Type[0].strip() + '  ' + Type[1] if len(Type) > 1 else Type[0]

                    Additional = dam_list.xpath('.//*[@class="damage-value damage-value--block mui-m-h-b"]/text()')
                    Additional = Additional[0] if len(Additional) > 0 else ''

                    # print(dam_list)
                    # 获取图片位置的div的class属性的值
                    url_div = dam_list.xpath('./div[2]/div[1]')[0]
                    url_div_class = url_div.xpath('./@class')[0]

                    url = url_div.xpath('./img/@src')[0] if 'has' in url_div_class else ''

                    print('损伤位置类型为：Interior,第%d个' % (i + 1), name, Condition, Severity, Type, Additional, url + '\n')
                    self.mon_db.update({'_id': CR_url_id}, {
                        '$set': {'Condition': Condition, 'Severity': Severity, 'Type': Type, 'Additional': Additional,
                                 'url': url}})
            else:
                name, Condition, Severity, Type, Additional,url = '', '', '', '', '', ''
                self.mon_db.update({'_id': CR_url_id},
                        {'$set': {'Condition': Condition, 'Severity': Severity, 'Type': Type, 'Additional': Additional,
                                  'url': url}})

            # ③structural_dam_num
            if structural_dam_num > 0:
                # 提取具体损坏部位的信息。先分组，再提取
                structural_damage_items = html.xpath('//*[@id="structural_damage_items"]')[0]
                for i in range(structural_dam_num):
                    dam_list = structural_damage_items.xpath('./div[%d]' % (i + 1))[0]
                    name = dam_list[3]
                    Condition = dam_list[12]
                    Severity = dam_list[16]
                    Type = dam_list[20]

                    Additional = dam_list.xpath('.//*[@class="damage-value damage-value--block mui-m-h-b"]/text()')
                    Additional = Additional[0] if len(Additional) > 0 else ''

                    # 获取图片位置的div的class属性的值
                    # url_div = html.xpath('//*[@id="structural_damage_items"]/div[%d]/div[2]/div[1]'%(i+1))[0]
                    url_div = structural_damage_items.xpath('.div[2]/div[1]')[0]
                    url_div_class = url_div.xpath('./@class')[0]

                    url = url_div.xpath('./img/@src')[0] if 'has' in url_div_class else ''

                    print('损伤位置类型为：Structural,第%d个' % (i + 1), name, Condition, Severity, Type, Additional, url + '\n',
                          )
                    self.mon_db.update({'_id': CR_url_id}, {
                        '$set': {'Condition': Condition, 'Severity': Severity, 'Type': Type, 'Additional': Additional,
                                 'url': url}})
            else:
                name, Condition, Severity, Type, Additional, url = '', '', '', '', '', ''
                self.mon_db.update({'_id': CR_url_id},
                        {'$set': {'Condition': Condition, 'Severity': Severity, 'Type': Type, 'Additional': Additional,
                                  'url': url}})
            # ④other_dam_num
            if other_dam_num > 0:
                # 提取具体损坏部位的信息。先分组，再提取
                other_damage_items = html.xpath('//*[@id="cr-damage-other"]')[0]
                for i in range(other_dam_num):
                    dam_list = other_damage_items.xpath('./div[%d]' % (i + 1))[0]

                    name = dam_list.xpath('.//*[@class="damage-item__header"]/span[2]/text()')[0]
                    Condition = dam_list.xpath('.//*[@class="damage-item"]/td[2]/span[1]/text()')[0]
                    Severity = dam_list.xpath('.//*[@class="damage-item"]/td[2]/span[2]/text()')[0]
                    Type = dam_list.xpath('.//*[@class="damage-item"]/td[3]//text()')
                    print(Type)
                    Type = Type[0].strip() + '  ' + Type[1] if len(Type) > 1 else Type[0]

                    Additional = dam_list.xpath('.//*[@class="damage-item"]/td[5]//text()')
                    Additional = ' '.join(Additional) if len(Additional) > 0 else ''

                    # 获取图片位置的div的class属性的值
                    url_div = dam_list.xpath('.//*[@class="damage-item"]/td[4]/div')[0]
                    url_div_class = url_div.xpath('./@class')[0]

                    url = url_div.xpath('./img/@src')[0] if 'has' in url_div_class else ''

                    print('损伤位置类型为：Other,第%d个' % (i + 1), name, Condition, Severity, Type, url + '\n')
                    self.mon_db.update({'_id': CR_url_id}, {
                        '$set': {'Condition': Condition, 'Severity': Severity, 'Type': Type, 'Additional': Additional,
                                 'url': url}})
            else:
                name, Condition, Severity, Type, url = '', '', '', '', ''
                self.mon_db.update({'_id': CR_url_id}, {
                    '$set': {'Condition': Condition, 'Severity': Severity, 'Type': Type, 'Additional': Additional,
                             'url': url}})

    # def getPhoto(self,html_str):
    #
    #     html=etree.HTML(html_str)
            print('开始打印图片url')
            # all_num=html.xpath('//a[@id="all"]/text()')[0]#.split(' ')[1].lstrip('(').rstrip(')'))
            # print(all_num)
            # exter_num=int(html.xpath('//a[@id="exterior"]/text()')[0].split(' ')[1].lstrip('(').rstrip(')'))
            # inter_num=int(html.xpath('//a[@id="interior"]/text()')[0].split(' ')[1].lstrip('(').rstrip(')'))
            # misc_num=int(html.xpath('//a[@id="misc"]/text()')[0].split(' ')[1].lstrip('(').rstrip(')'))
            # # damages_num=html.xpath('//a[@id="damages"]/text()')[0].split(' ')[1][0]
            # ext_list,int_list,misc_list,dam_list =[],[],[],[]
            # for i in range(all_num):
            #     if i < exter_num:
            #         exter_url=html.xpath("//div[@id='thumbnail-slider']/a[{}]/span/img/@src" .format(i+1))[0].split('?')[0]
            #         ext_list.append(exter_url)
            #     elif i < exter_num + inter_num:
            #         inter_url=html.xpath("//div[@id='thumbnail-slider']/a[{}]/span/img/@src" .format(i+1))[0].split('?')[0]
            #         int_list.append(inter_url)
            #     elif i < exter_num + inter_num + misc_num:
            #         misc_url=html.xpath("//div[@id='thumbnail-slider']/a[{}]/span/img/@src" .format(i+1))[0].split('?')[0]
            #         misc_list.append(misc_url)
            #     else:
            #         dam_url=html.xpath("//div[@id='thumbnail-slider']/a[{}]/span/img/@src" .format(i+1))[0].split('?')[0]
            #         dam_list.append(dam_url)
            # print
            exterior_url_list=html.xpath("//div[@id='thumbnail-slider']/a[@class='gallery_thumb_car exterior']/span/img/@src")
            interior_url_list=html.xpath("//div[@id='thumbnail-slider']/a[@class='gallery_thumb_car interior']/span/img/@src")
            misc_url_list=html.xpath("//div[@id='thumbnail-slider']/a[@class='gallery_thumb_car misc']/span/img/@src")
            damages_url_list=html.xpath("//div[@id='thumbnail-slider']/a[@class='gallery_thumb_car damages']/span/img/@src")
            self.mon_db.update({'_id': CR_url_id},
                        {'$set': {'exterior':exterior_url_list,'interior':interior_url_list,'misc':misc_url_list,'damages':damages_url_list}})

        CR.map_heat_num += 1

    def run(self):
        self.getCookies()
        # cr_id = self.get_redis_data()[0]
        # cr_url = self.get_redis_data()[1]
        # 死循环，不断从redis获取cr_url，发送请求执行爬取
        # 拿到一个cr_url，执行爬取

        while True:
            CR_url_id,CR_url = self.get_redis_data()
            print('正在处理：_id:%s cr_url:%s' %(CR_url_id,CR_url))
            self.extract_CR_page(CR_url_id,CR_url)


# with open('./CR_new_page_test4.html') as f:
#     page_html_str = f.read()

# cr = CR()
# cr.extract_CR_page(page_html_str)

    # cr = CR()
    # cr.extract_CR_page(CR_url,CR_url_id,CR_url)
if __name__ == '__main__':
    cr=CR()
    cr.run()
