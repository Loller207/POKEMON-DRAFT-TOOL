import json
import math
import random
import threading
from io import BytesIO
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image
import requests

# --- CONFIGURAZIONE TEMA E FONT ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

FONT_FAMILY = "Consolas"
FONT_TITLE = (FONT_FAMILY, 14, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 12, "bold")
FONT_BODY = (FONT_FAMILY, 11)
FONT_SM = (FONT_FAMILY, 10)
FONT_XS = (FONT_FAMILY, 9)

BASE_URL = "https://pokeapi.co/api/v2"

# Mappatura dei range degli ID Pokémon per Generazione
GEN_RANGES = {
    1: (1, 151),
    2: (152, 251),
    3: (252, 386),
    4: (387, 493),
    5: (494, 649),
    6: (650, 721),
    7: (722, 809),
    8: (810, 905),
    9: (906, 1025)
}

DEFAULT_BANNED_MOVES = [
    "fissure", "sheer-cold", "guillotine", "double-team"
]

DEFAULT_BANNED_POKEMON = []

COMMON_ITEMS = [
    "leftovers", "life-orb", "choice-band", "choice-specs", "choice-scarf",
    "focus-sash", "heavy-duty-boots", "assault-vest", "rocky-helmet", "eviolite",
    "expert-belt", "black-sludge", "sitrus-berry", "lum-berry", "weakness-policy",
    "air-balloon", "light-clay", "damp-rock", "heat-rock"
]

TYPE_CHART = {
    "normal": {"rock": 0.5, "ghost": 0, "steel": 0.5},
    "fire": {"fire": 0.5, "water": 0.5, "grass": 2.0, "ice": 2.0, "bug": 2.0, "rock": 0.5, "dragon": 0.5, "steel": 2.0},
    "water": {"fire": 2.0, "water": 0.5, "grass": 0.5, "ground": 2.0, "rock": 2.0, "dragon": 0.5},
    "grass": {"fire": 0.5, "water": 2.0, "grass": 0.5, "poison": 0.5, "ground": 2.0, "flying": 0.5, "bug": 0.5, "rock": 2.0, "dragon": 0.5, "steel": 0.5},
    "electric": {"water": 2.0, "grass": 0.5, "electric": 0.5, "ground": 0, "flying": 2.0, "dragon": 0.5},
    "ice": {"fire": 0.5, "water": 0.5, "grass": 2.0, "ice": 0.5, "ground": 2.0, "flying": 2.0, "dragon": 2.0, "steel": 0.5},
    "fighting": {"normal": 2.0, "ice": 2.0, "poison": 0.5, "flying": 0.5, "psychic": 0.5, "bug": 0.5, "rock": 2.0, "ghost": 0, "dark": 2.0, "steel": 2.0, "fairy": 0.5},
    "poison": {"grass": 2.0, "poison": 0.5, "ground": 0.5, "rock": 0.5, "ghost": 0.5, "steel": 0, "fairy": 2.0},
    "ground": {"fire": 2.0, "grass": 0.5, "electric": 2.0, "poison": 2.0, "flying": 0, "bug": 0.5, "rock": 2.0, "steel": 2.0},
    "flying": {"grass": 2.0, "electric": 0.5, "fighting": 2.0, "bug": 2.0, "rock": 0.5, "steel": 0.5},
    "psychic": {"fighting": 2.0, "poison": 2.0, "psychic": 0.5, "dark": 0, "steel": 0.5},
    "bug": {"fire": 0.5, "grass": 2.0, "fighting": 0.5, "poison": 0.5, "flying": 0.5, "psychic": 2.0, "ghost": 0.5, "dark": 2.0, "steel": 0.5, "fairy": 0.5},
    "rock": {"fire": 2.0, "ice": 2.0, "fighting": 0.5, "ground": 0.5, "flying": 2.0, "bug": 2.0, "steel": 0.5},
    "ghost": {"normal": 0, "psychic": 2.0, "ghost": 2.0, "dark": 0.5},
    "dragon": {"dragon": 2.0, "steel": 0.5, "fairy": 0},
    "dark": {"fighting": 0.5, "psychic": 2.0, "ghost": 2.0, "dark": 0.5, "fairy": 0.5},
    "steel": {"fire": 0.5, "water": 0.5, "electric": 0.5, "ice": 2.0, "rock": 2.0, "steel": 0.5, "fairy": 2.0},
    "fairy": {"fire": 0.5, "fighting": 2.0, "poison": 0.5, "dragon": 2.0, "dark": 2.0, "steel": 0.5}
}

NATURES = {
    "Adamant": ("+Atk", "-SpA"), "Jolly": ("+Spe", "-SpA"), "Modest": ("+SpA", "-Atk"),
    "Timid": ("+Spe", "-Atk"), "Bold": ("+Def", "-Atk"), "Impish": ("+Def", "-SpA"),
    "Calm": ("+SpD", "-Atk"), "Careful": ("+SpD", "-SpA"), "Naive": ("+Spe", "-SpD"),
    "Hasty": ("+Spe", "-Def"), "Brave": ("+Atk", "-Spe"), "Quiet": ("+SpA", "-Spe"),
    "Hardy": ("Neutro", ""), "Docile": ("Neutro", ""), "Bashful": ("Neutro", ""),
    "Quirky": ("Neutro", ""), "Serious": ("Neutro", "")
}

STAT_KEY_MAP = {
    "hp": "hp", "attack": "atk", "defense": "def",
    "special-attack": "spa", "special-defense": "spd", "speed": "spe"
}


