import streamlit as st
from PIL import Image
import pycountry
import pandas as pd
import altair as alt
import seaborn as sns
import matplotlib.pyplot as plt
import re

country_codes = list(map(lambda x: x.alpha_3, pycountry.countries))

# region Useful Function 
def select_indonesia(csv, start, end):
  range_tahun_index = list(range(45 + start, 66 - end))
  country_name_index = [0]

  col_selected = csv.iloc[:, country_name_index + range_tahun_index]
  col_selected = col_selected.query('`Country Name` == "Indonesia"')
  col_selected.reset_index(drop=True, inplace=True)
  return col_selected

def transform_table(csv, key):
  year_column = csv.columns[1:]
  value = csv.iloc[0, 1:]
  dict_structure = {"year": year_column}
  dict_structure[key] = value

  df_selected = pd.DataFrame(dict_structure).reset_index(drop=True)
  return df_selected

# base chart
def get_chart(data):
    hover = alt.selection_single(
        fields=["year"],
        nearest=True,
        on="mouseover",
        empty="none",
    )

    lines = (
        alt.Chart(data, title="Angka Sektor Penopang PDB")
        .mark_line()
        .encode(
            x="year",
            y="value",
            color="variable",
        )
    )

    # Draw points on the line, and highlight based on selection
    points = lines.transform_filter(hover).mark_circle(size=65)

    # Draw a rule at the location of the selection
    tooltips = (
        alt.Chart(data)
        .mark_rule()
        .encode(
            x="year",
            y="value",
            opacity=alt.condition(hover, alt.value(0.3), alt.value(0)),
            tooltip=[
                alt.Tooltip("year", title="Year"),
                alt.Tooltip("value", title="\% Based of PDB"),
            ],
        )
        .add_selection(hover)
    )
    return (lines + points + tooltips).interactive()


# endregion

# region (page config)
padding_top = 0

st.markdown(f"""
    <style>
        .main .block-container{{
            padding-top: {padding_top}rem !important;
        }}
    </style>""",
    unsafe_allow_html=True,
)
# endregion

# region (Header)
banner_image = Image.open("assets/images/centered_banner_v2.jpg")
st.image(banner_image)
st.title("Angka PDB Indonesia Tinggi, Mengapa Angka Impor Semakin Meningkat?")
st.caption("Diposting pada 3 Agustus, 2022, at 11:32 p.m. WIB")
st.markdown("<div style='position: absolute; color: #84858C; font-size: 0.9rem'>oleh Muhammad Rizky Ridwan Fauzi</div>", unsafe_allow_html=True)
# endregion

# region (quote)
st.markdown("<center style='padding: 2.8rem 2rem; font-size: 1.2rem;'>“Indonesia memiliki penduduk 262 juta jiwa membutuhkan pangan yang amat banyak.  Ketergantungan pada impor pangan beresiko besar terhadap ketahanan pangan dan akan mengancam kedaulatan kebijakan pangan NKRI” — Prima Gandhi, SP, MSi</center>", unsafe_allow_html=True)
# endregion

# region (body1: top 20)

st.write("Perkembangan perekonomian di Indonesia telah mengalami banyak peningkatan dari tahun ketahun. Peningkatan PDB (Produk Domestik Bruto) yang semakin signifikan telah membuat Indonesia menempati posisi 16 dalam sensus PDB tahun 2021 dengan angka PDB sebesar 1.2T USD")

# Processing Top 20 Chart
df_gdp = pd.read_csv("data_source/gdp_dollar.csv")
df_gdp = df_gdp[df_gdp['Country Code'].isin(country_codes)].reset_index(drop=True)

chosen_year = st.select_slider(
     'Pilih tahun untuk melihat PDB 5 tahun terakhir!',
     options=["2017", "2018", "2019", "2020", "2021"], value=("2021"))
