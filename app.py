import json
import streamlit as st
import plotly.express as px
import pandas as pd
from deepdiff import DeepDiff


def render_diff(diff):
    if not diff:
        st.write("Žádné rozdíly nebyly nalezeny.")
        return

    if "dictionary_item_added" in diff:
        st.markdown("**Přidané klíče:**")
        for item in diff["dictionary_item_added"]:
            st.write(f"- {item}")

    if "dictionary_item_removed" in diff:
        st.markdown("**Odebrané klíče:**")
        for item in diff["dictionary_item_removed"]:
            st.write(f"- {item}")

    if "values_changed" in diff:
        st.markdown("**Změněné hodnoty:**")
        for path, change in diff["values_changed"].items():
            old_val = change["old_value"]
            new_val = change["new_value"]
            st.write(f"- **{path}**")
            st.write(f"  - Původní: {old_val}")
            st.write(f"  - Nová: {new_val}")

    if "iterable_item_added" in diff:
        st.markdown("**Položky přidané do pole/seznamu:**")
        for path, val in diff["iterable_item_added"].items():
            st.write(f"- **{path}**: {val}")

    if "iterable_item_removed" in diff:
        st.markdown("**Položky odebrané z pole/seznamu:**")
        for path, val in diff["iterable_item_removed"].items():
            st.write(f"- **{path}**: {val}")


# Nastaví stránku do wide režimu
st.set_page_config(layout="wide")

# Uživatel nahraje JSON soubor
uploaded_file = st.file_uploader("Nahraj JSON soubor", type="json")

if uploaded_file is not None:
    data = json.load(uploaded_file)

    container_ids = data.get("data", {}).get("domainDetails", {}).get("containers", [])
    if not container_ids:
        container_ids = [
            c.get("publicId")
            for c in data.get("data", {}).get("containers", [])
            if c.get("publicId")
        ]

    if not container_ids:
        st.error("Nebyl nalezen žádný container v nahraném souboru.")
        st.stop()

    container_id = st.selectbox("Vyber container", container_ids)

    containers = data.get("data", {}).get("containers", [])
    target_container = next(
        (c for c in containers if c.get("publicId") == container_id), None
    )

    if not target_container:
        st.error(f"Container {container_id} nebyl nalezen v nahraném souboru.")
        st.stop()

    events = target_container.get("messages", [])[::-1]
    num_events = len(events)
    if not events:
        st.error("Nebyla nalezena žádná událost v tomto containeru.")
        st.stop()

    indices = list(range(1, num_events + 1))
    titles = [event.get("title", "No Title") for event in events]
    unique_ids = [event.get("gtm.uniqueEventId", "N/A") for event in events]

    df = pd.DataFrame({"Event Order": indices, "Title": titles, "Event ID": unique_ids})

    st.title("Interaktivní timeline událostí a DL")

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
            st.subheader(f"Detaily události {event_index}: {titles[event_index - 1]}")
            st.json(event.get("message", {}))

    st.header("Porovnání událostí pomocí DeepDiff")

    diff_event1 = st.selectbox(
        "Vyber první událost pro porovnání",
        options=indices,
        key="diff_event1",
        format_func=lambda i: f"Událost {i}: {titles[i-1]}",
    )
    diff_event2 = st.selectbox(
        "Vyber druhou událost pro porovnání",
        options=indices,
        key="diff_event2",
        format_func=lambda i: f"Událost {i}: {titles[i-1]}",
    )

    if st.button("Porovnat vybrané události"):
        message1 = events[diff_event1 - 1].get("message", {})
        message2 = events[diff_event2 - 1].get("message", {})
        diff = DeepDiff(message1, message2, ignore_order=True)
        st.subheader("Rozdíly mezi událostmi")
        render_diff(diff)

else:
    st.info("Nahraj JSON soubor pro pokračování.")
