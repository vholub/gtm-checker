import json
import streamlit as st
import plotly.express as px
import pandas as pd

# Nastavení stránky do wide režimu
st.set_page_config(layout="wide")

# Uživatel nahraje JSON soubor
uploaded_file = st.file_uploader("Nahraj JSON soubor", type="json")

if uploaded_file is not None:
    # Načteme data z nahraného souboru
    data = json.load(uploaded_file)

    # Zkusíme nejdříve získat container ID z domainDetails
    container_ids = data.get("data", {}).get("domainDetails", {}).get("containers", [])
    # Pokud není, extrahujeme container ID z detailů každého containeru
    if not container_ids:
        container_ids = [
            c.get("publicId")
            for c in data.get("data", {}).get("containers", [])
            if c.get("publicId")
        ]

    if not container_ids:
        st.error("Nebyl nalezen žádný container v nahraném souboru.")
        st.stop()

    # Uživatel vybere container, se kterým chce pracovat
    container_id = st.selectbox("Vyber container", container_ids)

    # Vyhledáme container v datové struktuře
    containers = data.get("data", {}).get("containers", [])
    target_container = next(
        (c for c in containers if c.get("publicId") == container_id), None
    )

    if not target_container:
        st.error(f"Container {container_id} nebyl nalezen v nahraném souboru.")
        st.stop()

    # Načteme události z vybraného containeru, nejstarší jako první
    events = target_container.get("messages", [])[::-1]
    num_events = len(events)
    if not events:
        st.error("Nebyla nalezena žádná událost v tomto containeru.")
        st.stop()

    indices = list(range(1, num_events + 1))
    titles = [event.get("title", "No Title") for event in events]
    unique_ids = [event.get("gtm.uniqueEventId", "N/A") for event in events]
    df = pd.DataFrame({"Event Order": indices, "Title": titles, "Event ID": unique_ids})

    view_option = st.sidebar.radio(
        "Vyber zobrazení", ("Vývoj datové vrstvy", "Výpis událostí")
    )

    if view_option == "Vývoj datové vrstvy":
        st.title("Interaktivní timeline událostí a datové vrstvy")
        df["dummy"] = 0
        fig = px.scatter(
            df,
            x="Event Order",
            y="dummy",
            hover_data=["Title", "Event ID"],
            title="Event Timeline",
            labels={"dummy": ""},
        )
        fig.update_yaxes(visible=False)
        fig.update_traces(marker=dict(size=10, color="RoyalBlue"))
        st.plotly_chart(fig, use_container_width=True)

        st.header("Srovnání událostí")
        num_columns = st.number_input(
            "Počet sloupců pro srovnání", min_value=1, max_value=5, value=3, step=1
        )
        cols = st.columns([1] * num_columns)
        for idx, col in enumerate(cols):
            with col:
                event_index = st.selectbox(
                    f"Vyber událost {idx + 1}",
                    options=indices,
                    key=f"event{idx + 1}",
                    format_func=lambda i: f"Událost {i}: {titles[i-1]}",
                )
                event = events[event_index - 1]
                st.subheader(
                    f"Detaily události {event_index}: {titles[event_index - 1]}"
                )
                st.json(event.get("message", {}))
    else:
        st.title("Výpis událostí")
        dl_filtered = df[["Event Order", "Title"]]
        st.dataframe(dl_filtered)

        selected_event = st.selectbox(
            "Vyber událost pro zobrazení detailů",
            options=indices,
            format_func=lambda i: f"Událost {i}: {titles[i-1]}",
        )
        event = events[selected_event - 1]
        st.subheader(f"Detaily události {selected_event}: {titles[selected_event - 1]}")
        st.json(event.get("message", {}))
else:
    st.info("Nahraj JSON soubor pro pokračování.")
