# cwb-cache
抓取中央氣象局開放資料

[資料使用說明](http://opendata.cwb.gov.tw/usages)

## RESTful API document

[中央氣象局氣象資料開放平臺 – 資料擷取使用說明(pdf)](http://opendata.cwb.gov.tw/opendatadoc/CWB_Opendata_API_V1.1.pdf)

### 目前已開放資料擷取之氣象資料

項次 資料集名稱 資料集編號 資料項編號

1. 一般天氣預報-今明36小時天氣預報 F-C0032 F-C0032-001

* 第一級行政區：直轄市、省

* 第二級行政區：縣、市

2. 鄉鎮天氣預報-單一鄉鎮市區預報資料 F-D0047 F-D0047-001 ~ F-D0047-091

* 第三級行政區：鄉、鎮、縣轄市、區

3. 鄉鎮天氣預報-全臺灣各鄉鎮市區預報資料 F-D0047 F-D0047-093

4. 即時海況-潮位-沿岸潮位站監測資料 O-A0017 O-A0017-001

5. 即時海況-海象海溫-浮標站監測資料 O-A0018 O-A0018-001

6. 即時海況-海溫-浮標站與沿岸潮位站監測資料 O-A0019 O-A0019-001

7. 潮汐預報-未來 1 個月潮汐預報 F-A0021 F-A0021-001

僅有 1. 目前實作中

### endpoint

```
http://opendata.cwb.gov.tw/api/v1/rest/datastore/{dataid}
```
