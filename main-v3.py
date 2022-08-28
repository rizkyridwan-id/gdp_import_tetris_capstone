from json import tool
import streamlit as st
from PIL import Image
import pycountry
import pandas as pd
import altair as alt
import seaborn as sns
import matplotlib.pyplot as plt
import re
from numerize import numerize

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
st.set_page_config(layout="wide")
padding_top = 1

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
banner_image = Image.open("assets/images/centered_banner_wide.jpg")
st.image(banner_image)
st.title("Angka PDB Indonesia Tinggi, Mengapa Angka Impor Semakin Meningkat?")
st.caption("Diposting pada 3 Agustus, 2022, at 11:32 p.m. WIB")
st.markdown("<div style='position: absolute; color: #84858C; font-size: 0.9rem'>oleh Muhammad Rizky Ridwan Fauzi</div>", unsafe_allow_html=True)
# endregion

# region (quote)
st.markdown("<center style='padding: 2.8rem 2rem; font-size: 1.2rem;'>“Indonesia memiliki penduduk 262 juta jiwa membutuhkan pangan yang amat banyak.  Ketergantungan pada impor pangan beresiko besar terhadap ketahanan pangan dan akan mengancam kedaulatan kebijakan pangan NKRI” — Prima Gandhi, SP, MSi</center>", unsafe_allow_html=True)
# endregion

# region (body1: top 20)
# Processing Top 20 Chart
def generateGDP(chosen_year):
    df_gdp = pd.read_csv("data_source/gdp_dollar.csv")
    df_gdp = df_gdp[df_gdp['Country Code'].isin(country_codes)].reset_index(drop=True)

    df_gdp_top20 = df_gdp.sort_values(by=chosen_year, ascending=False).reset_index(drop=True).head(20)
    df_gdp_top20 = df_gdp_top20.loc[:, ["Country Name", chosen_year]]
    df_gdp_top20[chosen_year] = df_gdp_top20[chosen_year]
    df_gdp_top20.rename(columns = {chosen_year: "US$"}, inplace=True)
    return df_gdp_top20

def makeG20Chart(df_gdp):
    return alt.Chart(df_gdp).mark_bar().encode(
        y=alt.Y('Country Name:N', sort="-x"),
        x=alt.X('US$', axis=alt.Axis(format='$.2s')),
        color=alt.condition(
            alt.datum['Country Name'] == "Indonesia",  # If the year is 1810 this test returns True,
            alt.value('#F25757'),     # which sets the bar orange.
            alt.value('#465A65')   # And if it's not true it sets the bar steelblue.
        ),
        tooltip=[
            alt.Tooltip("Country Name", title="Country Name"),
            alt.Tooltip("US$", title="US$", format="$.3s"),
        ],
    )

def findGDPIDValue(df_gdp):
    return df_gdp.query('`Country Name` == "Indonesia"').reset_index(drop=True)['US$'][0]

def findGDPIDIndex(df_gdp):
    return df_gdp.query('`Country Name` == "Indonesia"').index[0]

if 'chosen_year' not in st.session_state:
    st.session_state.chosen_year = "2021"

col_lead1, col_lead2 = st.columns([6,1])

with col_lead2:
    select_box_value = st.selectbox(
     'Pilih Tahun:',
     ('2021', '2020', '2019', "2018", "2017", "2016", "2015", "2014", "2013", "2012", "2011", "2010"))
    if select_box_value:
        st.session_state.chosen_year = select_box_value
    
    pdb_id_value = findGDPIDValue(generateGDP(select_box_value))
    pdb_id_value_previous = findGDPIDValue(generateGDP(str(int(select_box_value) - 1)))
    id_index = findGDPIDIndex(generateGDP(select_box_value))
    id_index_previous = findGDPIDIndex(generateGDP(str(int(select_box_value) - 1)))

    st.metric("Nilai PDB Indonesia", value=numerize.numerize(int(pdb_id_value)), delta=numerize.numerize(int(pdb_id_value) - int(pdb_id_value_previous)))
    st.metric("Posisi Indonesia G20", value="{}/20".format(id_index + 1), delta=str( id_index_previous - id_index))

with col_lead1:
    st.altair_chart(makeG20Chart(generateGDP(select_box_value)), use_container_width=True)
# endregion

# region (body2: PDB Summarize)
def makePDBComparisonChart(df_gdp, year):
    df_gdp_max = df_gdp[year].max()

    return alt.Chart(df_gdp).mark_bar().encode(
        y=alt.Y('{}:Q'.format(year), title="Miliar RP", axis=alt.Axis(format='.2s')),
        x=alt.X('lapangan_usaha',title="Lapangan Usaha", axis=alt.Axis(labelAngle=-45)),
        tooltip=[
            alt.Tooltip("lapangan_usaha", title="Lapangan Usaha"),
            alt.Tooltip(year, title="Nilai (Miliar Rp)", format=".3s"),
        ],
        color=alt.condition(
            alt.datum[year] == df_gdp_max,  # If the year is 1810 this test returns True,
            alt.value('#F25757'),     # which sets the bar orange.
            alt.value('#465A65')   # And if it's not true it sets the bar steelblue.
        ),
    ).properties(height=400)

