#################### GÖREV 1 - VERİYİ ANLAMA VE HAZIRLAMA ####################

import datetime as dt
import pandas as pd

#pd.set_option('display.max_columns', None)
#pd.set_option('display.max_rows', None)
#pd.set_option('display.float_format', lambda x: '%.5f' % x)

# 1.1 - Online Retail 2 excelindeki 2010-2011 verisini okuyunuz ve oluşturduğunuz
# dataframe'in kopyasını oluşturunuz.
data = pd.read_excel('online_retail_II.xlsx', sheet_name='Year 2010-2011')
data.info()
df = data.copy()

# 1.2 - Veri setinin betimsel istatistiklerini inceleyiniz.
df.describe([0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]).T

# 1.3 - Veri setinde eksik gözlem var mı? Varsa hangi değişkende kaç tane eksik gözlem vardır?
total = df.isnull().sum().sort_values(ascending = False)
percent = (df.isnull().sum() / df.isnull().count()).sort_values(ascending=False)
missing_data = pd.concat([total, percent], axis = 1, keys = ['total_null', 'percent_null'])
missing_data.head()

# 1.4 - Eksik gözlemleri veri setinden çıkartınız. Çıkarma işleminde inplace=True parametresini kullanınız.
df.dropna(inplace=True)

df['Customer ID'] = df['Customer ID'].astype(int)

# 1.5 - Eşsiz ürün sayısı kaçtır?
df['Description'].unique()
df['Description'].nunique()

# 1.6 - Hangi üründen kaçar tane vardır?
df['Description'].value_counts()

# 1.7 - En çok sipariş verilen 5 ürünü çoktan aza doğru sıralayınız.
df.groupby('Description').agg({'Quantity': 'sum'}).sort_values('Quantity', ascending=False).head()

# 1.8 -Faturalardaki 'C' iptal edilen işlemleri göstermektedir. İptal edilen işlemleri veri setinden çıkartınız.
df = df[~df['Invoice'].str.contains('C', na=False)]

# 1.9 - Fatura başına elde edilen toplam kazancı ifade eden 'TotalPrice' adında bir değişken oluşturunuz.
df['TotalPrice'] = df['Quantity'] * df['Price']


#################### GÖREV 2 - RFM METRİKLERİNDEN HESAPLANMASI ####################

# 2.1 - Recency, Frequency ve Monetary tanımlarını yapınız.
# Recency: Müşterinin son alışverişinin üzerinden geçen süredir.
# Frequency: Müşterinin şu ana kadar kaç kez alışveriş yaptığını ifade eder.
# Monetary: Müşterinin parasal değeridir.

# 2.2 - Müşteri özelinde Recency, Frequency ve Monetary metriklerini groupby, agg ve lambda ile
# hesaplayınız.

# 2.3 - Hesapladığınız metrikleri rfm isimli bir değişkene atayınız.

# 2.4 - Oluşturduğunuz metriklerin isimlerini recency, frequency ve monetary olarak değiştiriniz.

# Elimizdeki veri setindeki en son faturalama, alışveriş tarihidir.
df['InvoiceDate'].max() #2011-12-09

# Elde edilen tarihin üzerine saat farkları nedeniyle (?) 2 gün ekledik.
today_date = dt.datetime(2011, 12, 11)

rfm = df.groupby('Customer ID').agg({'InvoiceDate': lambda InvoiceDate: (today_date - InvoiceDate.max()).days,
                                     'Invoice': lambda Invoice: Invoice.nunique(),
                                     'TotalPrice': lambda TotalPrice: TotalPrice.sum()})

# InvoiceDate bizim için recency, Invoice-frequency, TotalPrice-Monetary şeklinde adlandırılırsa daha anlamlı olacaktır.
rfm.columns = ['recency', 'frequency', 'monetary']

# Parasal değeri 0'dan küçük olan müşterileri dikkate almıyoruz.
rfm = rfm[rfm['monetary'] > 0]
rfm.head()


#################### GÖREV 3 - RFM SKORLARININ OLUŞTURULMASI VE TEK BİR DEĞİŞKENE ÇEVRİLMESİ ####################

