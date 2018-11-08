import json
import re
import random
from lxml import etree
import time
from util.timeconvert import timer
import pymongo
import redis
import setting
import requests
import multiprocessing
# from cr_extract import cr
"""
账号
密码
"""

class ManheimSpider():
    def __init__(self):
        self.s = requests.session()
        self.s.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36'}
        self.url = 'https://www.manheim.com'
        

       
        self.conn = redis.StrictRedis(setting.REDIS_URL, setting.REDIS_PORT)
        client = pymongo.MongoClient(setting.MONGODB_URL, setting.MONGODB_PORT)
        self.collection = client['vehicle']['vehicle']
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

            'user[username]': ''

            'user[password]': ''
            'submit': 'Login',
        }
        self.s.post(login_url, data=data) # 登陆
        resp = self.s.get('https://www.manheim.com/members/mymanheim/')
        # print(resp.text)


    def getFirstListPage(self):
        # data = {
        #     'vehicleTypes': '-1',
        #     'fromYear': 'ALL', # 起始年份
        #     'toYear': 'ALL', # 结束年份
        #     # 'make': '101000004' # 车辆品牌编码 101000005==audi
        # }

        resp = self.s.post('https://www.manheim.com/members/powersearch/searchSubmit.do')
        # print(resp.text)
        # with open('list_html_first.html', 'w', encoding='utf8') as f:
        #     f.write(resp.text)
        # self.data_extract(resp)

        total_pages=self.getTotalPages(resp)
        # 获取总页数
        # self.page_nums = total_pages//25 + 1 if isinstance(total_pages/25, float) else total_pages/25
        # print(self.page_nums)
    #     翻页url：https://www.manheim.com/members/powersearch/searchResults.do?WT.svl=m_ps_srp_next
        # 获取总页数
        return total_pages
    def getTotalPages(self, resp):
        """获取总页数"""
        html = etree.HTML(resp.text)
        try:
            html_str = html.xpath("//div[@class='mui-pagination']/a[@class='next']/@href")[0]
            total_pages_str = re.search(r'\d+, (\d+), 25', html_str).group(1)
            return int(total_pages_str)
        except:
            return None
    def getNextListPage(self, current_page):
        data = {
            'searchOperation': 'Paging',
            'sellerCompany': '',
            'newSort': 'false',
            'sortKeys': 'YEAR',
            'previousSortKeys': '',
            'sortIndicator': 'FORWARD',
            # 'recordOffset': '25', # 翻页！ 第一页：0；第二页：25；第三页：50
            'recordOffset': '{}'.format(current_page*25-25),
            # 'vehicleTypes': '104000001',
            # 'vehicleTypes': '104000002',
            # 'vehicleTypes': '104000003',
            # 'vehicleTypes': '104000004',
            # 'make': '101000004', # 入参
            'fromYear': '', # 入参
            'toYear': '', # 入参
            'distance': '',
            'distanceUnits': '',
            'zipCode': '',
            'saleDate': '',
            'certified': '',
            'searchTerms': '',
            'listingFromTime': '',
            'listingToTime': '',
            'submittedFilters': '',
            'vehicleUniqueId': '',
            'detailPageUrl': '',
            'vin': '',
            'channel': '',
            'displayDistance': '',
            'saleId': '',
            'saleGroupId': '',
            'fromOdometer': '0',
            'toOdometer': 'ALL',
            'fromValuation': '0',
            'toValuation': 'ALL',
            'valuationType': 'MMR',
            'includeMissingValuations': 'on',
            'conditionGradeRefined': 'false',
            'fromConditionGrade': '0.0',
            'toConditionGrade': '5.0',
            'resultsPerPage': '25',
            # 'resultsPerPage': '25',
            'srpSortKeys': '',
            'wbSortKeys': '',
            'wbResultsPerPage': '25',
            'srpResultsPerPage': '25',
            'wtTracker': '(wtSearchType, PowerSearch Other)(wtRefLinkPrefix, ps_srp_)(wtSavedSearchRefLink, )(wtSavedSearchTypeLink, )',
            # 'searchResultsOffset': '25' # 翻页！ 第一页：0；第二页：25；第三页：50
            'searchResultsOffset': '{}'.format(current_page*25-25)
        }
        # https://www.manheim.com/members/powersearch/searchResults.do?WT.svl=m_ps_srp_next
        resp = self.s.post('https://www.manheim.com/members/powersearch/searchResults.do?WT.svl=m_ps_srp_next', data=data)
        # print(resp.content)
        # print(resp.request.headers)
        # with open('list_html_{}.html'.format(current_page), 'w', encoding='utf8') as f:
        #     f.write(resp.text)
        # print(current_page)
        # print(resp.text)
        self.data_extract(resp,current_page)
        # cr.run()
        print('第%d页提取完毕' % current_page)
    def AutoCheck(self,url):
        """获取事故出现次数字段的提取"""
        if url=='':
            return ''
        resp = self.s.get(url)
        html = etree.HTML(resp.text)
        accidentNumber = html.xpath("//table[@id='vehicle-info']/tbody/tr[3]/td[1]/text()")[0].strip() if len(html.xpath("//table[@id='vehicle-info']/tbody/tr[3]/td[1]/text()"))>0 else ''
        return accidentNumber

    def getDetailFields(self,url,current_page,index):
        '''

        获取详情页所需字段

        '''
        resp=self.s.post(url)
        html= etree.HTML(resp.text)

        year=html.xpath("//div[@class='ui-p-b span16-16']/div[1]/div[1]/span/text()")[0]
        name=html.xpath("//div[@class='ui-p-b span16-16']/div[1]/div[3]/span/text()")[0]
        make=html.xpath("//div[@class='ui-p-b span16-16']/div[1]/div[2]/span/text()")[0]
        trim=html.xpath("//div[@class='ui-p-b span16-16']/div[1]/div[4]/span/text()")[0]
        cylinderNumber=html.xpath("//div[@class='ui-p-b span16-16']/div[1]/div[9]/span/text()")[0].split(' ')[0]
        displacement=html.xpath("//div[@class='ui-p-b span16-16']/div[1]/div[10]/span/text()")[0]
        transmissionType=html.xpath("//div[@class='ui-p-b span16-16']/div[1]/div[11]/span/text()")[0]
        modelldentityNo=html.xpath("//div[@class='ui-p-b span16-16']/div[2]/div/span/text()")[0][0:8]
        driverType=4 if html.xpath("//div[@class='ui-p-b span16-16']/div[2]/div[9]/span/text()")[0] in ['All Wheel Driver','Full Wheel Driver'] else 2
        print('详情页字段')
        print(1,year)
        print(2,make)
        print(3,trim)
        print(4,name)
        print(5,cylinderNumber)
        print(6,transmissionType)
        print(7,modelldentityNo)
        print(8,displacement)
        print(9,driverType)
        print('详情页字段')
        collection = self.save_data()
        collection.update({'_id':'%07d' % current_page+'%02d' % index},{'$set':{'year':year,'make':make,'trim':trim,
                                                                                'driverType':driverType}})
    def data_extract(self,resp,current_page=1):
        """
        数据提取入口
        """
        html = etree.HTML(resp.text)
        # 进行分组
        div_list = html.xpath('//div[@class="wbMain mui-m-h-tb"]')
        for index, div in enumerate(div_list):
            print(index)
            description = div.xpath('.//a[@target]/text()')[0].strip()

            title_url = 'https://www.manheim.com/members/powersearch/' + div.xpath(".//a[@target]/@href")[0]


            # ------获取详情页面的信息字段--------
            time.sleep(3)
            self.getDetailFields(title_url,current_page,index)




            vehicleldentityNo = div.xpath('.//div/div/p/text()')[0]

            odometer = div.xpath("./div[2]/div[1]/div[1]/div[2]/span/text()")[0]

            conditionGrade =div.xpath(".//div[@class='mui-icon-row']/a[last()]/text()")[0] if len(
                div.xpath(".//div[@class='mui-icon-row']/a[last()]/text()")) > 0 else ''  # 可能没有
            try:
                href = div.xpath("./div[2]/div/div/div[2]/div/div/a[last()-2]/@href")[0]  # 可能不存在
                # str = "javascript:openECR('http://windowsticker-prod.aws.manheim.com/showGmWs?auctionID=AAAW&vin=5GAERBKW3KJ103226&workOrderNumber=7307952&sblu=11907338', '5GAERBKW3KJ103226');"
                windowStickerFile = re.search(r'^http[^ ]', href).group().rstrip('\',')  # 可能不存在
            except:
                windowStickerFile = ''

            pickCity = div.xpath("./div[2]/div[2]/p[1]/text()")[0].strip()

            pickupFacilitation = div.xpath("./div[2]/div[2]/p[2]/text()")[0]

            seller = div.xpath("./div[2]/div[2]/p[3]/text()")[0].strip()

            Color = div.xpath("./div[2]/div[1]/div[1]/div[1]/div/text()")[0].split(" | ") if len(div.xpath("./div[2]/div[1]/div[1]/div[1]/div/text()"))>0 else ''
            if Color=='':
                exteriorColor=''
                interiorColor=''
            else:
                exteriorColor = Color[0] if Color[0]!='—' else ''
                interiorColor = Color[1] if Color[1]!='—' else ''

            # manheimMarketReport = div.xpath("./div[2]/div[3]/div/div/div/div/div/a/text()")[0]
            manheimMarketReport=div.xpath(".//a[@class='bold']/text()")[0] if len(div.xpath(".//a[@class='bold']"))>0 else ''
            eventTitle = div.xpath("./div[2]/div[2]/a/text()")[0] if len(
                div.xpath("./div[2]/div[2]/a/text()")) > 0 else ''  # 可能不存在

            eventLink = 'https://www.manheim.com/members/powersearch/' + div.xpath("./div[2]/div[2]/a/@href")[0] if len(
                div.xpath("./div[2]/div[2]/a/@href")) > 0 else ''  # 可能不存在

            # bidStartsAt_str1 = div.xpath("./div/div[2]/h3/span[1]/text()")[0]
            # bidStartsAt_str2 = div.xpath("./div/div[2]/h3/span[3]/text()")[0] if len(div.xpath("./div/div[2]/h3/span[3]/text()"))>0 else ''
            # # print('页面时间：',bidStartsAt_str1,bidStartsAt_str2)
            # # bidEndsAt_str = div.xpath("./div/div[2]/div/span[2]/text()")
            # bidEndsAt_str = div.xpath("./div[1]/div[2]/div/span[last()]/text()")
            # # print(bidEndsAt_str,'-'*10)
            bidLineNumber=''
            bidRunNumber=''
            bidEndsAt=''
            bidPlatform=''
            bidStartsAt=''
            # buyNowPrice=''
            # bidPrice=''
            # offerAcceptable=''
            # bidStartsAt=''
            # bidPlatform=''
            # bidStartsAt=timer.start_timestamp(bidStartsAt_str1,bidStartsAt_str2)
            # if bidStartsAt > time.time(): #未开始拍卖
            #     bidPlatform = div.xpath("./div/div[2]/div/span[1]/text()")[0].strip()
            #     bidLineNumber_bidRunNumber = div.xpath(".//span[@class='laneRun']/text()")[0]
            #     bidLineNumber = bidLineNumber_bidRunNumber.split(' / ')[0]
            #     bidRunNumber = bidLineNumber_bidRunNumber.split(' / ')[1]
            # else: #已开始拍卖
            #     bidEndsAt_str = div.xpath(".//span[@class='timeLeft']/text()")[0]
            #     bidEndsAt = timer.end_timestamp(bidEndsAt_str)
            #
            # bidPlatform = div.xpath("./div/div[2]/div/span[1]/text()")[0].strip()
            buyNowPrice = div.xpath("./div[2]/div[3]/div/div/div2/input[@name='BUY NOW']/@value")[0].split(' ')[
                2] if len(div.xpath("./div[2]/div[3]/div/div/div2/input[@name='BUY NOW']/@value")) > 0 else ''
            bidPrice = div.xpath("./div/div[2]/input[@name='BID']/@value")[0].split(' ')[1] if len(
                div.xpath("./div/div[2]/input[@name='BID']/@value")) > 0 else ''
            offerAcceptable = True if len(div.xpath("./div[2]/div[3]/div/div[2]/div/input/@name")) > 0 else False


            sellerGrade = div.xpath("./div[2]/div[2]/div/div/div/b/text()")[0].strip() if len(
                div.xpath("./div[2]/div[2]/div/div/div/b/text()")) > 0 else ''  # 可能没有这个字段
            # 获取自动检测的url以便于进一步提取accidentNumber
            autocheck_url = re.search(r'http.*\'',
                                      div.xpath(".//a[@class='autocheckLink']/@href")[0]).group().rstrip('\',') if len(div.xpath(".//a[@class='autocheckLink']/@href"))>0 else ''
            accidentNumber=self.AutoCheck(autocheck_url)

            self.collection.insert({'_id':'%07d' % current_page+'%02d' % index,'description':description,'vehicleldentityNo':vehicleldentityNo,'odometer':odometer,'conditionGrade':conditionGrade,'windowStickerFile':windowStickerFile,
                               'pickCity':pickCity,'pickupFacilitation':pickupFacilitation,'seller':seller,'exteriorColor':exteriorColor,'interiorColor':interiorColor,
                               'manheimMarketReport':manheimMarketReport,'eventTitle':eventTitle,'eventLink':eventLink,
                               'bidPlatform':bidPlatform,'bidStartsAt':bidStartsAt,'bidLineNumber':bidLineNumber,
                               'bidRunNumber':bidRunNumber,'bidEndsAt':bidEndsAt,'buyNowPrice':buyNowPrice,'bidPrice':bidPrice,
                               'offerAcceptable':offerAcceptable,'sellerGrade':sellerGrade,'accidentNumber':accidentNumber})
            cr_url_str = div.xpath(".//a[@class='icon icon-cr']/@onclick")[0] if len(
                div.xpath(".//a[@class='icon icon-cr']/@onclick")) > 0 else ''
            if cr_url_str != '':
                # <a href="#stayput" onclick="openECR('https://www.edgepipeline.com/components/vehicle/detail/aaahouston/60880?&amp;username=yuzhongkai&amp;locale=en_US&amp;listingID=141681328&amp;channel=OVE', 'WBA4Z1C55KEE44534');; return false;" class="icon icon-cr">cr</a>
                cr_url = re.search(r'http.+US', cr_url_str).group()

                value = "%07d" % current_page + "%02d" % index
                value1 = {"_id": value, "url": cr_url}
                svalue1 = json.dumps(value1)
                self.conn.sadd("CR_url", svalue1)
            else:
                cr_url = ''
            # print(1, description)
            # print(2, vehicleldentityNo)
            # print(3, odometer)
            # print(4, conditionGrade)
            # print(5, pickCity)
            # print(6, pickupFacilitation)
            # print(7, seller)
            # print(8, sellerGrade)
            # print(9, exteriorColor)
            # print(10, interiorColor)
            # print(11, eventTitle)
            # print(12, eventLink)
            # print(13, manheimMarketReport)
            # print(14, windowStickerFile)
            # print(15, autocheck_url)
            # print(16, bidStartsAt)
            # print(17, bidEndsAt)
            # print(18, bidLineNumber)
            # print(19, bidRunNumber)
            # print(20, bidPlatform)
            # print(21, buyNowPrice)
            # print(22, bidPrice)
            # print(23, offerAcceptable)
            # print(bidPlatform)
            # print(24, cr_url)
            # print(25, title_url)
            # print(26,accidentNumber)

    def run(self):

        self.getCookies()
        total_pages=self.getFirstListPage() # 在函数中调用提取数据方法
        # for page_num in range(self.page_nums)[1:]: # 翻页
        # for page_num in range(3)[1:]:  # 翻页
        # total_pages=self.getTotalPages(resp)
        print(total_pages)
        if total_pages:
            #for 循环获取每一页
            for i in range(1,total_pages+1):
                time.sleep(random.randint(10,15))
                print('-' * 20)
                # p=multiprocessing.Process(target=self.getNextListPage,args=(i,))
                self.getNextListPage(i) # 在函数中调用提取数据方法
                time.sleep(3)
                # p.start()


if __name__ == '__main__':

    s = ManheimSpider()
    s.run()
