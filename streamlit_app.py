import streamlit as st
import pandas as pd
import ast
import networkx as nx
import plotly.graph_objects as go

st.set_page_config(page_title="Top 250 Movies Analyzer", layout="wide")

st.title("🎬 Top 250 Movies Analyzer")

st.markdown("""
Lade hier eine CSV oder JSON Datei hoch, die die **Top 250 Filme** enthält.  
Spalten:  
`url`, `title`, `ratingValue`, `ratingCount`, `year`, `description`, `budget`, `gross`, `duration`,  
`genreList`, `countryList`, `castList`, `characterList`, `directorList`.
""")

# --- Datei Upload ---
uploaded_file = st.file_uploader("📁 CSV oder JSON Datei hochladen", type=["csv", "json"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_json(uploaded_file)
    except Exception as e:
        st.error(f"Fehler beim Einlesen der Datei: {e}")
        st.stop()

    # --- Listen-Spalten konvertieren ---
    list_columns = ["genreList", "countryList", "castList", "characterList", "directorList"]
    for col in list_columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

    st.success("✅ Datei erfolgreich geladen!")
    st.subheader("📋 Vorschau der Daten")
    st.dataframe(df.head(20), use_container_width=True)

    # --- Tabs ---
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Patience",
        "Binge Watching Steven Spielberg",
        "This is about me",
        "Workhorse",
        "Cash Horse",
        "WOW Factor 🌟"
    ])

    # --- Tab 1: Patience ---
    with tab1:
        st.header("🎞️ Filme mit epischer Länge (>= 220 Minuten)")
        long_movies = df[df["duration"] >= 220].sort_values(by="duration", ascending=False)
        st.dataframe(long_movies[["title", "year", "duration", "ratingValue", "directorList"]], use_container_width=True)

    # --- Tab 2: Binge Watching Steven Spielberg ---
    with tab2:
        st.header("🎬 Steven Spielberg Marathon")
        spielberg_movies = df[df["directorList"].apply(lambda x: "Steven Spielberg" in x if isinstance(x, list) else False)]
        total_duration = spielberg_movies["duration"].sum()
        st.metric(label="Gesamtlaufzeit aller Steven Spielberg Filme", value=f"{total_duration} Minuten")
        st.dataframe(spielberg_movies[["title", "year", "duration", "ratingValue"]], use_container_width=True)

    # --- Tab 3: This is about me ---
    with tab3:
        st.header("🧍‍♂️ Top Schauspieler nach Gesamtlaufzeit")
        top_n = st.slider("Anzahl der TOP Schauspieler anzeigen", 5, 30, 10)
        cast_duration = {}
        for _, row in df.iterrows():
            for actor in row["castList"]:
                cast_duration[actor] = cast_duration.get(actor, 0) + row["duration"]
        top_cast = pd.DataFrame(sorted(cast_duration.items(), key=lambda x: x[1], reverse=True)[:top_n],
                                columns=["Actor", "Total Duration (min)"])
        st.dataframe(top_cast, use_container_width=True)

    # --- Tab 4: Workhorse ---
    with tab4:
        st.header("💪 Top Schauspieler mit den meisten Filmen")
        top_n = st.slider("Anzahl der TOP Schauspieler anzeigen", 5, 30, 10, key="workhorse_slider")
        cast_counts = {}
        for _, row in df.iterrows():
            for actor in row["castList"]:
                cast_counts[actor] = cast_counts.get(actor, 0) + 1
        top_cast_counts = pd.DataFrame(sorted(cast_counts.items(), key=lambda x: x[1], reverse=True)[:top_n],
                                       columns=["Actor", "Number of Movies"])
        st.dataframe(top_cast_counts, use_container_width=True)

    # --- Tab 5: Cash Horse ---
    with tab5:
        st.header("💰 Top Schauspieler nach Gesamtumsatz (gross)")
        top_n = st.slider("Anzahl der TOP Schauspieler anzeigen", 5, 30, 10, key="cashhorse_slider")
        cast_gross = {}
        for _, row in df.iterrows():
            for actor in row["castList"]:
                cast_gross[actor] = cast_gross.get(actor, 0) + (row["gross"] if pd.notna(row["gross"]) else 0)
        top_cast_gross = pd.DataFrame(sorted(cast_gross.items(), key=lambda x: x[1], reverse=True)[:top_n],
                                      columns=["Actor", "Total Gross"])
        st.dataframe(top_cast_gross, use_container_width=True)

    # --- WOW Factor: Netzwerk-Graph ---
    with tab6:
        st.header("🌟 WOW Factor: Netzwerk der Kollaborationen zwischen Regisseuren und Schauspielern")
        st.markdown("Erkunde visuell, wer mit wem am häufigsten zusammengearbeitet hat!")

        top_n_directors = st.slider("Wähle Anzahl der Top-Regisseure", 3, 15, 5)
        top_n_actors = st.slider("Wähle Anzahl der Top-Schauspieler", 10, 50, 20)

        # Zähle Regisseure und Schauspieler
        director_counts = {}
        actor_counts = {}
        for _, row in df.iterrows():
            for d in row["directorList"]:
                director_counts[d] = director_counts.get(d, 0) + 1
            for a in row["castList"]:
                actor_counts[a] = actor_counts.get(a, 0) + 1

        top_directors = set([d for d, _ in sorted(director_counts.items(), key=lambda x: x[1], reverse=True)[:top_n_directors]])
        top_actors = set([a for a, _ in sorted(actor_counts.items(), key=lambda x: x[1], reverse=True)[:top_n_actors]])

        # Netzwerk aufbauen
        G = nx.Graph()
        for _, row in df.iterrows():
            for d in row["directorList"]:
                if d in top_directors:
                    for a in row["castList"]:
                        if a in top_actors:
                            if G.has_edge(d, a):
                                G[d][a]['weight'] += 1
                            else:
                                G.add_edge(d, a, weight=1)

        # Positionierung und Layout
        pos = nx.spring_layout(G, k=0.4, iterations=30, seed=42)

        edge_x, edge_y = [], []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines'
        )

        node_x, node_y, node_text, node_color = [], [], [], []
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
            if node in top_directors:
                node_color.append("#1f77b4")  # Blau für Regisseure
            else:
                node_color.append("#ff7f0e")  # Orange für Schauspieler

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=node_text,
            textposition="top center",
            hoverinfo='text',
            marker=dict(
                color=node_color,
                size=10,
                line=dict(width=1, color='DarkSlateGrey')
            )
        )

        fig = go.Figure(data=[edge_trace, node_trace],
                        layout=go.Layout(
                            showlegend=False,
                            hovermode='closest',
                            margin=dict(b=0, l=0, r=0, t=30),
                            title="🎥 Netzwerk der Regisseur–Schauspieler Kollaborationen"
                        ))
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("⬆️ Bitte lade eine Datei hoch, um zu starten.")
