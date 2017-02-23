## 声明：
1. 该项目仅作为测试、学习使用，如有侵犯您的权益请联系
 - 邮箱：<calmtmoonlight@aliyun.com>
    
2. 为避免对网站[鱼C工作室](http://fishc.com/)造成一定的压力，请合理设置请求时间、线程以及避开网站访问高峰期。


## 使用：

``` Python

>>>category = FishC()   #保存栏目列表
>>>category.save_db_category()  #保存详细信息
>>>detail = FishC_detail(threadNum=2)
>>>detail.start()
>>>ver = VerifyLink(threadNum=2)#保存验证码--链接
>>>ver.save_verify()
```

######注：
1. 该项目可结合项目[yun](https://github.com/CalmtMoonlight/baidu/tree/master/yun)
使用。