if 'chosen_year_pdb' not in st.session_state:
    st.session_state.chosen_year_pdb = "2021"

df_pdb_lapangan_usaha = pd.read_csv("./data_source/pdb_lapangan_usaha.csv")

for column in df_pdb_lapangan_usaha.columns[1:]:
    df_pdb_lapangan_usaha[column] = df_pdb_lapangan_usaha[column].astype('int64')

st.subheader("Perkembangan Nilai PDB")
st.caption("Berdasarkan harga konstan 2010")
col_body2_1, col_body2_2 = st.columns([5, 6])
with col_body2_1:
    chosen_year_pdb_selectbox = st.selectbox("Tahun", ('2021', '2020', '2019', "2018", "2017", "2016", "2015", "2014", "2013", "2012", "2011", "2010"))
    st.session_state.chosen_year_pdb = chosen_year_pdb_selectbox
    st.write("Indonesia Berada di posisi 20 Besar atau G20 dalam peringkat PDB Dunia. Untuk mengetahui Nilai PDB dalam berbagai lapangan usaha dapat dilihat dalam diagram disamping!")
    with st.expander("3 Lapangan Usaha Terbesar"):
        df_pdb_usaha_sorted = df_pdb_lapangan_usaha.sort_values(by=chosen_year_pdb_selectbox, ascending=False)
        series_usaha_pdb = df_pdb_usaha_sorted['lapangan_usaha'][:3]
        values_usaha_pdb = df_pdb_usaha_sorted[chosen_year_pdb_selectbox]

        for i,usaha in enumerate(series_usaha_pdb):
            st.write("({}) {} ({})".format(i + 1, usaha, numerize.numerize(int(values_usaha_pdb[values_usaha_pdb.index[i]]))))
     
with col_body2_2:
    st.altair_chart(makePDBComparisonChart(df_pdb_lapangan_usaha, st.session_state.chosen_year_pdb), use_container_width=True)

# endregion

# region (body3: Impor Summarize)
def makeImporBarChart(df_impor, year):
    df_impor_max = df_impor[year].max()

    return alt.Chart(df_impor).mark_bar().encode(
        y=alt.Y('{}:Q'.format(year), title="Volume (Ton)", axis=alt.Axis(format='.2s')),
        x=alt.X('golongan_sitc',title="Kategori SITC", axis=alt.Axis(labelAngle=-45)),
        tooltip=[
            alt.Tooltip("golongan_sitc", title="Kategori SITC"),
            alt.Tooltip(year, title="Volume (Ton)", format=".3s"),
        ],
        color=alt.condition(
            alt.datum[year] == df_impor_max,  # If the year is 1810 this test returns True,
            alt.value('#F25757'),     # which sets the bar orange.
            alt.value('#465A65')   # And if it's not true it sets the bar steelblue.
        ),
    ).properties(height=400)

st.subheader("Perkembangan Nilai Impor")
st.caption("Berdasarkan Volume Impor")

if 'chosen_year_impor' not in st.session_state:
    st.session_state.chosen_year_impor = "2021"

df_impor_sitc = pd.read_csv("./data_source/impor_ton.csv")

for column in df_impor_sitc.columns[1:]:
    df_impor_sitc[column] = df_impor_sitc[column].astype('int64')

col_body3_1, col_body3_2 = st.columns([6, 5])
with col_body3_2:
    chosen_year_impor_selectbox = st.selectbox("Tahun Impor", ('2021', '2020', '2019', "2018", "2017", "2016", "2015", "2014", "2013", "2012", "2011", "2010"))
    st.session_state.chosen_year_impor = chosen_year_impor_selectbox
    st.write("Nilai Impor Indonesia tiap tahun juga mengalami peningkatan untuk memenuhi kebutuhan Indonesia.")
    with st.expander("3 Nilai Impor Terbesar"):
        df_impor_sorted = df_impor_sitc.sort_values(by=chosen_year_impor_selectbox, ascending=False)
        series_impor_pdb = df_impor_sorted['golongan_sitc'][:3]
        values_impor_pdb = df_impor_sorted[chosen_year_impor_selectbox]

        for i,impor_category in enumerate(series_impor_pdb):
            st.write("({}) {} ({})".format(i + 1, impor_category, numerize.numerize(int(values_impor_pdb[values_impor_pdb.index[i]]))))
     
with col_body3_1:
    st.altair_chart(makeImporBarChart(df_impor_sitc, st.session_state.chosen_year_impor), use_container_width=True)

