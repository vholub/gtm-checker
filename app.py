import json
import pathlib
import streamlit as st
import pandas as pd

CONTAINER_ID = "GTM-PPKDLQC3"
DEFAULT_COLUMNS = 5
DEFAULT_EVENTS = [29, 31, 110, 127, 143]
GA4_ECOMMERCE_EVENTS = [
    "view_item",
    "view_cart",
    "add_to_cart",
    "remove_from_cart",
    "begin_checkout",
    "add_shipping_info",
    "add_payment_info",
    "purchase",
    "view_item_list",
    "select_item",
    "view_promotion",
    "select_promotion",
]

st.set_page_config(layout="wide")

data = json.loads(pathlib.Path("tag_futrale-new.json").read_text(encoding="utf-8"))

containers = data.get("data", {}).get("containers", [])
target_container = next(
    (c for c in containers if c.get("publicId") == CONTAINER_ID), None
)

if not target_container:
    st.error(f"Container {CONTAINER_ID} nebyl nalezen.")
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

st.title("Výpis událostí")
df_filtered = df[["Event Order", "Title"]]


def highlight_ecommerce(row):
    if row["Title"] in GA4_ECOMMERCE_EVENTS:
        return ["background-color: #90EE90; color: #000000"] * len(row)
    return [""] * len(row)


styled_df = df_filtered.style.apply(highlight_ecommerce, axis=1)
st.dataframe(styled_df, use_container_width=True)

st.header("Srovnání událostí")
num_columns = st.number_input(
    "Počet sloupců pro srovnání",
    min_value=1,
    max_value=10,
    value=DEFAULT_COLUMNS,
    step=1,
)
cols = st.columns([1] * num_columns)
for idx, col in enumerate(cols):
    with col:
        default_index = DEFAULT_EVENTS[idx] if idx < len(DEFAULT_EVENTS) else 1
        if default_index > num_events:
            default_index = 1
        event_index = st.selectbox(
            f"Vyber událost {idx + 1}",
            options=indices,
            index=default_index - 1,
            key=f"event{idx + 1}",
            format_func=lambda i: f"Událost {i}: {titles[i-1]}",
        )
        event = events[event_index - 1]
        st.subheader(f"Detaily události {event_index}: {titles[event_index - 1]}")
        st.json(event.get("message", {}))