# ==============================================================================
# FINESTRA DI CONFIGURAZIONE PRE-DRAFT (REGOLAMENTO)
# ==============================================================================
class DraftConfigWindow(ctk.CTkToplevel):
    def __init__(self, parent, on_start_callback):
        super().__init__(parent)
        self.title("⚙️ Configurazione Regole Draft")
        self.geometry("600x680")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        self.on_start_callback = on_start_callback

        self.banned_gens = []
        self.banned_moves = list(DEFAULT_BANNED_MOVES)
        self.banned_pokemon = list(DEFAULT_BANNED_POKEMON)

        # Title
        lbl_title = ctk.CTkLabel(self, text="⚙️ IMPOSTAZIONI REGOLE DRAFT", font=FONT_TITLE, text_color="#61AFEF")
        lbl_title.pack(pady=10)

        # Export/Import Bar
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=5)

        btn_imp = ctk.CTkButton(btn_frame, text="📥 Importa Regole (.txt/.json)", font=FONT_SM, fg_color="#D19A66", hover_color="#B27D4A", command=self.import_rules)
        btn_imp.pack(side="left", expand=True, padx=5)

        btn_exp = ctk.CTkButton(btn_frame, text="📤 Esporta Regole (.txt/.json)", font=FONT_SM, fg_color="#E5C07B", hover_color="#C49F5A", text_color="#1E222A", command=self.export_rules)
        btn_exp.pack(side="right", expand=True, padx=5)

        # Tab View per organizzare le tre sezioni
        self.tabview = ctk.CTkTabview(self, width=560, height=480)
        self.tabview.pack(padx=15, pady=10, fill="both", expand=True)

        self.tab_gen = self.tabview.add("Generazioni Bannate")
        self.tab_moves = self.tabview.add("Mosse Bannate")
        self.tab_poke = self.tabview.add("Pokémon Bannati")

        self.setup_gen_tab()
        self.setup_list_tab(self.tab_moves, "mossa", self.banned_moves, self.refresh_moves)
        self.setup_list_tab(self.tab_poke, "pokémon", self.banned_pokemon, self.refresh_pokemon)

        # Bottone Avvio
        btn_start = ctk.CTkButton(self, text="AVVIA DRAFT CON QUESTE REGOLE", font=FONT_SUBTITLE, height=45, fg_color="#98C379", hover_color="#7CA35F", text_color="#1E222A", command=self.confirm_and_start)
        btn_start.pack(fill="x", padx=15, pady=12)

    def setup_gen_tab(self):
        lbl = ctk.CTkLabel(self.tab_gen, text="Spunta le Generazioni che vuoi BANNARE dal Draft:", font=FONT_BODY)
        lbl.pack(pady=10)

        self.gen_vars = {}
        frame_grid = ctk.CTkFrame(self.tab_gen, fg_color="transparent")
        frame_grid.pack(pady=10)

        for gen in range(1, 10):
            var = ctk.BooleanVar(value=False)
            self.gen_vars[gen] = var
            r, c = divmod(gen - 1, 3)
            chk = ctk.CTkCheckBox(frame_grid, text=f"Gen {gen} ({GEN_RANGES[gen][0]}-{GEN_RANGES[gen][1]})", variable=var, font=FONT_BODY)
            chk.grid(row=r, column=c, padx=15, pady=12, sticky="w")

    def setup_list_tab(self, tab, entity_name, data_list, refresh_callback):
        input_frame = ctk.CTkFrame(tab, fg_color="transparent")
        input_frame.pack(fill="x", padx=10, pady=10)

        entry = ctk.CTkEntry(input_frame, placeholder_text=f"Aggiungi {entity_name}...", font=FONT_BODY)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        def _add():
            val = entry.get().strip().lower().replace(" ", "-")
            if val and val not in data_list:
                data_list.append(val)
                entry.delete(0, "end")
                refresh_callback()

        btn_add = ctk.CTkButton(input_frame, text="Aggiungi", width=80, font=FONT_SM, fg_color="#98C379", text_color="#1E222A", command=_add)
        btn_add.pack(side="right")

        scroll = ctk.CTkScrollableFrame(tab)
        scroll.pack(fill="both", expand=True, padx=10, pady=5)

        tab.scroll_widget = scroll
        refresh_callback()

    def refresh_moves(self):
        scroll = self.tab_moves.scroll_widget
        for w in scroll.winfo_children():
            w.destroy()
        for move in sorted(self.banned_moves):
            r = ctk.CTkFrame(scroll, fg_color="transparent")
            r.pack(fill="x", pady=2)
            ctk.CTkLabel(r, text=move.replace("-", " ").title(), font=FONT_BODY, anchor="w").pack(side="left", fill="x", expand=True)
            ctk.CTkButton(r, text="❌", width=30, height=22, fg_color="#E06C75", command=lambda m=move: (self.banned_moves.remove(m), self.refresh_moves())).pack(side="right")

    def refresh_pokemon(self):
        scroll = self.tab_poke.scroll_widget
        for w in scroll.winfo_children():
            w.destroy()
        for pk in sorted(self.banned_pokemon):
            r = ctk.CTkFrame(scroll, fg_color="transparent")
            r.pack(fill="x", pady=2)
            ctk.CTkLabel(r, text=pk.replace("-", " ").title(), font=FONT_BODY, anchor="w").pack(side="left", fill="x", expand=True)
            ctk.CTkButton(r, text="❌", width=30, height=22, fg_color="#E06C75", command=lambda p=pk: (self.banned_pokemon.remove(p), self.refresh_pokemon())).pack(side="right")

    def export_rules(self):
        banned_gens = [g for g, v in self.gen_vars.items() if v.get()]
        data = {
            "banned_generations": banned_gens,
            "banned_moves": self.banned_moves,
            "banned_pokemon": self.banned_pokemon
        }
        fpath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON / TXT Rules", "*.json *.txt")], title="Esporta Regole Draft")
        if fpath:
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            messagebox.showinfo("Successo", "Regole esportate correttamente!")

    def import_rules(self):
        fpath = filedialog.askopenfilename(filetypes=[("JSON / TXT Rules", "*.json *.txt")], title="Importa Regole Draft")
        if fpath:
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                banned_gens = data.get("banned_generations", [])
                for g, var in self.gen_vars.items():
                    var.set(g in banned_gens)
                self.banned_moves = data.get("banned_moves", [])
                self.banned_pokemon = data.get("banned_pokemon", [])
                self.refresh_moves()
                self.refresh_pokemon()
                messagebox.showinfo("Successo", "Regole importate con successo!")
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile leggere il file delle regole: {e}")

    def confirm_and_start(self):
        banned_gens = [g for g, v in self.gen_vars.items() if v.get()]
        if len(banned_gens) == 9:
            messagebox.showwarning("Attenzione", "Non puoi bannare tutte le 9 generazioni!")
            return

        rules = {
            "banned_gens": banned_gens,
            "banned_moves": self.banned_moves,
            "banned_pokemon": self.banned_pokemon
        }
        self.destroy()
        self.on_start_callback(rules)