# endregion

# region (body3: Revision (Laju Impor dan Laju PDB))
st.write("Melihat 3 Nilai Terbesar PDB diatas, lantas bagaimana laju nilai PDB dan Impor Indonesia? Apakah dengan Meningkatnya PDB laju Impor Juga Ikut Meningkat?")
st.subheader("Perbandingan Laju PDB & Import")
st.caption("Berdasarkan data 10 Tahun terakhir (2010 - 2021)")

# data processing
df_pdb = pd.read_csv("./data_source/pdb_lapangan_usaha.csv")
df_impor = pd.read_csv("./data_source/impor_ton.csv")

def make_layered_chart_impor(data):
    hover = alt.selection_single(
        fields=["index"],
        nearest=True,
        on="mouseover",
        empty="none",
    )

    lines = (
        alt.Chart(data, title="Angka Impor")
        .mark_line()
        .encode(
            x=alt.X('index', axis=alt.Axis(title='Year', labelAngle=-45)),
            y=alt.Y('value:Q', axis=alt.Axis(title='Volume (Ton)', format='.2s')),
            color="golongan_sitc",
        )
        .properties(
            width=525
        )
    )

    # Draw points on the line, and highlight based on selection
    points = lines.transform_filter(hover).mark_circle(size=75)

    # Draw a rule at the location of the selection
    tooltips = (
        alt.Chart(data)
        .mark_rule()
        .encode(
            x="index",
            y="value",
            opacity=alt.condition(hover, alt.value(0.3), alt.value(0)),
            tooltip=[
                alt.Tooltip("index", title="Tahun"),
                alt.Tooltip("value", title="Volume(Ton)", format='.2s'),
                alt.Tooltip("golongan_sitc", title="Golongan SITC"),
            ],
        )
        .add_selection(hover)
    )
    return (lines + points + tooltips).interactive()


def find_pdb_by_usaha(usaha):
    df_pdb_filtered = df_pdb.query('lapangan_usaha == "{}"'.format(usaha)).reset_index(drop=True)
    return pd.DataFrame({
        "y": df_pdb_filtered.iloc[0, 1:],
        "x": df_pdb_filtered.columns[1:]
    })

def find_impor_by_kategori(kategori):
    df_impor_filtered = df_impor.query('golongan_sitc == "{}"'.format(kategori)).reset_index(drop=True)
    return pd.DataFrame({
        "y": df_impor_filtered.iloc[0, 1:],
        "x": df_impor_filtered.columns[1:]
    })

def find_impor_v2_by_kategori(kategori):
    df_impor_filtered = df_impor.query('golongan_sitc in {}'.format(list(kategori))).reset_index(drop=True)
    return df_impor_filtered.set_index('golongan_sitc').T.reset_index(level=0)

def build_line_chart(df, impor = False):
    color_string = '#F25757' if impor else '#465A65'
    lines = alt.Chart(df,  title="Angka PDB").mark_line().encode(
       x=alt.X('x', axis=alt.Axis(title='Year', labelAngle=-45)),
       y=alt.Y('y:Q',axis=alt.Axis(title='Miliar RP', format='.2s')),
       color = alt.value(color_string),
    #    tooltip=[
    #             alt.Tooltip("x", title="Year"),
    #             alt.Tooltip("y", title="Miliar RP", format='.2s'),
    #     ],
     )
    hover = alt.selection_single(
        fields=["x"],
        nearest=True,
        on="mouseover",
        empty="none"
    )

    points = lines.transform_filter(hover).mark_circle(size=75)

    tooltips = (
        alt.Chart(df)
        .mark_rule()
        .encode(
            x='x',
            y='y',
            opacity = alt.condition(hover, alt.value(0.3), alt.value(0)),
            tooltip=[
                alt.Tooltip("x", title="Year"),
                alt.Tooltip("y", title="Miliar RP", format='.3s'),
            ],
        )
        .add_selection(hover)
    )

    return (lines + points + tooltips).interactive()

lapangan_usaha_selection = df_pdb['lapangan_usaha']
lapangan_usaha_selected = st.selectbox("Sektor PDB", lapangan_usaha_selection)
col_body3_1, col_body3_2 = st.columns(2)
with col_body3_1:
    pdb_by_usaha_processed = find_pdb_by_usaha(lapangan_usaha_selected)
    st.altair_chart(build_line_chart(pdb_by_usaha_processed).interactive(), True)
