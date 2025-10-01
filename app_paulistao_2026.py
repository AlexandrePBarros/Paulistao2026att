import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="Paulistão Compacto 2025 – Totalmente Interativo", layout="wide")
st.title("Paulistão Compacto 2025 – Totalmente Interativo")

# 1️⃣ Nomes dos times
st.subheader("Editar nomes dos 16 times")
default_teams = [
    "Água Santa", "Botafogo-SP", "Bragantino", "Corinthians",
    "Guarani", "Inter de Limeira", "Mirassol", "Noroeste",
    "Novorizontino", "Palmeiras", "Ponte Preta", "Portuguesa",
    "Red Bull Bragantino", "Santos", "São Bernardo", "São Paulo"
]
teams = []
for i in range(16):
    name = st.text_input(f"Time {i+1}", default_teams[i])
    teams.append(name)

# 2️⃣ Sorteio fase de grupos
if st.button("Sortear 5 jogos por time (fase de grupos)"):
    if "fase_grupos" in st.session_state:
        del st.session_state["fase_grupos"]
    if "semis" in st.session_state:
        del st.session_state["semis"]
    if "final" in st.session_state:
        del st.session_state["final"]
    
    random.seed(42)
    pairs = [(teams[i], teams[j]) for i in range(16) for j in range(i+1, 16)]
    rounds = [[] for _ in range(5)]
    team_opponents = {t: set() for t in teams}
    
    sorteio_concluido = False
    while not sorteio_concluido:
        random.shuffle(pairs)
        rounds = [[] for _ in range(5)]
        team_opponents = {t: set() for t in teams}
        available_pairs = pairs.copy()
        
        for rnd in range(5):
            attempts = 0
            while len(rounds[rnd]) < 8 and attempts < 500:
                attempts += 1
                if not available_pairs:
                    break
                
                pair_found = False
                temp_available = available_pairs.copy()
                random.shuffle(temp_available)
                
                for p in temp_available:
                    a, b = p
                    teams_in_round = {t for match in rounds[rnd] for t in match}
                    
                    if a not in teams_in_round and b not in teams_in_round and                        b not in team_opponents[a] and a not in team_opponents[b]:
                        rounds[rnd].append(p)
                        team_opponents[a].add(b)
                        team_opponents[b].add(a)
                        available_pairs.remove(p)
                        pair_found = True
                        break
                
                if not pair_found:
                    break
            
            if len(rounds[rnd]) < 8:
                break
        
        if all(len(r) == 8 for r in rounds):
            sorteio_concluido = True

    home_count = {t: 0 for t in teams}
    assign_rounds = []
    for rnd_matches in rounds:
        rnd_assigned = []
        for a, b in rnd_matches:
            if home_count[a] < home_count[b]:
                home, away = a, b
            elif home_count[b] < home_count[a]:
                home, away = b, a
            else:
                home, away = random.choice([(a, b), (b, a)])
            home_count[home] += 1
            rnd_assigned.append((home, away))
        assign_rounds.append(rnd_assigned)

    rows = []
    for r_idx, rnd in enumerate(assign_rounds, start=1):
        for match in rnd:
            rows.append({"Rodada": r_idx, "Mandante": match[0], "Visitante": match[1],
                         "Gols Mandante": 0, "Gols Visitante": 0})
    df_rounds = pd.DataFrame(rows)
    st.session_state["fase_grupos"] = df_rounds
    st.success("Sorteio concluído! Agora você pode editar os placares da fase de grupos.")