# 3.1 - Recency, Frequency ve Monetary metriklerini qcut yardımı ile 1-5 arasında skorlara çeviriniz.
# 3.2 - Bu skorları recency_score, frequecny_score ve monetary_score olarak kaydediniz.

# Recency Score
# Müşterilerin bizden yakın tarihte alışveriş yapmasını dileriz. Qcut fonksiyonu elimizdeki değerleri büyükten küçüğe sıralar.
# Etiketlemeyi bu şekilde yapma sebebim: recency=1 demek 1 gün önce alışveriş yapıldı demektir. Düşüğe büyük puan verecek şekilde bir ayarlama söz konusu.
rfm['recency_score'] = pd.qcut(rfm['recency'], 5, labels=[5, 4, 3, 2, 1])
rfm.sort_values('recency').head()

# Frequency Score
# Burada ise büyük değere 5 puan veriyoruz.
rfm['frequency_score'] = pd.qcut(rfm['frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5])
rfm.sort_values('frequency_score').head()

# Monetary Score
# Yine büyük değere 5 puan veriyoruz.
rfm['monetary_score'] = pd.qcut(rfm['monetary'], 5, labels=[1, 2, 3, 4, 5])

# 3.3 - Oluşan 2 farklı değişkenin değerini tek bir değişken olarak ifade ediniz ve RFM_SCORE olarak kaydediniz.

# RFM skoruna Monetary değerini dahil etmiyoruz.
rfm['RFM_SCORE'] = (rfm['recency_score'].astype(str) +
                    rfm['frequency_score'].astype(str))


#################### GÖREV 4 - RFM SKORLARININ SEGMENT OLARAK TANIMLANMASI ####################

# 4.1 - Oluşturulan RFM skorlarının daha açıklanabilir olması için segment tanımlamaları yapınız.
# 4.1.1 - seg_map yardımı ile skorları segmentlere çeviriniz.

# Regex. R'de 1 ya da 2, F'de 1 ya da 2 görürsen şunu yaz şeklinde.
seg_map = {
        r'[1-2][1-2]': 'hibernating',
        r'[1-2][3-4]': 'at_risk',
        r'[1-2]5': 'cant_loose',
        r'3[1-2]': 'about_to_sleep',
        r'33': 'need_attention',
        r'[3-4][4-5]': 'loyal_customers',
        r'41': 'promising',
        r'51': 'new_customers',
        r'[4-5][2-3]': 'potential_loyalists',
        r'5[4-5]': 'champions'
    }

rfm['segment'] = rfm['RFM_SCORE'].replace(seg_map, regex=True)
rfm = rfm[['recency', 'frequency', 'monetary', 'segment']]


#################### GÖREV 5 - AKSİYON ZAMANI! ####################

# 5.1 - Önemli bulduğunuz 3 segmenti seçiniz.
segment_total=rfm.groupby('segment').mean().reset_index()
rfm['segment'].value_counts()


"""
POTENTIAL ROYALIST
Sık alışveriş yaptığını söyleyebileceğimiz bu grupta 484 müşterimiz bulunuyor. Ancak satın aldıkları ürün sayısını artırmak
üzerine çalışmamız gerekiyor. Kişiye özel süreli kampanyalar ile satın alma alışkanlıkları değiştirilebilir gibi geliyor.

CHAMPIONS
Sık sık ve çok alışveriş yapan bu segmentteki müşteriler toplamda 633 kişidir.
Elimizde tutmamız gerektiğine inanıyorum.

NEED ATTENTION
İlgilenirsek olumlu, ilgilenmezsek olumsuz yönde ivme kazanacak bir segment olması nedeniyle biz ilgilenmeyi seçelim :)
187 müşterimizden bir kısmını 52 günden daha sık alışveriş yapmaya teşvik edersek ortalama kazancımız 897.62 brden çok daha fazla olacaktır.

"""

# 5.2 - "Loyal customers" sınıfına ait customer ID'leri seçerek Excel çıktısını alınız.
rfm[rfm['segment'] == 'loyal_customers'].head()
new_df = pd.DataFrame()
new_df["Loyal_Customers_ID"] = rfm[rfm["segment"] == "loyal_customers"].index
new_df.to_csv("Loyal_Customers.csv")