with col_body3_2:

    # processing data
    impor_transposed = df_impor.set_index("golongan_sitc").transpose()
    pdb_transposed = df_pdb.set_index("lapangan_usaha").transpose()
        
    df_merged = pdb_transposed.join(impor_transposed)
    # print(df_merged.info())
    series_selected = df_merged.corr()
    series_filtered = series_selected[lapangan_usaha_selected].filter(items=df_impor["golongan_sitc"])
    series_column = series_filtered[series_filtered > 0.71].index

    # kategori_sitc_selection = df_impor["golongan_sitc"]
    # kategori_sitc_selected = st.selectbox("Sektor Impor", kategori_sitc_selection)
    impor_by_usaha_kategori = find_impor_v2_by_kategori(series_column)
    df_impor_melted = pd.melt(impor_by_usaha_kategori.reset_index(), id_vars='index',value_vars=series_column)

    # print(df_impor_melted)
    chart = make_layered_chart_impor(df_impor_melted)
    st.altair_chart(
        chart.interactive(),
        use_container_width=True
    )
    # st.altair_chart(build_line_chart(impor_by_usaha_kategori, True), True)

st.write("Berdasarkan kedua diagram diatas dapat disimpulkan bahwa laju 1 nilai PDB berkaitan dengan laju beberapa nilai impor. Hal ini bisa terjadi karena untuk memenuhi komponen yang dibutuhkan produsen dari berbagai lapangan usaha agar dapat menjalankan produksinya.")
# endregion

# region (body4: Revision (Korelasi Dari Berbagai Variable))

# if 'lapangan_usaha_corr_selected' not in st.session_state:
#     st.session_state.lapangan_usaha_corr_selected = ["A. Pertanian, Kehutanan, dan Perikanan", "C. Industri Pengolahan", "F. Perdagangan Besar dan Eceran"]

# if 'kategori_sitc_corr_selected' not in st.session_state:
#     st.session_state.kategori_sitc_corr_selected = kategori_sitc_selection[:9]

# st.subheader("Uji Korelasi")
# st.caption("Range Data (2010-2021)")
# body4_col1, body4_col2 = st.columns([3,6])
# with body4_col1:
#     lapangan_usaha_corr_selectbox = st.multiselect("Sektor PDB", lapangan_usaha_selection)
#     # st.session_state.lapangan_usaha_corr_selected = st.multiselect("Sektor PDB", lapangan_usaha_selection, default=st.session_state.lapangan_usaha_corr_selected)
#     st.session_state.lapangan_usaha_corr_selected = lapangan_usaha_corr_selectbox
#     print(st.session_state.lapangan_usaha_corr_selected)
    
#     kategori_sitc_corr_selectbox = st.multiselect("Sektor Impor", kategori_sitc_selection)
#     # st.session_state.kategori_sitc_corr_selected = st.multiselect("Sektor Impor", kategori_sitc_selection, default=st.session_state.kategori_sitc_corr_selected)
#     st.session_state.kategori_sitc_corr_selected = kategori_sitc_corr_selectbox

# with body4_col2:
    
#     if len(st.session_state.lapangan_usaha_corr_selected) == 0 and len(st.session_state.kategori_sitc_corr_selected) == 0:
#         st.session_state.lapangan_usaha_corr_selected = ["A. Pertanian, Kehutanan, dan Perikanan", "C. Industri Pengolahan", "F. Perdagangan Besar dan Eceran"]
#         st.session_state.kategori_sitc_corr_selected = kategori_sitc_selection[:9]

#     impor_transposed = df_impor.query('golongan_sitc in @st.session_state.kategori_sitc_corr_selected').set_index("golongan_sitc").transpose()
#     pdb_transposed = df_pdb.query('lapangan_usaha in @st.session_state.lapangan_usaha_corr_selected').set_index("lapangan_usaha").transpose()
    
#     df_merged = pdb_transposed.join(impor_transposed)
#     df_merged.columns = df_merged.columns.str.replace(r'(?<=[A-Z0-9]\.).+', '')

#     sns.set(font_scale=0.5)
#     fig, ax = plt.subplots()

#     sns.heatmap(
#         df_merged.corr(method="pearson"),
#         vmin=df_merged.corr().values.min(), vmax=1, square=True, cmap="YlGnBu", linewidths=0.1, annot=True, annot_kws={"fontsize":4.5}
#     )

#     st.pyplot(fig)
# endregion

# with st.expander("Heatmap Legend:"):
#     cc_1, cc_2 = st.columns(2)
#     with cc_1:
#         st.subheader("Sektor PDB")
#         for key in list(lapangan_usaha_selection):
#             st.write(key)
        
#     with cc_2:
#         st.subheader("Sektor Impor")
#         for key in list(kategori_sitc_selection):
#             st.write(key)

        
# st.write("Berdasarkan uji korelasi diatas, diketahui bahwa 1 sektor nilai PDB berkorelasi dengan berbagai sektor impor. Hal ini terjadi karena satu sektor nilai PDB memiliki kaitan yang cukup erat dengan nilai impor dari berbagai sektor.")

st.subheader("Sumber")
st.write("1. BPS (Nilai Impor & PDB)")
st.write("2. Data World Bank (GDP World)")