# 3️⃣ Placar fase de grupos
if "fase_grupos" in st.session_state:
    st.subheader("Editar Placar da Fase de Grupos")
    df_rounds = st.session_state["fase_grupos"]
    edited_df = st.data_editor(df_rounds, num_rows="dynamic")
    st.session_state["fase_grupos"] = edited_df

    st.subheader("Cartões para critério disciplinar")
    cards_df = pd.DataFrame({"Time": teams, "Cartões": [0] * 16})
    cards_df = st.data_editor(cards_df, num_rows="fixed")
    cards_dict = dict(zip(cards_df["Time"], cards_df["Cartões"]))

    points = {t: 0 for t in teams}
    gf = {t: 0 for t in teams}
    ga = {t: 0 for t in teams}
    matches = {}

    for _, row in edited_df.iterrows():
        h, a = row["Mandante"], row["Visitante"]
        gh, ga_ = int(row["Gols Mandante"]), int(row["Gols Visitante"])
        gf[h] += gh
        gf[a] += ga_
        ga[h] += ga_
        ga[a] += gh
        matches[(h, a)] = (gh, ga_)
        if gh > ga_:
            points[h] += 3
        elif gh < ga_:
            points[a] += 3
        else:
            points[h] += 1
            points[a] += 1

    classif = []
    for t in teams:
        classif.append({"Time": t, "Pontos": points[t], "GP": gf[t], "GC": ga[t],
                        "SG": gf[t] - ga[t], "Cartões": cards_dict.get(t, 0)})
    df_classif = pd.DataFrame(classif)

    def desempate_confronto(t1, t2):
        for match_teams, scores in matches.items():
            if set(match_teams) == {t1, t2}:
                gh, ga_ = scores
                if match_teams[0] == t1:
                    if gh > ga_: return 1
                    if ga_ > gh: return -1
                else:
                    if ga_ > gh: return 1
                    if gh > ga_: return -1
                return 0
        return 0

    def ranking(df):
        df_sorted = df.sort_values(["Pontos", "SG", "GP"], ascending=[False, False, False]).reset_index(drop=True)
        i = 0
        while i < len(df_sorted) - 1:
            t1, t2 = df_sorted.loc[i, "Time"], df_sorted.loc[i + 1, "Time"]
            if df_sorted.loc[i, "Pontos"] == df_sorted.loc[i + 1, "Pontos"] and                df_sorted.loc[i, "SG"] == df_sorted.loc[i + 1, "SG"] and                df_sorted.loc[i, "GP"] == df_sorted.loc[i + 1, "GP"]:
                res = desempate_confronto(t1, t2)
                if res == -1:
                    df_sorted.iloc[[i, i + 1]] = df_sorted.iloc[[i + 1, i]].values
                elif res == 0:
                    if df_sorted.loc[i, "Cartões"] > df_sorted.loc[i + 1, "Cartões"]:
                        df_sorted.iloc[[i, i + 1]] = df_sorted.iloc[[i + 1, i]].values
                    elif df_sorted.loc[i, "Cartões"] == df_sorted.loc[i + 1, "Cartões"]:
                        if random.random() < 0.5:
                            df_sorted.iloc[[i, i + 1]] = df_sorted.iloc[[i + 1, i]].values
            i += 1
        return df_sorted

    df_classif = ranking(df_classif)
    st.subheader("Classificação Atualizada")
    st.dataframe(df_classif)

    st.subheader("Fase Final – Registrar resultados de ida e volta")

    def create_knockout_df(round_name, matches):
        rows = []
        for idx, (h, a) in enumerate(matches, start=1):
            rows.append({
                "Partida": f"{round_name} {idx}",
                "Mandante (ida)": h, "Visitante (ida)": a,
                "Gols Mandante (ida)": 0, "Gols Visitante (ida)": 0,
                "Mandante (volta)": a, "Visitante (volta)": h,
                "Gols Mandante (volta)": 0, "Gols Visitante (volta)": 0
            })
        return pd.DataFrame(rows)

    def get_winners(df_knockout):
        winners = []
        for _, row in df_knockout.iterrows():
            ida_gols_mandante = int(row["Gols Mandante (ida)"])
            ida_gols_visitante = int(row["Gols Visitante (ida)"])
            volta_gols_mandante = int(row["Gols Mandante (volta)"])
            volta_gols_visitante = int(row["Gols Visitante (volta)"])
            time_1 = row["Mandante (ida)"]
            time_2 = row["Visitante (ida)"]
            placar_agregado_time_1 = ida_gols_mandante + volta_gols_visitante
            placar_agregado_time_2 = ida_gols_visitante + volta_gols_mandante
            if placar_agregado_time_1 > placar_agregado_time_2:
                winners.append(time_1)
            elif placar_agregado_time_2 > placar_agregado_time_1:
                winners.append(time_2)
            else:
                if random.random() < 0.5:
                    winners.append(time_1)
                else:
                    winners.append(time_2)
        return winners

    top8 = df_classif.head(8)["Time"].tolist()
    quartas = [(top8[0], top8[7]), (top8[1], top8[6]), (top8[2], top8[5]), (top8[3], top8[4])]
    
    if "quartas" not in st.session_state:
        st.session_state["quartas"] = create_knockout_df("Q", quartas)
        st.success("Quartas de final definidas! Edite os placares abaixo.")

    edited_q = st.data_editor(st.session_state["quartas"], num_rows="dynamic")
    st.session_state["quartas"] = edited_q

    if st.button("Calcular Semifinais"):
        winners_q = get_winners(st.session_state["quartas"])
        semis = [(winners_q[0], winners_q[3]), (winners_q[1], winners_q[2])]
        st.session_state["semis"] = create_knockout_df("S", semis)
        st.success("Semifinais definidas! Edite os placares abaixo.")

    if "semis" in st.session_state:
        st.subheader("Semifinais")
        edited_s = st.data_editor(st.session_state["semis"], num_rows="dynamic")
        st.session_state["semis"] = edited_s

        if st.button("Calcular Final"):
            winners_s = get_winners(st.session_state["semis"])
            final = [(winners_s[0], winners_s[1])]
            st.session_state["final"] = create_knockout_df("F", final)
            st.success("Final definida! Edite os placares abaixo.")

    if "final" in st.session_state:
        st.subheader("Final")
        edited_f = st.data_editor(st.session_state["final"], num_rows="dynamic")
        st.session_state["final"] = edited_f

        if st.button("Revelar o Campeão!"):
            winner_f = get_winners(st.session_state["final"])
            st.balloons()
            st.subheader(f"🏆 O grande campeão do Paulistão 2025 é: **{winner_f[0]}**!")
