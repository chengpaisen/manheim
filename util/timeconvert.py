import time


class TimeStamp():

    MONTH_DICT = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,'Aug':8,'Sept':9,'Oct':10,'Nov':11,'Dec':12}

    def start_timestamp(self,str1,str2):

        '''
        拍卖开始时间转换
        params:str2可能为 '' 或者 09:30 am  或者12:30 pm; str1为 “Oct 10”

        '''

        MONTH_DICT = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,'Aug':8,'Sept':9,'Oct':10,'Nov':11,'Dec':12}
        month=self.MONTH_DICT[str1.split(' ')[0]]
        day=str1.split(' ')[1]
        if str2=='':
            detail_time = '2018-{}-{} 00:00:00'.format(month,day)
            print(1,detail_time)
        elif str2.split(' ')[1]=='pm' and str2.split(':')[0] != '12':
            hour=int(str2.split(':')[0])+12
            minute=str2.split(' ')[0].split(':')[1]
            detail_time = '2018-{}-{} {}:{}:00'.format(month,day,hour,minute)
            print(2,detail_time)

        else:
            hour = str2.split(':')[0]
            minute = str2.split(' ')[0].split(':')[1]
            detail_time = '2018-{}-{} {}:{}:00'.format(month, day, hour, minute)
            print(3,detail_time)

        # 时间转成时间戳之前，先拼接成为右边的时间格式 dt = "2016-05-05 20:28:54"
        # detail_time = '2018-%s-%s %s:00' % (month, day, str2[0])
        # print('xpath获取到的时间:',detail_time)

        # 转换成时间数组
        timeArray = time.strptime(detail_time, "%Y-%m-%d %H:%M:%S")
        # 转换成时间戳
        timestamp = time.mktime(timeArray)
        return timestamp
    def end_timestamp(self,end_time_str):
        """
        结束时间戳的转换
        param : end_time_str 为 '(13 Hours 42 Minutes)'

        :return:
        """
        # shengyu_time1 = '(2 Days 8 Hours 36 Minutes)'
        # shengyu_time2 = '(9 Hours 36 Minutes)'
        # shengyu_time3 = '(9 Hours)'
        # shengyu_time4 = '(36 Minutes)'
        time_list=end_time_str.lstrip('(').rstrip(')').split(' ')
        if 'Days' in time_list:
            Days = int(time_list[time_list.index('Days') - 1])
        elif 'Day' in time_list:
            Days = 1
        else:
            Days=0

        if 'Hours' in time_list:
            Hours = int(time_list[time_list.index('Hours') - 1])
        elif 'Hour' in time_list:
            Hours = 1
        else:
            Hours=0

        if 'Minutes' in time_list:
            Minutes = int(time_list[time_list.index('Minutes') - 1])
        elif 'Minute' in time_list:
            Minutes = 1
        else:
            Minutes=0


        #
        # Days= int(time_list[time_list.index('Days')-1]) if 'Days' in time_list else 0
        #
        # Hours= int(time_list[time_list.index('Hours')-1]) if 'Hours' in time_list or 'Hour' in time_list else 0
        # Minutes= int(time_list[time_list.index('Minutes')-1]) if 'Minutes' in time_list or 'Minute' in time_list else 0

        return Days * 24 * 60 * 60 + Hours * 60 * 60 + Minutes * 60 + time.time()








timer=TimeStamp()