st.write('Tahun dipilih:', chosen_year)
df_gdp_top20 = df_gdp.sort_values(by=chosen_year, ascending=False).reset_index(drop=True).head(20)
df_gdp_top20 = df_gdp_top20.loc[:, ["Country Name", chosen_year]]
df_gdp_top20[chosen_year] = df_gdp_top20[chosen_year].astype("int64")
df_gdp_top20.rename(columns = {chosen_year: "US$"}, inplace=True)

chart = alt.Chart(df_gdp_top20).mark_bar().encode(
    y=alt.Y('Country Name:N', sort="-x"),
    x=alt.X('US$', axis=alt.Axis(format='$.2s')),
    color=alt.condition(
        alt.datum['Country Name'] == "Indonesia",  # If the year is 1810 this test returns True,
        alt.value('#F25757'),     # which sets the bar orange.
        alt.value('#465A65')   # And if it's not true it sets the bar steelblue.
    ),
    tooltip=[
        alt.Tooltip("Country Name", title="Country Name"),
        alt.Tooltip("US$", title="US$", format="$.2s"),
    ],
)
st.altair_chart(chart, use_container_width=True)



# endregion

# region (body2: Angka Penopang )
st.write("Seperti yang kita ketahui bahwa angka PDB itu dihitung dari beberapa sektor. Angka Industri masih menjadi penopang terbesar dalam PDB Nasional setiap tahunnya, kemudian diikutinya dengan angka agrikultur sehingga mendapatkan angka PDB akhir.")

# Data Processing
csv_agri = pd.read_csv("data_source/AGRI_GDP_VALUE.csv")
csv_gdp = pd.read_csv("data_source/GDP_GROWTH.csv")
csv_industry = pd.read_csv("data_source/INDUSTRY_VALUE.csv")
csv_import_goods = pd.read_csv("data_source/IMPORT_GOOD_VALUE.csv")

start_year, end_year = st.select_slider(
     'Geser Slider dibawah untuk melihat periode rentang tahun!',
     options=["2001","2002","2003","2004","2005","2006","2007","2008","2009","2010","2011","2012","2013","2014","2015","2016","2017", "2018", "2019", "2020", "2021"], value=("2001", "2021"))
st.write('Rentang Tahun:', start_year, " - ", end_year)

start_year_diff = int(start_year) - 2001
end_year_diff =  2021 - int(end_year)

pd_agri = transform_table(select_indonesia(csv_agri, start_year_diff, end_year_diff), 'agri_value')
pd_gdp = transform_table(select_indonesia(csv_gdp, start_year_diff, end_year_diff), 'gdp_value')
pd_industry = transform_table(select_indonesia(csv_industry, start_year_diff, end_year_diff), 'industry_value')
pd_import_goods = transform_table(select_indonesia(csv_import_goods, start_year_diff, end_year_diff), 'import_goods_value')

pd_merged = pd.merge(pd_agri, pd_gdp, on="year")
pd_merged = pd.merge(pd_merged, pd_industry, on="year")
pd_merged = pd.merge(pd_merged, pd_import_goods, on="year")

dict_type = {
    'agri_value': 'int32',
    'gdp_value': 'int32',
    'import_goods_value': 'int32',
    'industry_value': 'int32',
}

for key in dict_type:
  pd_merged[key] = pd_merged[key].astype(dict_type[key])

var = pd_merged.loc[:, ["year", "agri_value", "industry_value"]]
df2 = pd.melt(var.reset_index(), id_vars='year',value_vars=['agri_value','industry_value'])

chart = get_chart(df2)
st.altair_chart(
    chart.interactive(),
    use_container_width=True
)

st.write("Data di atas menunjukan bahwa nilai industri menjadi penopang angka PDB. Nilai Industri tertinggi terjadi pada tahun 2008 dengan nilai 48\% dari total PDB dan pada tahun 2021 nilai industri naik sebanyak 1\% hingga mencapai nilai 39\% dari PDB. Lantas Mengapa Angka Impor semakin meningkat ?")