# ==============================================================================
# POKÉMON DRAFT TOOL
# ==============================================================================
class PokemonDraftApp(ctk.CTkToplevel):
    def __init__(self, parent, rules):
        super().__init__(parent)

        self.title("Pokémon Draft Tool")
        try:
            self.state("zoomed")
        except Exception:
            self.attributes("-fullscreen", True)

        self.rules = rules
        self.banned_moves = list(rules.get("banned_moves", DEFAULT_BANNED_MOVES))
        self.banned_pokemon = list(rules.get("banned_pokemon", []))
        self.banned_gens = list(rules.get("banned_gens", []))

        # Calcolo ID ammessi in base alle Generazioni bannate
        self.valid_poke_ids = []
        for gen, (start, end) in GEN_RANGES.items():
            if gen not in self.banned_gens:
                self.valid_poke_ids.extend(range(start, end + 1))

        self.image_cache = {}
        self.move_cache = {}
        self.item_cache = {}
        self.ability_cache = {}
        self.draft_round = 0
        self.team = []
        self.current_pokemon = None
        self.current_options = []
        self.move_pick_round = 0

        # Disposizione Griglia Principale
        self.grid_columnconfigure(0, weight=5, uniform="main_col")
        self.grid_columnconfigure(1, weight=3, uniform="main_col")
        self.grid_rowconfigure(0, weight=1)

        # Colonna Sinistra
        self.left_container = ctk.CTkFrame(self, fg_color="transparent")
        self.left_container.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.left_container.rowconfigure(0, weight=2, uniform="left_row")
        self.left_container.rowconfigure(1, weight=3, uniform="left_row")
        self.left_container.columnconfigure(0, weight=1)

        self.action_frame = ctk.CTkFrame(self.left_container, corner_radius=8)
        self.action_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        # TEAM VIEWER
        self.team_frame = ctk.CTkFrame(self.left_container, corner_radius=8)
        self.team_frame.grid(row=1, column=0, sticky="nsew")

        # Colonna Destra
        self.right_container = ctk.CTkFrame(self, fg_color="transparent")
        self.right_container.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")
        self.right_container.rowconfigure(0, weight=1, uniform="right_row")
        self.right_container.rowconfigure(1, weight=2, uniform="right_row")
        self.right_container.columnconfigure(0, weight=1)

        self.detail_frame = ctk.CTkFrame(self.right_container, corner_radius=8)
        self.detail_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        self.sidebar_frame = ctk.CTkFrame(self.right_container, corner_radius=8)
        self.sidebar_frame.grid(row=1, column=0, sticky="nsew")

        self.setup_detail_box()
        self.setup_sidebar()
        self.setup_team_view()

        self.show_loading("Inizializzazione Draft...")
        threading.Thread(target=self.start_draft, daemon=True).start()

    def fetch_ability_description(self, ability_name):
        if not ability_name or ability_name == "Nessuna":
            return "Nessun effetto disponibile."
        if ability_name in self.ability_cache:
            return self.ability_cache[ability_name]

        try:
            res = requests.get(f"{BASE_URL}/ability/{ability_name.lower().replace(' ', '-')}", timeout=4).json()
            for entry in res.get('effect_entries', []):
                if entry['language']['name'] == 'en':
                    desc = entry['short_effect']
                    self.ability_cache[ability_name] = desc
                    return desc
        except Exception:
            pass
        return "Descrizione abilità non reperibile."

    def fetch_item_description(self, item_name):
        if not item_name:
            return "Nessun oggetto equipaggiato."
        if item_name in self.item_cache:
            return self.item_cache[item_name]
        try:
            res = requests.get(f"{BASE_URL}/item/{item_name.lower().replace(' ', '-')}", timeout=4).json()
            for entry in res.get('effect_entries', []):
                if entry['language']['name'] == 'en':
                    desc = entry['short_effect']
                    self.item_cache[item_name] = desc
                    return desc
        except Exception:
            pass
        return "Descrizione oggetto non disponibile."

    def fetch_move_data(self, move_name):
        if move_name in self.move_cache:
            return self.move_cache[move_name]
        try:
            res = requests.get(f"{BASE_URL}/move/{move_name.lower().replace(' ', '-')}", timeout=4).json()
            desc = "Descrizione non disponibile."
            for entry in res.get('effect_entries', []):
                if entry['language']['name'] == 'en':
                    desc = entry['short_effect']
                    break

            data = {
                'desc': desc,
                'power': res.get('power', '-') or '-',
                'accuracy': res.get('accuracy', '-') or '-',
                'type': res['type']['name'].capitalize(),
                'damage_class': res['damage_class']['name'].capitalize(),
            }
            self.move_cache[move_name] = data
            return data
        except Exception:
            pass
        return {'desc': "Descrizione non disponibile.", 'power': '-', 'accuracy': '-', 'type': '-', 'damage_class': '-'}

    def get_pokemon_image(self, url, size=(70, 70)):
        if not url:
            return None
        if url in self.image_cache:
            return self.image_cache[url]
        try:
            res = requests.get(url, timeout=5)
            img_data = Image.open(BytesIO(res.content))
            ctk_img = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=size)
            self.image_cache[url] = ctk_img
            return ctk_img
        except Exception:
            return None

    def setup_detail_box(self):
        lbl_title = ctk.CTkLabel(self.detail_frame, text="[ SCHEDA POKÉMON SELEZIONATO ]", font=FONT_SUBTITLE, text_color="#58A6FF")
        lbl_title.pack(pady=(8, 2))

        self.txt_details = ctk.CTkTextbox(self.detail_frame, font=FONT_BODY, fg_color="transparent", activate_scrollbars=True)
        self.txt_details.pack(fill="both", expand=True, padx=8, pady=4)
        self.set_detail_text("Clicca su una card in alto o su uno slot del Team Viewer per vederne i dettagli.")

    def set_detail_text(self, text):
        self.txt_details.configure(state="normal")
        self.txt_details.delete("0.0", "end")
        self.txt_details.insert("0.0", text)
        self.txt_details.configure(state="disabled")

    def refresh_pokemon_details(self, pdata):
        if not pdata:
            return

        self.update_sidebar(pdata)

        def _bg_fetch_and_render():
            ab_name = pdata['selected_ability'].replace('-', ' ').title()
            ab_desc = pdata.get('ability_desc', self.fetch_ability_description(pdata['selected_ability']))

            lines = [
                f"=== {pdata['name'].upper()} ===",
                f"• ABILITÀ: {ab_name}",
                f"  -> Effetto: {ab_desc}"
            ]

            if pdata.get("selected_moves"):
                lines.append("\n• MOSSE SELEZIONATE:")
                for m in pdata["selected_moves"]:
                    m_title = m.replace('-', ' ').title()
                    m_info = self.fetch_move_data(m)
                    lines.append(f"  - {m_title} [{m_info['type']} | {m_info['damage_class']}] - Pot: {m_info['power']} | Prec: {m_info['accuracy']}%")
                    lines.append(f"    Effetto: {m_info['desc']}")

            if pdata.get("selected_item"):
                item_title = pdata['selected_item'].replace('-', ' ').title()
                item_desc = self.fetch_item_description(pdata['selected_item'])
                lines.append(f"\n• OGGETTO: {item_title}")
                lines.append(f"  -> Effetto: {item_desc}")

            self.after(0, lambda: self.set_detail_text("\n".join(lines)))

        threading.Thread(target=_bg_fetch_and_render, daemon=True).start()

    def setup_sidebar(self):
        self.sidebar_frame.pack_propagate(False)

        self.lbl_side_title = ctk.CTkLabel(self.sidebar_frame, text="Info Pokémon", font=FONT_TITLE)
        self.lbl_side_title.pack(pady=(8, 2))

        self.lbl_side_image = ctk.CTkLabel(self.sidebar_frame, text="", height=45)
        self.lbl_side_image.pack(pady=0)

        self.lbl_types = ctk.CTkLabel(self.sidebar_frame, text="Tipi: -", font=FONT_BODY)
        self.lbl_types.pack(pady=0)

        self.lbl_bst = ctk.CTkLabel(self.sidebar_frame, text="BST: -", font=FONT_SUBTITLE, text_color="#E5C07B")
        self.lbl_bst.pack(pady=2)

        self.lbl_abilities = ctk.CTkLabel(self.sidebar_frame, text="Abilità: -", font=FONT_SM, wraplength=300)
        self.lbl_abilities.pack(pady=0)

        self.stats_container = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.stats_container.pack(fill="x", padx=12, pady=4)

        self.stat_widgets = {}
        stat_names = [("hp", "HP "), ("attack", "ATK"), ("defense", "DEF"), ("special-attack", "SPA"), ("special-defense", "SPD"), ("speed", "SPE")]

        for key, label_text in stat_names:
            row = ctk.CTkFrame(self.stats_container, fg_color="transparent")
            row.pack(fill="x", pady=1)

            lbl = ctk.CTkLabel(row, text=label_text, font=FONT_SM, width=35, anchor="w")
            lbl.pack(side="left")

            val_lbl = ctk.CTkLabel(row, text="0", font=FONT_SM, width=35, anchor="e")
            val_lbl.pack(side="left", padx=(0, 6))

            bar = ctk.CTkProgressBar(row, height=7)
            bar.pack(side="left", fill="x", expand=True)
            bar.set(0)

            self.stat_widgets[key] = {"val": val_lbl, "bar": bar}

        matchup_box = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        matchup_box.pack(fill="x", padx=12, pady=(2, 6))

        self.lbl_weak_x4 = ctk.CTkLabel(matchup_box, text="Debolezze x4: -", font=FONT_XS, text_color="#E06C75", anchor="w")
        self.lbl_weak_x4.pack(fill="x")

        self.lbl_weak_x2 = ctk.CTkLabel(matchup_box, text="Debolezze x2: -", font=FONT_XS, text_color="#D19A66", anchor="w")
        self.lbl_weak_x2.pack(fill="x")

        self.lbl_immunity = ctk.CTkLabel(matchup_box, text="Immunità (x0): -", font=FONT_XS, text_color="#7F848E", anchor="w")
        self.lbl_immunity.pack(fill="x")

        self.lbl_res_x05 = ctk.CTkLabel(matchup_box, text="Resistenze x0.5: -", font=FONT_XS, text_color="#98C379", anchor="w")
        self.lbl_res_x05.pack(fill="x")

        self.lbl_res_x025 = ctk.CTkLabel(matchup_box, text="Super Res. x0.25: -", font=FONT_XS, text_color="#56B6C2", anchor="w")
        self.lbl_res_x025.pack(fill="x")

    def setup_team_view(self):
        lbl_team_title = ctk.CTkLabel(self.team_frame, text="IL TUO TEAM (Clicca su uno slot per vederne i dettagli)", font=FONT_SUBTITLE, text_color="#E5C07B")
        lbl_team_title.pack(pady=6)

        self.team_grid_frame = ctk.CTkFrame(self.team_frame, fg_color="transparent")
        self.team_grid_frame.pack(fill="both", expand=True, padx=6, pady=4)

        for i in range(2):
            self.team_grid_frame.grid_rowconfigure(i, weight=1, uniform="team_r")
        for j in range(3):
            self.team_grid_frame.grid_columnconfigure(j, weight=1, uniform="team_c")

        self.team_slots = []
        for idx in range(6):
            r, c = divmod(idx, 3)
            slot = ctk.CTkFrame(self.team_grid_frame, border_width=1, border_color="#3E4451", corner_radius=6, cursor="hand2")
            slot.grid(row=r, column=c, padx=4, pady=4, sticky="nsew")

            header_frame = ctk.CTkFrame(slot, fg_color="transparent")
            header_frame.pack(fill="x", padx=4, pady=2)

            lbl_img = ctk.CTkLabel(header_frame, text="", width=35, height=35)
            lbl_img.pack(side="left", padx=(0, 4))

            lbl_name = ctk.CTkLabel(header_frame, text=f"Slot {idx+1}: Vuoto", font=FONT_SM, anchor="w")
            lbl_name.pack(side="left", fill="x", expand=True)

            txt_info = ctk.CTkTextbox(slot, font=FONT_XS, fg_color="transparent", activate_scrollbars=False)
            txt_info.pack(fill="both", expand=True, padx=4, pady=2)

            for widget in (slot, header_frame, lbl_img, lbl_name, txt_info):
                widget.bind("<Button-1>", lambda event, i=idx: self.on_slot_click(i))

            self.team_slots.append({"frame": slot, "name": lbl_name, "img": lbl_img, "info": txt_info})

    def on_slot_click(self, index):
        if index < len(self.team):
            pdata = self.team[index]
            self.refresh_pokemon_details(pdata)

    def update_team_view(self):
        for idx, slot in enumerate(self.team_slots):
            if idx < len(self.team):
                p = self.team[idx]
                gender_str = f" ({p['gender']})" if p.get('gender') else ""
                slot["name"].configure(text=f"{idx+1}. {p['name'].capitalize()}{gender_str}", text_color="#61AFEF")

                img = self.get_pokemon_image(p["sprite_url"], size=(35, 35))
                if img:
                    slot["img"].configure(image=img, text="")

                item_str = f"Item: {p['selected_item'].replace('-', ' ').title()}" if p["selected_item"] else "Item: -"
                moves_str = ", ".join([m.replace("-", " ").title() for m in p["selected_moves"]]) if p["selected_moves"] else "Mosse: -"
                ev_str = f"EV: {sum(p['selected_evs'].values())}" if p["selected_evs"] else "EV: -"
                nat_str = f"Nat: {p['selected_nature']}" if p["selected_nature"] else "Nat: -"

                info_text = f"{item_str}\n{nat_str} | {ev_str}\nMosse: {moves_str}"

                slot["info"].configure(state="normal")
                slot["info"].delete("0.0", "end")
                slot["info"].insert("0.0", info_text)
                slot["info"].configure(state="disabled")
            else:
                slot["name"].configure(text=f"Slot {idx+1}: Vuoto", text_color="#5C6370")
                slot["img"].configure(image=None, text="")
                slot["info"].configure(state="normal")
                slot["info"].delete("0.0", "end")
                slot["info"].configure(state="disabled")

    def calculate_stat_level_50(self, stat_name, base_val, ev_val, nature_name):
        short_stat = STAT_KEY_MAP[stat_name]
        if stat_name == "hp":
            return math.floor((2 * base_val + math.floor(ev_val / 4)) * 50 / 100) + 50 + 10

        raw_stat = math.floor((2 * base_val + math.floor(ev_val / 4)) * 50 / 100) + 5
        nature_mod = 1.0
        if nature_name in NATURES:
            plus_stat, minus_stat = NATURES[nature_name]
            nat_map = {
                "+Atk": "atk", "-Atk": "atk", "+Def": "def", "-Def": "def",
                "+SpA": "spa", "-SpA": "spa", "+SpD": "spd", "-SpD": "spd",
                "+Spe": "spe", "-Spe": "spe"
            }
            if plus_stat in nat_map and nat_map[plus_stat] == short_stat:
                nature_mod = 1.1
            elif minus_stat in nat_map and nat_map[minus_stat] == short_stat:
                nature_mod = 0.9

        return math.floor(raw_stat * nature_mod)

    def update_sidebar(self, pdata):
        if not pdata:
            return

        has_full_customization = bool(pdata.get("selected_nature") or pdata.get("selected_evs"))
        title_suffix = " (LIV. 50)" if has_full_customization else ""
        self.lbl_side_title.configure(text=pdata["name"].capitalize() + title_suffix)
        self.lbl_types.configure(text=f"Tipi: {', '.join([t.capitalize() for t in pdata['types']])}")

        img = self.get_pokemon_image(pdata["sprite_url"], size=(55, 55))
        if img:
            self.lbl_side_image.configure(image=img, text="")
        else:
            self.lbl_side_image.configure(image=None, text="[No Pic]")

        ab_title = pdata['selected_ability'].replace('-', ' ').title()
        self.lbl_abilities.configure(text=f"Abilità: {ab_title}")

        total_stats = 0
        for stat_key, widget_group in self.stat_widgets.items():
            base_val = pdata["stats"].get(stat_key, 0)

            if has_full_customization:
                short_key = STAT_KEY_MAP[stat_key]
                ev_val = pdata.get("selected_evs", {}).get(short_key, 0)
                nat = pdata.get("selected_nature", "")
                calc_val = self.calculate_stat_level_50(stat_key, base_val, ev_val, nat)

                widget_group["val"].configure(text=str(calc_val))
                total_stats += calc_val
                progress = min(calc_val / 250.0, 1.0)
                widget_group["bar"].set(progress)
                color = "#E06C75" if calc_val < 80 else "#D19A66" if calc_val < 110 else "#98C379" if calc_val < 150 else "#61AFEF"
            else:
                widget_group["val"].configure(text=str(base_val))
                total_stats += base_val
                progress = min(base_val / 200.0, 1.0)
                widget_group["bar"].set(progress)
                color = "#E06C75" if base_val < 60 else "#D19A66" if base_val < 90 else "#98C379" if base_val < 120 else "#61AFEF"

            widget_group["bar"].configure(progress_color=color)

        label_bst_text = f"STAT TOT (L.50): {total_stats}" if has_full_customization else f"BST: {total_stats}"
        self.lbl_bst.configure(text=label_bst_text)

        matchups = self.calculate_detailed_type_matchups(pdata["types"])
        self.lbl_weak_x4.configure(text="Debolezze x4: " + (", ".join(matchups["x4"]) if matchups["x4"] else "Nessuna"))
        self.lbl_weak_x2.configure(text="Debolezze x2: " + (", ".join(matchups["x2"]) if matchups["x2"] else "Nessuna"))
        self.lbl_immunity.configure(text="Immunità (x0): " + (", ".join(matchups["x0"]) if matchups["x0"] else "Nessuna"))
        self.lbl_res_x05.configure(text="Resistenze x0.5: " + (", ".join(matchups["x0.5"]) if matchups["x0.5"] else "Nessuna"))
        self.lbl_res_x025.configure(text="Super Res. x0.25: " + (", ".join(matchups["x0.25"]) if matchups["x0.25"] else "Nessuna"))

    def calculate_detailed_type_matchups(self, types):
        all_types = TYPE_CHART.keys()
        multipliers = {t: 1.0 for t in all_types}

        for ptype in types:
            ptype = ptype.lower()
            for atk_type, targets in TYPE_CHART.items():
                if ptype in targets:
                    multipliers[atk_type] *= targets[ptype]

        matchups = {"x4": [], "x2": [], "x0": [], "x0.5": [], "x0.25": []}
        for t, m in multipliers.items():
            t_cap = t.capitalize()
            if m == 4.0: matchups["x4"].append(t_cap)
            elif m == 2.0: matchups["x2"].append(t_cap)
            elif m == 0.0: matchups["x0"].append(t_cap)
            elif m == 0.5: matchups["x0.5"].append(t_cap)
            elif m == 0.25: matchups["x0.25"].append(t_cap)

        return matchups

    def clear_action_frame(self):
        for widget in self.action_frame.winfo_children():
            widget.destroy()

    def show_loading(self, message="Caricamento..."):
        self.clear_action_frame()
        lbl = ctk.CTkLabel(self.action_frame, text=message, font=FONT_TITLE)
        lbl.pack(expand=True)

    def start_draft(self):
        self.draft_round = 0
        self.team = []
        self.next_pokemon_round()

    def next_pokemon_round(self):
        if self.draft_round >= 6:
            self.draft_round = 0
            self.start_moves_phase()
            return

        self.draft_round += 1
        self.show_loading(f"Caricamento Pokémon ({self.draft_round}/6)...")

        def _load():
            fetched = []
            attempts = 0
            while len(fetched) < 3 and attempts < 50:
                attempts += 1
                pid = random.choice(self.valid_poke_ids)
                pdata = self.fetch_pokemon_data(pid)
                if pdata and pdata["name"].lower() not in self.banned_pokemon:
                    if not any(x["id"] == pdata["id"] for x in fetched):
                        fetched.append(pdata)

            self.current_options = fetched
            for p in self.current_options:
                self.get_pokemon_image(p["sprite_url"])
            self.after(0, self.display_pokemon_choice)

        threading.Thread(target=_load, daemon=True).start()

    def fetch_pokemon_data(self, poke_id):
        try:
            res = requests.get(f"{BASE_URL}/pokemon/{poke_id}").json()
            types = [t["type"]["name"] for t in res["types"]]
            abilities = [a["ability"]["name"] for a in res["abilities"]]
            stats = {s["stat"]["name"]: s["base_stat"] for s in res["stats"]}
            moves = [m["move"]["name"] for m in res["moves"] if m["move"]["name"] not in self.banned_moves]
            sprite_url = res["sprites"]["front_default"]

            gender = random.choice(["M", "F"])
            selected_ability = random.choice(abilities) if abilities else "Nessuna"
            ability_desc = self.fetch_ability_description(selected_ability)

            return {
                "id": res["id"],
                "name": res["name"],
                "types": types,
                "abilities": abilities,
                "stats": stats,
                "moves": moves,
                "sprite_url": sprite_url,
                "gender": gender,
                "selected_ability": selected_ability,
                "ability_desc": ability_desc,
                "selected_item": "",
                "selected_moves": [],
                "selected_evs": {},
                "selected_nature": "",
            }
        except Exception:
            return None

    def display_pokemon_choice(self):
        self.clear_action_frame()

        title = ctk.CTkLabel(self.action_frame, text=f"Scegli un Pokémon ({self.draft_round}/6)", font=FONT_TITLE)
        title.pack(pady=(6, 2))

        cards_container = ctk.CTkFrame(self.action_frame, fg_color="transparent")
        cards_container.pack(fill="both", expand=True, padx=8, pady=2)
        cards_container.rowconfigure(0, weight=1)

        for i in range(3):
            cards_container.columnconfigure(i, weight=1, uniform="poke_card")

        for idx, pdata in enumerate(self.current_options):
            bst = sum(pdata["stats"].values())
            card = ctk.CTkFrame(cards_container, border_width=1, border_color="#3E4451", corner_radius=8, cursor="hand2")
            card.grid(row=0, column=idx, padx=4, pady=2, sticky="nsew")

            card.bind("<Button-1>", lambda e, p=pdata: self.refresh_pokemon_details(p))

            img = self.get_pokemon_image(pdata["sprite_url"], size=(50, 50))
            if img:
                lbl_img = ctk.CTkLabel(card, image=img, text="")
                lbl_img.pack(pady=(4, 0))
                lbl_img.bind("<Button-1>", lambda e, p=pdata: self.refresh_pokemon_details(p))

            gender_str = f" ({pdata['gender']})" if pdata.get('gender') else ""
            lbl_name = ctk.CTkLabel(card, text=f"{pdata['name'].capitalize()}{gender_str}", font=FONT_SUBTITLE, text_color="#61AFEF")
            lbl_name.pack(pady=0)

            ab_title = pdata['selected_ability'].replace('-', ' ').title()
            lbl_ability = ctk.CTkLabel(card, text=f"⚡ {ab_title}", font=FONT_XS, text_color="#98C379", wraplength=180)
            lbl_ability.pack(pady=(2, 0))

            lbl_bst = ctk.CTkLabel(card, text=f"BST: {bst}", font=FONT_XS, text_color="#E5C07B")
            lbl_bst.pack(pady=(0, 2))

            stats_box = ctk.CTkFrame(card, fg_color="#21252B", corner_radius=6)
            stats_box.pack(fill="x", padx=6, pady=2)

            s = pdata["stats"]
            stat_grid_text = (
                f"HP: {s.get('hp', 0):<3} | ATK: {s.get('attack', 0):<3}\n"
                f"DEF: {s.get('defense', 0):<3} | SPA: {s.get('special-attack', 0):<3}\n"
                f"SPD: {s.get('special-defense', 0):<3} | SPE: {s.get('speed', 0):<3}"
            )

            lbl_stats = ctk.CTkLabel(stats_box, text=stat_grid_text, font=FONT_XS, text_color="#ABB2BF", justify="center")
            lbl_stats.pack(pady=4)

            btn = ctk.CTkButton(card, text="Scegli", font=FONT_SM, height=26, corner_radius=4, command=lambda p=pdata: self.select_pokemon(p))
            btn.pack(pady=(4, 6), padx=10, fill="x")

    def select_pokemon(self, pdata):
        self.team.append(pdata)
        self.update_team_view()
        self.refresh_pokemon_details(pdata)
        self.next_pokemon_round()

    def start_moves_phase(self):
        if self.draft_round >= len(self.team):
            self.draft_round = 0
            self.start_nature_phase()
            return

        self.current_pokemon = self.team[self.draft_round]
        self.refresh_pokemon_details(self.current_pokemon)

        if not self.current_pokemon["moves"]:
            self.draft_round += 1
            self.start_moves_phase()
            return

        self.move_pick_round = len(self.current_pokemon["selected_moves"])
        self.next_move_round()

    def next_move_round(self):
        available = [m for m in self.current_pokemon["moves"] if m not in self.current_pokemon["selected_moves"] and m not in self.banned_moves]

        if self.move_pick_round >= 4 or not available:
            self.draft_round += 1
            self.start_moves_phase()
            return

        self.move_pick_round += 1
        count = min(3, len(available))
        move_options = random.sample(available, count)

        self.clear_action_frame()

        title = ctk.CTkLabel(
            self.action_frame,
            text=f"Mosse per {self.current_pokemon['name'].capitalize()} ({self.draft_round + 1}/6)\nScegli mossa {self.move_pick_round}/4",
            font=FONT_TITLE
        )
        title.pack(pady=(12, 6))

        def on_move_hover(move_name):
            def _bg_fetch():
                m_info = self.fetch_move_data(move_name)
                title_formatted = move_name.replace('-', ' ').title()
                text = (
                    f"=== ANTEPRIMA MOSSA ===\n"
                    f"• {title_formatted} [{m_info['type']} | {m_info['damage_class']}]\n"
                    f"  - Potenza: {m_info['power']} | Precisione: {m_info['accuracy']}%\n"
                    f"  -> Effetto: {m_info['desc']}"
                )
                self.after(0, lambda: self.set_detail_text(text))

            threading.Thread(target=_bg_fetch, daemon=True).start()

        for move in move_options:
            btn = ctk.CTkButton(
                self.action_frame,
                text=move.replace("-", " ").title(),
                font=FONT_BODY,
                height=36,
                corner_radius=6,
                command=lambda m=move: self.select_move(m)
            )
            btn.pack(fill="x", pady=4, padx=30)
            btn.bind("<Enter>", lambda e, m=move: on_move_hover(m))

    def select_move(self, move):
        self.current_pokemon["selected_moves"].append(move)
        self.update_team_view()
        self.refresh_pokemon_details(self.current_pokemon)
        self.next_move_round()

    def start_nature_phase(self):
        if self.draft_round >= len(self.team):
            self.draft_round = 0
            self.start_ev_phase()
            return

        self.current_pokemon = self.team[self.draft_round]
        self.refresh_pokemon_details(self.current_pokemon)

        chosen_natures = random.sample(list(NATURES.keys()), 3)

        self.clear_action_frame()

        title = ctk.CTkLabel(self.action_frame, text=f"Natura per {self.current_pokemon['name'].capitalize()} ({self.draft_round + 1}/6)", font=FONT_TITLE)
        title.pack(pady=(12, 6))

        for nat in chosen_natures:
            effect = NATURES[nat]
            eff_str = f"({effect[0]}, {effect[1]})" if effect[1] else f"({effect[0]})"
            btn = ctk.CTkButton(self.action_frame, text=f"{nat} {eff_str}", font=FONT_BODY, height=36, corner_radius=6, command=lambda n=nat: self.select_nature(n))
            btn.pack(fill="x", pady=4, padx=30)

    def select_nature(self, nature_name):
        self.current_pokemon["selected_nature"] = nature_name
        self.update_team_view()
        self.refresh_pokemon_details(self.current_pokemon)
        self.draft_round += 1
        self.start_nature_phase()

    def start_ev_phase(self):
        if self.draft_round >= len(self.team):
            self.draft_round = 0
            self.start_item_phase()
            return

        self.current_pokemon = self.team[self.draft_round]
        self.refresh_pokemon_details(self.current_pokemon)

        ev_options = [self.generate_random_evs() for _ in range(3)]

        self.clear_action_frame()

        title = ctk.CTkLabel(self.action_frame, text=f"Spread EV per {self.current_pokemon['name'].capitalize()} ({self.draft_round + 1}/6)", font=FONT_TITLE)
        title.pack(pady=(12, 6))

        for i, evs in enumerate(ev_options, 1):
            ev_str = " / ".join([f"{v} {k.upper()}" for k, v in evs.items() if v > 0])
            total_evs = sum(evs.values())

            btn = ctk.CTkButton(self.action_frame, text=f"Opz. {i} ({total_evs} EV): {ev_str}", font=FONT_SM, height=36, corner_radius=6, command=lambda e=evs: self.select_ev(e))
            btn.pack(fill="x", pady=4, padx=15)

    def generate_random_evs(self):
        stats = ["hp", "atk", "def", "spa", "spd", "spe"]
        evs = {s: 0 for s in stats}
        style = random.choice(["252_252_6", "balanced_510"])

        if style == "252_252_6":
            main_stats = random.sample(stats, 2)
            evs[main_stats[0]] = 252
            evs[main_stats[1]] = 252
            rem_stats = [s for s in stats if s not in main_stats]
            evs[random.choice(rem_stats)] = 6
        else:
            chosen = random.sample(stats, 4)
            evs[chosen[0]] = 252
            evs[chosen[1]] = 128
            evs[chosen[2]] = 124
            evs[chosen[3]] = 6

        return evs

    def select_ev(self, evs):
        self.current_pokemon["selected_evs"] = evs
        self.update_team_view()
        self.refresh_pokemon_details(self.current_pokemon)
        self.draft_round += 1
        self.start_ev_phase()

    def start_item_phase(self):
        if self.draft_round >= len(self.team):
            self.finish_draft()
            return

        self.current_pokemon = self.team[self.draft_round]
        self.refresh_pokemon_details(self.current_pokemon)

        item_options = random.sample(COMMON_ITEMS, 3)

        self.clear_action_frame()

        title = ctk.CTkLabel(self.action_frame, text=f"Oggetto per {self.current_pokemon['name'].capitalize()} ({self.draft_round + 1}/6)", font=FONT_TITLE)
        title.pack(pady=(12, 6))

        def on_item_hover(item_name):
            def _bg_fetch():
                desc = self.fetch_item_description(item_name)
                title_formatted = item_name.replace('-', ' ').title()
                text = f"=== ANTEPRIMA OGGETTO ===\n• {title_formatted}\n  -> Effetto: {desc}"
                self.after(0, lambda: self.set_detail_text(text))

            threading.Thread(target=_bg_fetch, daemon=True).start()

        for item in item_options:
            btn = ctk.CTkButton(self.action_frame, text=item.replace("-", " ").title(), font=FONT_BODY, height=36, corner_radius=6, command=lambda it=item: self.select_item(it))
            btn.pack(fill="x", pady=4, padx=30)
            btn.bind("<Enter>", lambda e, it=item: on_item_hover(it))

    def select_item(self, item):
        self.current_pokemon["selected_item"] = item
        self.update_team_view()
        self.refresh_pokemon_details(self.current_pokemon)
        self.draft_round += 1
        self.start_item_phase()

    def finish_draft(self):
        self.clear_action_frame()

        title = ctk.CTkLabel(self.action_frame, text="[ Draft Completato ]", font=FONT_TITLE, text_color="#98C379")
        title.pack(pady=8)

        showdown_text = self.export_to_showdown()

        textbox = ctk.CTkTextbox(self.action_frame, font=FONT_BODY)
        textbox.pack(fill="both", expand=True, pady=6, padx=12)
        textbox.insert("0.0", showdown_text)

        btn_save = ctk.CTkButton(
            self.action_frame,
            text="💾 Salva Team in TXT",
            font=FONT_SUBTITLE,
            fg_color="#61AFEF",
            hover_color="#4B88BC",
            text_color="#1E222A",
            height=38,
            command=lambda: self.save_team_dialog(showdown_text),
        )
        btn_save.pack(fill="x", padx=12, pady=(4, 8))

    def save_team_dialog(self, text_content):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            title="Salva il tuo Showdown Team",
            initialfile="my_draft_team.txt",
        )

        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text_content)
            messagebox.showinfo("Salvato", "Team salvato con successo!")
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile salvare il file: {e}")

    def export_to_showdown(self):
        output = []
        stat_map = {"hp": "HP", "atk": "Atk", "def": "Def", "spa": "SpA", "spd": "SpD", "spe": "Spe"}

        for p in self.team:
            lines = []
            gender_part = f" ({p['gender']})" if p.get('gender') and p['gender'] in ['M', 'F'] else ""
            item_part = f" @ {p['selected_item'].replace('-', ' ').title()}" if p["selected_item"] else ""
            lines.append(f"{p['name'].capitalize()}{gender_part}{item_part}")
            lines.append(f"Ability: {p['selected_ability'].replace('-', ' ').title()}")
            lines.append("Level: 50")

            if p["selected_nature"]:
                lines.append(f"{p['selected_nature']} Nature")

            ev_list = [f"{v} {stat_map[k]}" for k, v in p["selected_evs"].items() if v > 0]
            if ev_list:
                lines.append(f"EVs: {' / '.join(ev_list)}")

            for m in p["selected_moves"]:
                lines.append(f"- {m.replace('-', ' ').title()}")

            output.append("\n".join(lines))

        return "\n\n".join(output)