pd_agri_corr = transform_table(select_indonesia(csv_agri, 0, 0), 'agri_value')
pd_gdp_corr = transform_table(select_indonesia(csv_gdp, 0, 0), 'gdp_value')
pd_industry_corr = transform_table(select_indonesia(csv_industry, 0, 0), 'industry_value')
pd_import_goods_corr = transform_table(select_indonesia(csv_import_goods, 0, 0), 'import_goods_value')

pd_merged_corr = pd.merge(pd_agri_corr, pd_gdp_corr, on="year")
pd_merged_corr = pd.merge(pd_merged_corr, pd_industry_corr, on="year")
pd_merged_corr = pd.merge(pd_merged_corr, pd_import_goods_corr, on="year")

for key in dict_type:
  pd_merged_corr[key] = pd_merged_corr[key].astype(dict_type[key])

body3_col1, body3_col2 = st.columns(2)
with body3_col1:
    fig, ax = plt.subplots()
    sns.scatterplot(
        pd_merged_corr['industry_value'], pd_merged_corr['import_goods_value']
    )
    st.pyplot(fig)
    
with body3_col2:
    fig, ax = plt.subplots()

    sns.heatmap(
        pd_merged_corr.corr(),
        annot=True
    )

    st.pyplot(fig)

st.write("Dari kedua data diatas, mengindikasikan bahwa nilai industri, dengan nilai impor berkorelasi positif dengan rho sebesar 0.82. Hal ini bisa terjadi karena beberapa faktor mulai dari sektor industri yang membutuhkan fasilitas yang memadai hingga pertumbuhan lahan agrikultur yang semakin berkurang karena adanya pertumbuhan industri yang sangat cepat.")

chosen_year_detail_variable = st.select_slider(
     'Pilih Tahun untuk melihat detail import!',
     options=["Jan - Des (2021)", "Jan (2022)"], value=("Jan (2022)"))

chosen_year_import_filtered = re.search(r"[0-9]{4}", chosen_year_detail_variable)[0]

print(chosen_year_import_filtered)
# Data Processing
df_latest_detail_import = pd.read_csv("data_source/DETAIL_IMPORT_LATEST.csv")
df_latest_detail_import_selected = df_latest_detail_import.query('`tahun` == '+chosen_year_import_filtered).reset_index(drop=True)
df_latest_detail_import_selected.rename(columns = {'value': "Million US$"}, inplace=True)

chart = alt.Chart(df_latest_detail_import_selected).mark_bar().encode(
    y=alt.Y('nama_data:N', sort="-x"),
    x=alt.X('Million US$'),
    
    tooltip=[
        alt.Tooltip("nama_data", title="Komoditas Barang"),
        alt.Tooltip("Million US$", title="Million US$", ),
    ],
)

st.altair_chart(chart, use_container_width=True)

st.write("Data 1 tahun komoditas impor di atas mengindikasikan bahwa angka terbesar impor itu ada pada kategori Mesin / Peralatan mekanis. Kategori Mesin dan Peralatan Mekanis ini memiliki kaitan yang sangat erat dengan nilai industri berdasarkan persentase perkembang PDB")

st.subheader("Sumber")
st.write("1. Katadata (Komoditas Impor Indonesia)")
st.write("2. Data World Bank (GDP Growth, Agriculture Value Based on GDP, Industry Value Based on GDP, Impor Value Based on GDP, World GDP US$)")

st.subheader("Catatan")
st.write("     Dikarenakan keterbatasan data yang dapat diakses oleh penulis. ")
st.write("Maka dari itu, penulis mengharapkan masukkan dari pembaca, agar penulis dapat mengembangkan lebih jauh tentang analisis ini.")
st.markdown("Untuk Saran dan Masukkan dapat dikirimkan ke <a href='mailto:rizkyridwan.id@gmail.com'>Email Saya</a>", unsafe_allow_html=True)