# ==============================================================================
# MAIN LAUNCHER
# ==============================================================================
class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Pokémon Utility Suite")
        self.geometry("450x280")
        self.resizable(False, False)

        self.active_draft_win = None

        self.main_container = ctk.CTkFrame(self, corner_radius=12)
        self.main_container.pack(fill="both", expand=True, padx=15, pady=15)

        lbl_header = ctk.CTkLabel(
            self.main_container,
            text="⚡ Pokémon Tool Suite ⚡",
            font=(FONT_FAMILY, 18, "bold"),
            text_color="#61AFEF"
        )
        lbl_header.pack(pady=(20, 5))

        btn_draft = ctk.CTkButton(
            self.main_container,
            text="Configura Draft",
            font=FONT_SUBTITLE,
            height=50,
            corner_radius=8,
            fg_color="#98C379",
            hover_color="#7CA35F",
            text_color="#1E222A",
            command=self.open_config
        )
        btn_draft.pack(fill="x", padx=25, pady=20)

    def open_config(self):
        DraftConfigWindow(self, self.start_draft_tool)

    def start_draft_tool(self, rules):
        if self.active_draft_win is None or not self.active_draft_win.winfo_exists():
            self.active_draft_win = PokemonDraftApp(self, rules)
        else:
            self.active_draft_win.focus()


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
